"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Osparc Control."""


if __name__ == "__main__":
    main(prog_name="osparc-control")  # pragma: no cover
