import argparse
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.bootstrap import DEFAULT_MODEL_ID, DEFAULT_PROVIDER, build_agent
from forge.model.codex_app_server import (
    CodexAppServerClient,
    CodexAppServerError,
)


BANNER_WORDMARK = (
    r" _   _    _    ____  _   _ _____ ____  ____ ",
    r"| | | |  / \  |  _ \| \ | | ____/ ___|/ ___|",
    r"| |_| | / _ \ | |_) |  \| |  _| \___ \\___ \ ",
    r"|  _  |/ ___ \|  _ <| |\  | |___ ___) |___) |",
    r"|_| |_/_/   \_\_| \_\_| \_|_____|____/|____/ ",
    "",
    r"    _    ____ _____ _   _ _____",
    r"   / \  / ___| ____| \ | |_   _|",
    r"  / _ \| |  _|  _| |  \| | | |  ",
    r" / ___ \ |_| | |___| |\  | | |  ",
    r"/_/   \_\____|_____|_| \_| |_|  ",
)


@dataclass
class CliConfig:
    command: str | None = None
    login_action: str | None = None
    device_code: bool = False
    model: str | None = None
    provider: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    project: str = "."
    once: str | None = None
    no_color: bool = False


class HarnessAgentCli:
    def __init__(
        self,
        agent,
        project_root: str | Path,
        console: Console | None = None,
    ):
        self.agent = agent
        self.project_root = Path(project_root).resolve()
        self.console = console or Console()
        self.running = True

    def banner(self) -> None:
        wordmark = "\n".join(
            f"[bold orange3]{line}[/bold orange3]" if line else ""
            for line in BANNER_WORDMARK
        )
        banner_text = "\n".join(
            [
                "[bold white on grey23]  * Welcome to HarnessAgent  [/bold white on grey23]",
                "",
                wordmark,
                "",
                "[dim]Press Enter to continue, or type your request below.[/dim]",
                "",
                f"[dim]Provider:[/dim] [green]{getattr(self.agent.model, 'provider', 'unknown')}[/green]",
                f"[dim]Model:[/dim] [green]{self.agent.model.model}[/green]",
                f"[dim]Project:[/dim] [green]{self.project_root}[/green]",
                f"[dim]Tools:[/dim] [green]{len(self.agent.tools.tools)} registered[/green]",
                "",
                "[dim]Type /help for commands, /exit to quit.[/dim]",
            ]
        )

        self.console.print(
            Panel(
                banner_text,
                border_style="cyan",
                box=box.ASCII,
                padding=(1, 2),
            )
        )

    def run_once(self, prompt: str) -> str:
        run_stream = getattr(self.agent, "run_stream", None)
        if callable(run_stream):
            streamed = False

            def display_delta(delta: str) -> None:
                nonlocal streamed
                if not delta:
                    return
                self.console.print(
                    delta,
                    end="",
                    markup=False,
                    highlight=False,
                )
                streamed = True

            self.console.print("[bold green]agent[/bold green] > ", end="")
            try:
                response = run_stream(prompt, display_delta)
            except Exception:
                self.console.print()
                raise

            if streamed:
                self.console.print()
            else:
                self.console.print(
                    response or "",
                    markup=False,
                    highlight=False,
                )
            return response

        response = self.agent.run(prompt)
        self.console.print(f"[bold green]agent[/bold green] > {response or ''}")
        return response

    def run(self) -> None:
        self.banner()
        try:
            while self.running:
                try:
                    user_input = self.console.input(
                        "[bold cyan]you[/bold cyan] > "
                    )
                    self.handle_input(user_input.strip())
                except (EOFError, KeyboardInterrupt):
                    self.console.print()
                    break
                except CodexAppServerError as exc:
                    self.console.print(f"[red]{exc}[/red]")
        finally:
            if hasattr(self.agent, "close"):
                self.agent.close()

    def handle_input(self, user_input: str) -> None:
        if not user_input:
            return

        if user_input.startswith("/"):
            self.handle_command(user_input)
            return

        self.run_once(user_input)

    def handle_command(self, command_line: str) -> None:
        command, _, argument = command_line.partition(" ")
        command = command.lower()
        argument = argument.strip()

        handlers = {
            "/help": self.show_help,
            "/model": self.change_model,
            "/models": self.show_models,
            "/tools": self.show_tools,
            "/status": self.show_status,
            "/security": self.show_security,
            "/verify": self.verify_project,
            "/clear": self.clear_history,
            "/exit": self.exit,
            "/quit": self.exit,
        }

        handler = handlers.get(command)

        if handler is None:
            self.console.print(f"[red]Unknown command:[/red] {command}")
            self.console.print("Type /help for available commands.")
            return

        handler(argument)

    def show_help(self, argument: str = "") -> None:
        table = Table(title="HarnessAgent CLI Commands")
        table.add_column("Command", style="cyan")
        table.add_column("What it does")

        for command, description in (
            ("/help", "Show CLI commands"),
            ("/model", "Display models and switch the active provider"),
            ("/models", "Fetch available Codex account models"),
            ("/tools", "List registered model tools"),
            ("/status", "Show model, tool count, and context summary status"),
            ("/security", "Show active security policy"),
            ("/verify", "Run project verification"),
            ("/clear", "Clear conversation history, keeping system instructions"),
            ("/exit", "Quit the CLI"),
        ):
            table.add_row(command, description)

        self.console.print(table)

    def change_model(self, argument: str = "") -> None:
        provider = getattr(self.agent.model, "provider", "unknown")
        self.console.print(
            f"[dim]Current:[/dim] [green]{provider}"
            f" / {self.agent.model.model}[/green]"
        )

        config = CliConfig(project=str(self.project_root))
        try:
            select_model(config, self.console)
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[yellow]Model switch cancelled.[/yellow]")
            return

        try:
            new_agent = build_agent(
                model_id=config.model or DEFAULT_MODEL_ID,
                project_root=self.project_root,
                provider=config.provider or DEFAULT_PROVIDER,
                base_url=config.base_url,
                api_key_env=config.api_key_env,
            )
        except (ValueError, CodexAppServerError) as exc:
            self.console.print(f"[red]{exc}[/red]")
            return

        old_agent = self.agent
        self.agent = new_agent
        if hasattr(old_agent, "close"):
            old_agent.close()

        self.console.print(
            "[green]Model switched.[/green] "
            f"Provider: {getattr(new_agent.model, 'provider', 'unknown')}, "
            f"Model: {new_agent.model.model}"
        )
        self.console.print("[dim]A new conversation has started.[/dim]")

    def show_models(self, argument: str = "") -> None:
        provider = getattr(self.agent.model, "provider", "unknown")

        try:
            if provider == "codex" and hasattr(
                self.agent,
                "available_models",
            ):
                models = self.agent.available_models()
            else:
                with CodexAppServerClient() as client:
                    models = client.list_models()
        except CodexAppServerError as exc:
            self.console.print(f"[red]{exc}[/red]")
            return

        if not models:
            self.console.print("[yellow]No Codex models are available.[/yellow]")
            return

        table = Table(title="Available Codex Models")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Model")
        table.add_column("Reasoning")
        table.add_column("Input")
        table.add_column("Default", justify="center")

        for index, model in enumerate(models, start=1):
            efforts = ", ".join(
                effort.get("reasoningEffort", "")
                for effort in model.get("supportedReasoningEfforts", [])
            ) or "-"
            modalities = ", ".join(
                model.get("inputModalities") or ["text", "image"]
            )
            table.add_row(
                str(index),
                model.get("displayName") or model.get("model") or model["id"],
                efforts,
                modalities,
                "yes" if model.get("isDefault") else "",
            )

        self.console.print(table)
        selection = self.console.input(
            "Select a model number, or press Enter to keep the current model: "
        ).strip()
        if not selection:
            return
        if not selection.isdigit() or not 1 <= int(selection) <= len(models):
            self.console.print("[yellow]Invalid model selection.[/yellow]")
            return

        selected = models[int(selection) - 1]
        model_id = selected.get("model") or selected["id"]

        if provider == "codex" and hasattr(self.agent, "set_model"):
            self.agent.set_model(model_id)
        else:
            try:
                new_agent = build_agent(
                    model_id=model_id,
                    project_root=self.project_root,
                    provider="codex",
                )
            except (ValueError, CodexAppServerError) as exc:
                self.console.print(f"[red]{exc}[/red]")
                return

            old_agent = self.agent
            self.agent = new_agent
            if hasattr(old_agent, "close"):
                old_agent.close()

        self.console.print(
            f"[green]Model switched to {model_id}.[/green]"
        )
        self.console.print("[dim]A new conversation has started.[/dim]")

    def show_tools(self, argument: str = "") -> None:
        table = Table(title="Registered Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description")

        for tool in self.agent.tools.tools.values():
            table.add_row(tool.name, tool.description)

        self.console.print(table)

    def show_status(self, argument: str = "") -> None:
        summary_state = (
            "active"
            if self.agent.conversation_summary
            else "empty"
        )

        self.console.print(
            Panel(
                "\n".join(
                    [
                        f"Provider: {getattr(self.agent.model, 'provider', 'unknown')}",
                        f"Model: {self.agent.model.model}",
                        f"Project: {self.project_root}",
                        f"Tools: {len(self.agent.tools.tools)}",
                        f"Messages: {len(self.agent.conversation.messages)}",
                        f"Summary: {summary_state}",
                    ]
                ),
                title="Status",
                border_style="cyan",
                box=box.ASCII,
            )
        )

    def show_security(self, argument: str = "") -> None:
        result = self.agent.tools.execute(
            "show_security_policy",
            {},
        )
        self.console.print_json(data=result)

    def verify_project(self, argument: str = "") -> None:
        result = self.agent.tools.execute(
            "verify_project",
            {},
        )
        self.console.print_json(data=result)

    def clear_history(self, argument: str = "") -> None:
        if hasattr(self.agent, "reset_conversation"):
            self.agent.reset_conversation()
            self.console.print("[green]Conversation cleared.[/green]")
            return

        system_messages = [
            message
            for message in self.agent.conversation.messages
            if message.get("role") == "system"
        ]
        self.agent.conversation.messages = system_messages
        self.agent.conversation_summary = None
        self.agent.summarized_turns = 0
        self.console.print("[green]Conversation cleared.[/green]")

    def exit(self, argument: str = "") -> None:
        self.running = False
        if hasattr(self.agent, "close"):
            self.agent.close()
        self.console.print("[cyan]Goodbye.[/cyan]")


