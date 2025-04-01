"""
Constants and enums shared across the spongecake package.
"""
import enum

class AgentStatus(enum.Enum):
    """Status of an agent action."""
    COMPLETE = "complete"           # Action completed successfully
    NEEDS_INPUT = "needs_input"     # Agent needs more input from the user
    NEEDS_SAFETY_CHECK = "needs_safety_check"  # Safety check needs acknowledgment
    ERROR = "error"                 # An error occurred
