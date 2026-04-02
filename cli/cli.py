import click

from backend.__main__ import main as run_api_main
from eit_dash.main import app


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Default prompt. It shows the help command."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="run", help="Start the dashboard.")
def run():
    """Start the dashboard."""
    app.run_server(debug=True)


@cli.command(name="run-api", help="Start the FastAPI preview backend.")
def run_api():
    """Start the FastAPI preview backend."""
    run_api_main()


if __name__ == "__main__":
    cli()
