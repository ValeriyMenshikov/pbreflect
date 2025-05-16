import pathlib

import click

from pbreflect.pbgen.runner import run
from pbreflect.protorecover.recover_service import RecoverService


@click.group()
def cli() -> None:
    pass


@click.command("get-protos")
@click.option("-h", "--host", type=str, required=True, help="Destination host")
@click.option("-o", "--output", type=str, default="protos", help="Output directory")
@click.option("--use-tls", is_flag=True, help="Use TLS/SSL for connection")
@click.option(
    "--root-cert",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    help="Path to root certificate file (CA certificate)",
)
@click.option(
    "--private-key",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    help="Path to private key file",
)
@click.option(
    "--cert-chain",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    help="Path to certificate chain file",
)
def get_protos(
    host: str,
    output: str,
    use_tls: bool,
    root_cert: pathlib.Path | None,
    private_key: pathlib.Path | None,
    cert_chain: pathlib.Path | None,
) -> None:
    """Recover proto files from a gRPC server using reflection.

    This command connects to a gRPC server, retrieves proto descriptors using the reflection API,
    and generates .proto files that can be used for client development.
    """
    output_dir = pathlib.Path(output)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate TLS parameters
    if root_cert or private_key or cert_chain:
        use_tls = True
        click.echo("TLS certificates provided, enabling TLS mode")

    if use_tls:
        click.echo("Using secure connection (TLS)")

    with RecoverService(
        host,
        output_dir,
        use_tls=use_tls,
        root_certificates_path=root_cert,
        private_key_path=private_key,
        certificate_chain_path=cert_chain,
    ) as service:
        try:
            saved_files = service.recover_protos()
            if saved_files:
                click.echo(f"Successfully recovered {len(saved_files)} proto files to {output_dir}")
                for proto_name, file_path in saved_files.items():
                    click.echo(f"  - {proto_name}: {file_path}")
            else:
                click.echo("No proto files were recovered")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()


@click.command("generate")
@click.option(
    "-t",
    "--gen_type",
    "gen_type",
    required=False,
    help="Type of generator, also you can pass name of your custom compiler",
    type=click.Choice(["default", "mypy", "betterproto"]),
    default="default",
)
@click.option(
    "-p", "--proto_dir", "proto_dir", required=True, help="Path to directory with proto files"
)
@click.option(
    "-o",
    "--output_dir",
    "output_dir",
    required=True,
    help="Path to directory where to put generated Python code",
)
@click.option(
    "-r", "--refresh", "refresh", required=False, is_flag=True, help="Clear output directory"
)
def gen(proto_dir: str, output_dir: str, gen_type: str = "default", refresh: bool = False):
    """
    Command to generate code

    :param proto_dir: Directory with proto files
    :param output_dir: Directory where to generate code
    :param gen_type: Type of generator
    :param refresh: Clear output directory
    """
    run(proto_dir, output_dir, gen_type, refresh)


cli.add_command(get_protos)
cli.add_command(gen)

if __name__ == "__main__":
    cli()
