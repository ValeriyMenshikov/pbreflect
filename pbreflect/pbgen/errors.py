"""Module for custom errors"""


class GenerationFailedError(Exception):
    """Class for exception while generating stubs"""

    def __init__(self, message: str = None) -> None:
        self.message = message or "Errors while generating stubs! Check logs."
        super().__init__(self.message)


class NoProtoFilesError(Exception):
    """Class for exception if input directory without proto files"""

    def __init__(self, include_dir: str) -> None:
        self.message = f"Proto files not found by path: {include_dir}!"
        super().__init__(self.message)
