"""CLI implementation for discord-guard."""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from guard.api.discord import DiscordAPIError, DiscordClient, InvalidTokenError
from guard.core.monitor import AccountMonitor
from guard.core.scanner import AccountScanner
from guard.models.risk import AccountRiskReport, Alert, RiskLevel
from guard.reports.json_report import JSONReportGenerator
from guard.reports.pdf_report import PDFReportGenerator

app = typer.Typer(
    help="Discord security scanner and protector.",
    add_completion=False,
)
console = Console()


def display_alert(alert: Alert) -> None:
    """Displays a real-time security alert."""
    console.print(
        "\n[bold blink red]⚠️  ALERT: Suspicious activity detected[/bold blink red]"
    )
    alert_panel = Panel(
        f"[bold]Type:[/bold] {alert.type}\n"
        f"[bold]Details:[/bold] {alert.description}\n"
        f"[bold]Time:[/bold] {alert.timestamp.strftime('%H:%M:%S')}\n"
        f"[bold]Action:[/bold] [yellow]{alert.recommendation}[/yellow]",
        title="[bold red]SECURITY ALERT[/bold red]",
        border_style="red",
        expand=False,
    )
    console.print(alert_panel)
    console.bell()


def display_welcome() -> None:
    """Displays the welcome banner."""
    console.print(
        Panel.fit(
            "[bold blue]discord-guard[/bold blue] v[white]1.0.0[/white]\n"
            "[italic]Discord Security Scanner[/italic]",
            border_style="blue",
        )
    )


def display_report(report: AccountRiskReport) -> None:
    """Displays the security report in a professional format.

    Args:
        report: The generated risk report.
    """
    # Overall Score Header
    level_color = "green"
    level_emoji = "✅"
    if report.overall_level == RiskLevel.CRITICAL:
        level_color = "red"
        level_emoji = "🔴"
    elif report.overall_level == RiskLevel.WARNING:
        level_color = "yellow"
        level_emoji = "🟡"

    console.print("\n[bold]Account Scanning Results:[/bold]")
    console.print(f"User: [bold cyan]{report.username}[/bold cyan] ({report.user_id})")

    score_panel = Panel(
        "[bold]SECURITY REPORT[/bold]\n"
        f"Overall Risk Score: [bold]{report.overall_score}/100[/bold]  "
        f"[{level_color}]{level_emoji} {report.overall_level.upper()}[/{level_color}]",
        border_style=level_color,
        expand=False,
    )
    console.print(score_panel)

    # Risk Details
    if report.risks:
        for risk in report.risks:
            color = "red" if risk.level == RiskLevel.CRITICAL else "yellow"
            emoji = "🔴" if risk.level == RiskLevel.CRITICAL else "🟡"
            console.print(
                f"\n{emoji} [bold {color}]{risk.level.upper()}[/bold {color}] — "
                f"{risk.description}"
            )
            console.print(f"   → [italic]{risk.recommendation}[/italic]")
    else:
        console.print(
            "\n✅ [bold green]SAFE[/bold green] — No immediate security risks detected."
        )

    # Sessions Summary
    session_count = len(report.active_sessions)
    if session_count > 0:
        console.print(f"\n[bold]Active Sessions:[/bold] {session_count} detected.")

    if report.sessions_note:
        console.print(f"\n[dim]ℹ {report.sessions_note}[/dim]")


