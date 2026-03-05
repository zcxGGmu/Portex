"""Authentication service placeholder."""


class AuthService:
    """Minimal auth service interface for scaffolding stage."""

    def authenticate(self, username: str, password: str) -> bool:
        """Return a deterministic placeholder auth result."""
        return bool(username and password)