def parse_args(argv: list[str] | None = None) -> CliConfig:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="HarnessAgent local coding-agent CLI",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("login", "logout"),
        help="Authenticate the Codex account provider",
    )
    parser.add_argument(
        "login_action",
        nargs="?",
        choices=("status",),
        help="Show the current Codex login status",
    )
    parser.add_argument(
        "--model",
        help="Model id to use",
    )
    parser.add_argument(
        "--provider",
        choices=("lmstudio", "codex", "openai", "gemini", "openai-compatible"),
        help="Model provider backend",
    )
    parser.add_argument(
        "--device-code",
        action="store_true",
        help="Use device-code login instead of a browser callback",
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api-key-env",
        help="Environment variable that contains the provider API key",
    )
    parser.add_argument(
        "--project",
        default=".",
        help="Project folder HarnessAgent should operate on",
    )
    parser.add_argument(
        "--once",
        help="Run one prompt and exit",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable terminal colors",
    )

    args = parser.parse_args(argv)

    return CliConfig(
        command=args.command,
        login_action=args.login_action,
        device_code=args.device_code,
        model=args.model,
        provider=args.provider,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        project=args.project,
        once=args.once,
        no_color=args.no_color,
    )


def _required_input(console: Console, prompt: str) -> str:
    while True:
        value = console.input(prompt).strip()
        if value:
            return value
        console.print("[yellow]Please enter a value.[/yellow]")


