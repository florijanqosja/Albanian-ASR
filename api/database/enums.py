import enum


class MediaProcessingStatus(str, enum.Enum):
    """Lifecycle states for uploaded media assets."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
