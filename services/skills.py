"""Skills service placeholder."""


class SkillsService:
    """Minimal in-memory skills registry."""

    def __init__(self) -> None:
        self._skills: set[str] = set()

    def register(self, skill_name: str) -> None:
        self._skills.add(skill_name)
