"""
Smart logging system for nmr-parser with verbosity levels and colors.

Supports PROD, INFO, DEBUG levels with appropriate coloring and
progress updates that overwrite instead of creating thousands of lines.
"""

from enum import IntEnum
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.text import Text
from contextlib import contextmanager


class LogLevel(IntEnum):
    """Logging verbosity levels."""
    PROD = 0   # Production: minimal output, only results
    INFO = 1   # Default: useful progress information
    DEBUG = 2  # Verbose: everything including detailed progress


class NMRLogger:
    """
    Smart logger with verbosity levels and progress tracking.

    Features:
    - Three verbosity levels (PROD, INFO, DEBUG)
    - Color-coded messages
    - Progress updates that overwrite (no spam)
    - Context managers for operations
    """

    def __init__(self, level: LogLevel = LogLevel.INFO, console: Optional[Console] = None):
        self.level = level
        self.console = console or Console()
        self._progress = None
        self._current_task = None

    def prod(self, message: str, style: str = "bold green"):
        """Production level - only essential results."""
        if self.level >= LogLevel.PROD:
            self.console.print(f"[{style}]{message}[/{style}]")

    def info(self, message: str, style: str = "blue"):
        """Info level - useful progress information."""
        if self.level >= LogLevel.INFO:
            self.console.print(f"[{style}]{message}[/{style}]")

    def debug(self, message: str, style: str = "dim cyan"):
        """Debug level - verbose details."""
        if self.level >= LogLevel.DEBUG:
            self.console.print(f"[{style}]{message}[/{style}]")

    def success(self, message: str, level: LogLevel = LogLevel.INFO):
        """Success message (green)."""
        if self.level >= level:
            self.console.print(f"[bold green]✓[/bold green] [green]{message}[/green]")

    def warning(self, message: str, level: LogLevel = LogLevel.INFO):
        """Warning message (yellow)."""
        if self.level >= level:
            self.console.print(f"[bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")

    def error(self, message: str):
        """Error message (red) - always shown."""
        self.console.print(f"[bold red]✗[/bold red] [red]{message}[/red]")

    def step(self, message: str, level: LogLevel = LogLevel.INFO):
        """Major step indicator."""
        if self.level >= level:
            self.console.print(f"[bold blue]▶[/bold blue] [blue]{message}[/blue]")

    def detail(self, message: str, indent: int = 2):
        """Detailed info (debug level)."""
        if self.level >= LogLevel.DEBUG:
            prefix = " " * indent
            self.console.print(f"[dim]{prefix}• {message}[/dim]")

    @contextmanager
    def progress(self, description: str, total: Optional[int] = None, level: LogLevel = LogLevel.INFO):
        """
        Context manager for progress tracking with overwriting updates.

        Usage:
            with logger.progress("Reading spectra", total=144) as update:
                for i in range(144):
                    # do work
                    update(i + 1)
        """
        if self.level < level:
            # If below log level, yield a no-op function
            yield lambda x: None
            return

        if total is None:
            # Spinner for indeterminate progress
            with self.console.status(f"[blue]{description}...[/blue]", spinner="dots"):
                yield lambda x: None
        else:
            # Progress bar for determinate progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
                transient=True  # Remove after completion
            ) as progress:
                task = progress.add_task(description, total=total)

                def update(current: int):
                    progress.update(task, completed=current)

                yield update

    @contextmanager
    def operation(self, description: str, level: LogLevel = LogLevel.INFO):
        """
        Context manager for an operation (shows start and completion).

        Usage:
            with logger.operation("Reading acquisition parameters"):
                # do work
                pass
        """
        if self.level >= level:
            self.step(description, level)

        yield

        if self.level >= level and self.level >= LogLevel.DEBUG:
            self.success(f"{description} - Done", LogLevel.DEBUG)

    def summary(self, title: str, items: dict, level: LogLevel = LogLevel.PROD):
        """
        Print a summary box.

        Args:
            title: Summary title
            items: Dict of label: value pairs
            level: Minimum log level
        """
        if self.level < level:
            return

        self.console.print()
        self.console.print(f"[bold cyan]{'─' * 50}[/bold cyan]")
        self.console.print(f"[bold cyan]{title}[/bold cyan]")
        self.console.print(f"[bold cyan]{'─' * 50}[/bold cyan]")

        for label, value in items.items():
            self.console.print(f"  [cyan]{label}:[/cyan] [white]{value}[/white]")

        self.console.print(f"[bold cyan]{'─' * 50}[/bold cyan]")
        self.console.print()


def get_logger(verbosity: str = "info") -> NMRLogger:
    """
    Get a logger with specified verbosity level.

    Args:
        verbosity: "prod", "info", or "debug"

    Returns:
        NMRLogger instance
    """
    level_map = {
        "prod": LogLevel.PROD,
        "info": LogLevel.INFO,
        "debug": LogLevel.DEBUG,
    }

    level = level_map.get(verbosity.lower(), LogLevel.INFO)
    return NMRLogger(level=level)
