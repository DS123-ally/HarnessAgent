import argparse
from dataclasses import dataclass
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.bootstrap import DEFAULT_MODEL_ID, build_agent


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
    model: str = DEFAULT_MODEL_ID
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
        response = self.agent.run(prompt)
        self.console.print(f"[bold green]agent[/bold green] > {response or ''}")
        return response

    def run(self) -> None:
        self.banner()

        while self.running:
            try:
                user_input = self.console.input("[bold cyan]you[/bold cyan] > ")
            except (EOFError, KeyboardInterrupt):
                self.console.print()
                break

            self.handle_input(user_input.strip())

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
            ("/tools", "List registered model tools"),
            ("/status", "Show model, tool count, and context summary status"),
            ("/security", "Show active security policy"),
            ("/verify", "Run project verification"),
            ("/clear", "Clear conversation history, keeping system instructions"),
            ("/exit", "Quit the CLI"),
        ):
            table.add_row(command, description)

        self.console.print(table)

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
        self.console.print("[cyan]Goodbye.[/cyan]")


def parse_args(argv: list[str] | None = None) -> CliConfig:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="HarnessAgent local coding-agent CLI",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_ID,
        help="LM Studio model id",
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
        model=args.model,
        project=args.project,
        once=args.once,
        no_color=args.no_color,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    console = Console(no_color=config.no_color)
    project_root = Path(config.project).resolve()

    if not project_root.exists():
        console.print(f"[red]Project path not found:[/red] {project_root}")
        return 1

    if not project_root.is_dir():
        console.print(f"[red]Project path is not a directory:[/red] {project_root}")
        return 1

    agent = build_agent(
        model_id=config.model,
        project_root=project_root,
    )
    cli = HarnessAgentCli(
        agent=agent,
        project_root=project_root,
        console=console,
    )

    if config.once:
        cli.run_once(config.once)
        return 0

    cli.run()
    return 0
