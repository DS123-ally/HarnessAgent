import json
import shutil
import subprocess
import threading
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any


class CodexAppServerError(RuntimeError):
    pass


class CodexAppServerClient:
    def __init__(
        self,
        executable: str | None = None,
        process_factory: Callable[..., Any] = subprocess.Popen,
    ):
        self.executable = executable or shutil.which("codex")
        if not self.executable:
            raise CodexAppServerError(
                "Codex CLI was not found. Install Codex before using "
                "the codex provider."
            )

        try:
            self.process = process_factory(
                [self.executable, "app-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError as exc:
            raise CodexAppServerError(
                f"Could not start Codex App Server: {exc}"
            ) from exc

        self._next_id = 1
        self._notifications = deque()
        self._stderr_lines = deque(maxlen=20)
        self.thread_id: str | None = None
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            daemon=True,
        )
        self._stderr_thread.start()
        self._initialize()

    def _drain_stderr(self) -> None:
        if self.process.stderr is None:
            return
        for line in self.process.stderr:
            self._stderr_lines.append(line.rstrip())

    def _initialize(self) -> None:
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "harness_agent",
                    "title": "HarnessAgent",
                    "version": "0.1.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        self.notify("initialized", {})

    def _send(self, message: dict) -> None:
        if self.process.stdin is None:
            raise CodexAppServerError("Codex App Server stdin is unavailable.")

        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise CodexAppServerError(
                "Codex App Server closed unexpectedly."
            ) from exc

    def _read(self) -> dict:
        if self.process.stdout is None:
            raise CodexAppServerError("Codex App Server stdout is unavailable.")

        while True:
            line = self.process.stdout.readline()
            if line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

            error = "\n".join(self._stderr_lines).strip()
            detail = f": {error}" if error else ""
            raise CodexAppServerError(
                f"Codex App Server stopped unexpectedly{detail}"
            )

    def notify(self, method: str, params: dict) -> None:
        self._send({"method": method, "params": params})

    def respond(self, request_id: int | str, result: dict) -> None:
        self._send({"id": request_id, "result": result})

    def request(
        self,
        method: str,
        params: dict | None = None,
        server_request_handler: Callable[[dict], dict] | None = None,
    ) -> dict:
        request_id = self._next_id
        self._next_id += 1
        message = {"method": method, "id": request_id}
        if params is not None:
            message["params"] = params
        self._send(message)

        while True:
            incoming = self._read()
            if incoming.get("id") == request_id and "method" not in incoming:
                if "error" in incoming:
                    error = incoming["error"]
                    raise CodexAppServerError(
                        error.get("message", str(error))
                        if isinstance(error, dict)
                        else str(error)
                    )
                return incoming.get("result", {})

            if "id" in incoming and "method" in incoming:
                if server_request_handler is None:
                    self.respond(
                        incoming["id"],
                        {"success": False, "contentItems": []},
                    )
                else:
                    self.respond(
                        incoming["id"],
                        server_request_handler(incoming),
                    )
                continue

            self._notifications.append(incoming)

    def _next_message(self) -> dict:
        if self._notifications:
            return self._notifications.popleft()
        return self._read()

    def account(self) -> dict | None:
        return self.request("account/read", {"refreshToken": True}).get(
            "account"
        )

    def start_login(self, device_code: bool = False) -> dict:
        login_type = "chatgptDeviceCode" if device_code else "chatgpt"
        return self.request(
            "account/login/start",
            {"type": login_type},
        )

    def wait_for_login(self, login_id: str) -> dict:
        while True:
            message = self._next_message()
            if message.get("method") != "account/login/completed":
                continue

            params = message.get("params", {})
            if params.get("loginId") != login_id:
                continue
            if not params.get("success"):
                raise CodexAppServerError(
                    params.get("error") or "ChatGPT login failed."
                )
            return params

    def logout(self) -> None:
        self.request("account/logout")

    def start_thread(
        self,
        project_root: str | Path,
        dynamic_tools: list[dict],
        developer_instructions: str,
        model: str | None = None,
    ) -> str:
        params = {
            "cwd": str(Path(project_root).resolve()),
            "approvalPolicy": "never",
            "sandbox": "read-only",
            "developerInstructions": developer_instructions,
            "dynamicTools": dynamic_tools,
            "serviceName": "harness_agent",
        }
        if model:
            params["model"] = model

        result = self.request("thread/start", params)
        self.thread_id = result["thread"]["id"]
        return self.thread_id

    def run_turn(
        self,
        prompt: str,
        server_request_handler: Callable[[dict], dict],
    ) -> str:
        if not self.thread_id:
            raise CodexAppServerError("A Codex thread has not been started.")

        result = self.request(
            "turn/start",
            {
                "threadId": self.thread_id,
                "input": [{"type": "text", "text": prompt}],
            },
            server_request_handler=server_request_handler,
        )
        turn_id = result["turn"]["id"]
        messages: list[str] = []

        while True:
            message = self._next_message()

            if "id" in message and "method" in message:
                response = server_request_handler(message)
                self.respond(message["id"], response)
                continue

            method = message.get("method")
            params = message.get("params", {})

            if method == "item/completed":
                item = params.get("item", {})
                if item.get("type") == "agentMessage" and item.get("text"):
                    messages.append(item["text"])

            if method == "error":
                error = params.get("error", {})
                raise CodexAppServerError(
                    error.get("message", str(error))
                    if isinstance(error, dict)
                    else str(error)
                )

            if method == "turn/completed":
                turn = params.get("turn", {})
                if turn.get("id") != turn_id:
                    continue
                if turn.get("status") == "failed":
                    error = turn.get("error") or {}
                    raise CodexAppServerError(
                        error.get("message", "Codex turn failed.")
                        if isinstance(error, dict)
                        else str(error)
                    )
                return "\n\n".join(messages)

    def reset_thread(self) -> None:
        self.thread_id = None

    def close(self) -> None:
        if self.process.poll() is not None:
            return

        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
