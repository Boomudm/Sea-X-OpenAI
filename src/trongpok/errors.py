"""Reader errors that callers can handle without inspecting SDK exceptions."""


class ReaderError(Exception):
    """Base class for U2 reader failures."""


class ReaderConfigurationError(ReaderError):
    """The local reader configuration is missing or unusable."""


class ReaderInputError(ReaderError):
    """Captured input does not satisfy the shared contract."""


class InvalidReaderOutput(ReaderError):
    """The model returned JSON or evidence that failed code validation."""

    valid = False


class ReaderUnavailableError(ReaderError):
    """The model call failed and the durable cache was incomplete."""
