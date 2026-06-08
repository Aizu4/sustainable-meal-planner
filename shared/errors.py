class ScrapeError(Exception):
    pass


class TransientScrapeError(ScrapeError):
    """Retryable failure: HTTP 5xx, connection error, timeout, rate limit."""


class FatalScrapeError(ScrapeError):
    """Non-retryable failure for a single recipe: malformed response, validation error, HTTP 4xx."""
