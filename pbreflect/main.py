import pathlib
import tempfile
from collections.abc import Callable
from typing import Any

import click

from pbreflect.pbgen.generators.factory import GeneratorType
from pbreflect.pbgen.runner import GenerationOptions, GenerationPipeline
from pbreflect.protorecover.recover_service import RecoverService

_TLS_OPTIONS = [
    click.option("--use-tls", is_flag=True, help="Use TLS/SSL for connection"),
    click.option(
        "--root-cert",
        type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
        help="Path to root certificate file (CA certificate)",
    ),
    click.option(
        "--private-key",
        type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
        help="Path to private key file",
    ),
    click.option(
        "--cert-chain",
        type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
        help="Path to certificate chain file",
    ),
]

_GEN_OPTIONS = [
    click.option(
        "-t", "--gen-type", "gen_type",
        default="pbreflect",
        type=click.Choice([e.value for e in GeneratorType]),
        help="Type of generator",
    ),
    click.option("-r", "--refresh", "refresh", is_flag=True, help="Clear output directory"),
    click.option("--async-mode", "async_mode", is_flag=True, help="Generate async client code"),
    click.option("--template-dir", "template_dir", help="Custom templates directory (pbreflect only)"),
    click.option("--gen-tests", "gen_tests", is_flag=True, help="Also generate pytest test stubs"),
    click.option("--tests-dir", "tests_dir", default="tests", help="Where to write test stubs"),
    click.option(
        "--tests-client-module", "tests_client_module",
        default="clients",
        help="Python module path for generated clients used in test imports",
    ),
]


def _apply_decorators(decorators: list[Callable[..., Any]]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        for d in reversed(decorators):
            f = d(f)
        return f
    return decorator


def _tls_flags(
    use_tls: bool,
    root_cert: pathlib.Path | None,
    private_key: pathlib.Path | None,
    cert_chain: pathlib.Path | None,
) -> bool:
    if root_cert or private_key or cert_chain:
        click.echo("TLS certificates provided, enabling TLS mode")
        return True
    if use_tls:
        click.echo("Using secure connection (TLS)")
    return use_tls


@click.group()
def cli() -> None:
    pass


@click.command("get-protos")
@click.option("-h", "--host", type=str, required=True, help="Destination host")
@click.option("-o", "--output", type=str, default="protos", help="Output directory")
@_apply_decorators(_TLS_OPTIONS)
def get_protos(
    host: str,
    output: str,
    use_tls: bool,
    root_cert: pathlib.Path | None,
    private_key: pathlib.Path | None,
    cert_chain: pathlib.Path | None,
) -> None:
    """Recover proto files from a gRPC server using reflection."""
    output_dir = pathlib.Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    use_tls = _tls_flags(use_tls, root_cert, private_key, cert_chain)

    with RecoverService(
        host, output_dir,
        use_tls=use_tls,
        root_certificates_path=root_cert,
        private_key_path=private_key,
        certificate_chain_path=cert_chain,
    ) as service:
        try:
            saved_files = service.recover_proto_files()
            if saved_files:
                click.echo(f"Successfully recovered {len(saved_files)} proto files to {output_dir}")
                for f in saved_files:
                    click.echo(f"  - {f.name}: {f}")
            else:
                click.echo("No proto files were recovered")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort() from e


@click.command("generate")
@click.option("-p", "--proto-dir", "proto_dir", required=True, help="Directory with proto files")
@click.option("-o", "--output-dir", "output_dir", required=True, help="Directory where to generate code")
@_apply_decorators(_GEN_OPTIONS)
def gen(
    proto_dir: str,
    output_dir: str,
    gen_type: str = "pbreflect",
    refresh: bool = False,
    async_mode: bool = False,
    template_dir: str | None = None,
    gen_tests: bool = False,
    tests_dir: str = "tests",
    tests_client_module: str = "clients",
) -> None:
    """Generate client code from local proto files."""
    GenerationPipeline(
        proto_dir,
        output_dir,
        GenerationOptions(
            gen_type=GeneratorType.from_str(gen_type),
            refresh=refresh,
            async_mode=async_mode,
            template_dir=template_dir,
            gen_tests=gen_tests,
            tests_dir=tests_dir,
            tests_client_module=tests_client_module,
        ),
    ).run()


@click.command("reflect")
@click.option("-h", "--host", type=str, required=True, help="Destination host")
@click.option("-o", "--output", type=str, default="clients", help="Output directory")
@_apply_decorators(_TLS_OPTIONS)
@_apply_decorators(_GEN_OPTIONS)
def generate_from_server(
    host: str,
    output: str,
    use_tls: bool,
    root_cert: pathlib.Path | None,
    private_key: pathlib.Path | None,
    cert_chain: pathlib.Path | None,
    gen_type: str = "pbreflect",
    async_mode: bool = False,
    template_dir: str | None = None,
    refresh: bool = False,
    gen_tests: bool = False,
    tests_dir: str = "tests",
    tests_client_module: str = "clients",
) -> None:
    """Generate client code directly from a running gRPC server."""
    output_dir = pathlib.Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    use_tls = _tls_flags(use_tls, root_cert, private_key, cert_chain)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        click.echo(f"Connecting to gRPC server at {host}…")

        with RecoverService(
            host, tmp_path,
            use_tls=use_tls,
            root_certificates_path=root_cert,
            private_key_path=private_key,
            certificate_chain_path=cert_chain,
        ) as service:
            try:
                saved_files = service.recover_proto_files()
                if not saved_files:
                    click.echo("No proto files were recovered")
                    return
                click.echo(f"Recovered {len(saved_files)} proto files")
            except Exception as e:
                click.echo(f"Error recovering proto files: {e}", err=True)
                raise click.Abort() from e

        click.echo(f"Generating {gen_type} client code in {output_dir}…")
        try:
            GenerationPipeline(
                str(tmp_path),
                str(output_dir),
                GenerationOptions(
                    gen_type=GeneratorType.from_str(gen_type),
                    refresh=refresh,
                    async_mode=async_mode,
                    template_dir=template_dir,
                    gen_tests=gen_tests,
                    tests_dir=tests_dir,
                    tests_client_module=tests_client_module,
                ),
            ).run()
            click.echo(f"Successfully generated client code in {output_dir}")
        except Exception as e:
            click.echo(f"Error generating client code: {e}", err=True)
            raise click.Abort() from e


cli.add_command(get_protos)
cli.add_command(gen)
cli.add_command(generate_from_server)

if __name__ == "__main__":
    cli()
