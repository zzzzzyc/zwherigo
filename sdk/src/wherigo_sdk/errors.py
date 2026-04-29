class WherigoSdkError(Exception):
    """Base SDK exception."""


class ValidationError(WherigoSdkError):
    """Raised when model validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "Validation failed:\n- " + "\n- ".join(errors)
        super().__init__(message)


class ProjectFormatError(WherigoSdkError):
    """Raised when project file content is invalid."""


class CompileError(WherigoSdkError):
    """Raised when GWC compilation fails."""


class PackagingError(WherigoSdkError):
    """Raised when Lua/GWZ artifact packaging fails."""
