"""Custom exceptions for PowerGuard backend."""


class PowerGuardException(Exception):
    """Base exception for PowerGuard."""
    pass


class AnalysisException(PowerGuardException):
    """Exception raised during device analysis."""
    pass


class RateLimitException(PowerGuardException):
    """Exception raised when rate limit is exceeded."""
    pass


class ValidationException(PowerGuardException):
    """Exception raised during data validation."""
    pass


class DatabaseException(PowerGuardException):
    """Exception raised during database operations."""
    pass