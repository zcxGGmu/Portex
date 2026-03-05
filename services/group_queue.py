"""Group queue service placeholder."""


class GroupQueueService:
    """In-memory queue placeholder for group scheduling."""

    def __init__(self) -> None:
        self._queue: list[str] = []

    def enqueue(self, item: str) -> None:
        self._queue.append(item)