def select_model(config: CliConfig, console: Console) -> CliConfig:
    console.print(
        Panel(
            "\n".join(
                [
                    "[bold cyan]1[/bold cyan]  Codex via ChatGPT account",
                    "[bold cyan]2[/bold cyan]  Gemma 4 e4b via LM Studio",
                    "[bold cyan]3[/bold cyan]  Another LM Studio model",
                    "[bold cyan]4[/bold cyan]  OpenAI API model",
                    "[bold cyan]5[/bold cyan]  Gemini API model",
                    "[bold cyan]6[/bold cyan]  OpenAI-compatible endpoint",
                ]
            ),
            title="Select Model",
            border_style="cyan",
            box=box.ASCII,
            padding=(1, 2),
        )
    )

    while True:
        choice = console.input("[bold cyan]Select[/bold cyan] [1]: ").strip() or "1"

        if choice == "1":
            config.provider = "codex"
            console.print(
                "[bold cyan]1[/bold cyan]  Account default\n"
                "[bold cyan]2[/bold cyan]  Enter a custom Codex model ID"
            )
            while True:
                model_choice = console.input(
                    "[bold cyan]Select Codex model[/bold cyan] [1]: "
                ).strip() or "1"
                if model_choice == "1":
                    config.model = DEFAULT_MODEL_ID
                    return config
                if model_choice == "2":
                    config.model = _required_input(
                        console,
                        "Codex model ID: ",
                    )
                    return config
                console.print("[yellow]Choose 1 or 2.[/yellow]")
        if choice == "2":
            config.provider = "lmstudio"
            config.model = DEFAULT_MODEL_ID
            return config
        if choice == "3":
            config.provider = "lmstudio"
            config.model = _required_input(console, "LM Studio model ID: ")
            return config
        if choice == "4":
            config.provider = "openai"
            config.model = _required_input(console, "OpenAI model ID: ")
            return config
        if choice == "5":
            config.provider = "gemini"
            config.model = _required_input(console, "Gemini model ID: ")
            return config
        if choice == "6":
            config.provider = "openai-compatible"
            config.base_url = _required_input(console, "API base URL: ")
            config.model = _required_input(console, "Model ID: ")
            return config

        console.print("[yellow]Choose a number from 1 to 6.[/yellow]")


