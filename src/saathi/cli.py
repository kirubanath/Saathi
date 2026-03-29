"""Saathi CLI — terminal interface for running and demoing the learning loop."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = _ROOT / "data"
USERS_PATH = DATA_DIR / "users.json"
TAXONOMY_PATH = DATA_DIR / "taxonomy.json"


def load_users() -> list[dict]:
    return json.loads(USERS_PATH.read_text())


@click.group()
def cli():
    """Saathi — AI Learning Companion"""
    pass


@cli.command("list-users")
def list_users():
    """List all saved user profiles."""
    users = load_users()
    table = Table(title="Saved Users", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Maturity")
    table.add_column("Tenure (days)", justify="right")
    for u in users:
        table.add_row(
            u["name"],
            u["user_type"].replace("_", " ").title(),
            u["maturity"].replace("_", " ").title(),
            str(u["tenure_days"]),
        )
    console.print(table)
