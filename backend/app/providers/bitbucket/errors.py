"""Bitbucket client errors. Messages must never include tokens."""


class BitbucketError(Exception):
    """Base error for Bitbucket connectivity and REST failures."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BitbucketNotConfiguredError(BitbucketError):
    def __init__(self, message: str = "Bitbucket is not configured") -> None:
        super().__init__(message, status_code=503)


class BitbucketAuthError(BitbucketError):
    def __init__(self, message: str = "Bitbucket authentication failed") -> None:
        super().__init__(message, status_code=502)


class BitbucketNotFoundError(BitbucketError):
    def __init__(self, message: str = "Bitbucket resource not found") -> None:
        super().__init__(message, status_code=404)


class BitbucketUnavailableError(BitbucketError):
    def __init__(self, message: str = "Bitbucket is unreachable") -> None:
        super().__init__(message, status_code=502)