def run_auth_command(config: CliConfig, console: Console) -> int:
    try:
        with CodexAppServerClient() as client:
            if config.command == "logout":
                client.logout()
                console.print("[green]Signed out of the Codex account.[/green]")
                return 0

            if config.login_action == "status":
                account = client.account()
                if not account:
                    console.print("[yellow]Not signed in.[/yellow]")
                    return 1

                console.print(f"[green]Signed in with {account['type']}.[/green]")
                if account.get("email"):
                    console.print(f"Account: {account['email']}")
                if account.get("planType"):
                    console.print(f"Plan: {account['planType']}")
                return 0

            login = client.start_login(device_code=config.device_code)
            login_id = login["loginId"]
            if login["type"] == "chatgptDeviceCode":
                console.print(f"Open: [link]{login['verificationUrl']}[/link]")
                console.print(f"Code: [bold cyan]{login['userCode']}[/bold cyan]")
                webbrowser.open(login["verificationUrl"])
            else:
                console.print("Opening ChatGPT sign-in in your browser...")
                console.print(f"[link]{login['authUrl']}[/link]")
                webbrowser.open(login["authUrl"])

            client.wait_for_login(login_id)
            account = client.account() or {}
            console.print("[green]ChatGPT login completed.[/green]")
            if account.get("email"):
                console.print(f"Account: {account['email']}")
            if account.get("planType"):
                console.print(f"Plan: {account['planType']}")
            return 0
    except CodexAppServerError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    console = Console(no_color=config.no_color)

    if config.command:
        return run_auth_command(config, console)

    if config.provider is None and config.model is None and config.once is None:
        try:
            select_model(config, console)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Model selection cancelled.[/yellow]")
            return 130

    config.provider = config.provider or DEFAULT_PROVIDER
    config.model = config.model or DEFAULT_MODEL_ID

    project_root = Path(config.project).resolve()

    if not project_root.exists():
        console.print(f"[red]Project path not found:[/red] {project_root}")
        return 1

    if not project_root.is_dir():
        console.print(f"[red]Project path is not a directory:[/red] {project_root}")
        return 1

    try:
        agent = build_agent(
            model_id=config.model,
            project_root=project_root,
            provider=config.provider,
            base_url=config.base_url,
            api_key_env=config.api_key_env,
        )
    except (ValueError, CodexAppServerError) as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    cli = HarnessAgentCli(
        agent=agent,
        project_root=project_root,
        console=console,
    )

    if config.once:
        try:
            cli.run_once(config.once)
            return 0
        except CodexAppServerError as exc:
            console.print(f"[red]{exc}[/red]")
            return 1
        finally:
            if hasattr(agent, "close"):
                agent.close()

    cli.run()
    return 0