async def revoke_flow(token: str, report: AccountRiskReport) -> None:
    """Handles the interactive revocation of suspicious apps.

    Args:
        token: The Discord user token.
        report: The current risk report.
    """
    fixable_apps = [
        app
        for app in report.authorized_apps
        if any(
            scope in {"bot", "rpc", "messages.read", "guilds.join"}
            for scope in app.scopes
        )
    ]

    if not fixable_apps:
        return

    console.print("\n[bold yellow]Suspicious Authorized Apps Found:[/bold yellow]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("App Name", style="cyan")
    table.add_column("Permissions", style="dim")
    table.add_column("ID", style="dim")

    for app_info in fixable_apps:
        table.add_row(app_info.name, ", ".join(app_info.scopes), app_info.id)

    console.print(table)

    confirm = typer.confirm(
        "\nWould you like to revoke access for these suspicious apps?"
    )
    if confirm:
        client = DiscordClient(token)
        for app_info in fixable_apps:
            if typer.confirm(
                f"Revoke access for [bold red]{app_info.name}[/bold red]?"
            ):
                try:
                    await client.revoke_app(app_info.id)
                    console.print(
                        f"✅ [green]Successfully revoked access for "
                        f"{app_info.name}.[/green]"
                    )
                except DiscordAPIError as e:
                    console.print(
                        f"❌ [red]Failed to revoke {app_info.name}: {e}[/red]"
                    )

        console.print("\n[bold green]Cleanup complete.[/bold green]")


@app.command()
def scan(
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="Your Discord user token.",
        prompt="Enter your Discord token",
        hide_input=True,
    ),
) -> None:
    """Scan account for risks."""
    display_welcome()

    async def _run():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Fetching account data...", total=None)
                scanner = AccountScanner(token)
                report_data = await scanner.run_scan()

            display_report(report_data)
            await revoke_flow(token, report_data)

        except InvalidTokenError:
            console.print(
                "\n❌ [bold red]Error:[/bold red] The provided token is invalid."
            )
        except Exception as e:
            console.print(
                f"\n❌ [bold red]An unexpected error occurred:[/bold red] {e}"
            )

    asyncio.run(_run())


@app.command()
def monitor(
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="Your Discord user token.",
        prompt="Enter your Discord token",
        hide_input=True,
    ),
    interval: int = typer.Option(30, help="Polling interval in seconds."),
) -> None:
    """Monitor account activity in real time."""
    display_welcome()
    console.print(
        f"\n[bold yellow]Monitoring account activity every {interval}s...[/bold yellow]"
    )
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    monitor = AccountMonitor(token, interval)

    try:
        asyncio.run(monitor.start(on_alert=display_alert))
    except KeyboardInterrupt:
        console.print("\n[bold blue]Monitoring stopped.[/bold blue]")
    except InvalidTokenError:
        console.print(
            "\n❌ [bold red]Error:[/bold red] The provided token is invalid."
        )
    except Exception as e:
        console.print(
            f"\n❌ [bold red]An unexpected error occurred:[/bold red] {e}"
        )


@app.command()
def report(
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="Your Discord user token.",
        prompt="Enter your Discord token",
        hide_input=True,
    ),
    format: str = typer.Option("pdf", help="Report format (pdf or json)."),
    output: str = typer.Option("report.pdf", help="Output file path."),
) -> None:
    """Generate report from a fresh account scan."""
    display_welcome()

    async def _run():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description="Scanning account for report...", total=None
                )
                scanner = AccountScanner(token)
                report_data = await scanner.run_scan()

            if format.lower() == "pdf":
                generator = PDFReportGenerator()
            elif format.lower() == "json":
                generator = JSONReportGenerator()
            else:
                console.print(
                    f"\n❌ [bold red]Error:[/bold red] Unsupported format "
                    f"'{format}'. Use 'pdf' or 'json'."
                )
                return

            output_path = generator.generate(report_data, output)
            console.print(
                f"\n✅ [bold green]Report successfully generated:[/bold green] "
                f"{output_path}"
            )

        except InvalidTokenError:
            console.print(
                "\n❌ [bold red]Error:[/bold red] The provided token is invalid."
            )
        except Exception as e:
            console.print(
                f"\n❌ [bold red]An unexpected error occurred:[/bold red] {e}"
            )

    asyncio.run(_run())


@app.callback()
def main() -> None:
    """
    discord-guard — Protect your Discord account from session hijacking.
    """
    pass


if __name__ == "__main__":
    app()
