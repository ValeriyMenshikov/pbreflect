import pathlib

from pgreflect.protorecover.recover_service import RecoverService


extractor = RecoverService(
    "10.227.44.45:82", output_dir=pathlib.Path("./recovered_protos")
)
extractor.recover_protos()
