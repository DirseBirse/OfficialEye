import click
import yaml
from yaml.loader import SafeLoader
# noinspection PyPackageRequirements
import cv2

from officialeye.context.singleton import oe_context
from officialeye.match.template import Template
from officialeye.meta import APPLICATION_GITHUB


@click.group()
@click.option("-d", "--debug", is_flag=True, show_default=True, default=False, help="Enable debug mode.")
@click.option("--dedir", type=click.Path(exists=True), help="Specify debug export directory")
@click.option("--edir", type=click.Path(exists=True), help="Specify export directory")
def cli(debug: bool, dedir: str, edir: str):
    oe_context().debug_mode = debug
    if oe_context().debug_mode:
        click.secho("Warning: Debug mode enabled. Disable for production use to avoid performance issues.",
                    bg="yellow", bold=True)
    if dedir is not None:
        oe_context().debug_export_directory = dedir
    if edir is not None:
        oe_context().export_directory = edir


def load_template(path: str) -> Template:
    # click.echo(f"Loading template '{click.format_filename(template_name)}'")

    with open(path) as f:
        data = yaml.load(f, Loader=SafeLoader)

    template = Template(data, path)
    click.secho(f"Loaded feature: {template}", fg="green", bold=True)
    return template


@click.command()
@click.argument("template_path", type=click.Path(exists=True))
def show(template_path: str):
    """Exports template as an image with features visualized."""
    template = load_template(template_path)
    template.show()
    oe_context().dispose()


@click.command()
@click.argument("template_path", type=click.Path(exists=True))
@click.argument("target_path", type=click.Path(exists=True))
def apply(template_path: str, target_path: str):
    """Analyzes image using template, and prints debug info."""
    template = load_template(template_path)
    target = cv2.imread(target_path, cv2.IMREAD_COLOR)
    template.apply(target, debug_mode=oe_context().debug_mode)
    oe_context().dispose()


@click.command()
def homepage():
    """Go to the officialeye's official GitHub homepage."""
    click.secho(f"Opening {APPLICATION_GITHUB}", bg="blue", fg="white")
    click.launch(APPLICATION_GITHUB)
    oe_context().dispose()


cli.add_command(show)
cli.add_command(apply)
cli.add_command(homepage)

if __name__ == "__main__":
    cli()
