import click
import pathlib

from pbreflect.protorecover.recover_service import RecoverService


@click.group()
def cli() -> None:
    pass


@click.command("get-protos")
@click.option("-h", "--host", type=str, required=True, help="Destination host")
@click.option("-o", "--output", type=str, default="protos", help="Output directory")
def get_protos(host: str, output: str) -> None:
    output_dir = pathlib.Path(output)
    with RecoverService(host, output_dir) as service:
        service.recover_protos()


cli.add_command(get_protos)

if __name__ == "__main__":
    cli()
