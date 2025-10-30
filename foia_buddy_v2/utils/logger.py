"""
Enhanced logging for demo purposes.
Captures agent decisions and reasoning for visualization.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    """Structured log entry for agent activities."""
    timestamp: str
    agent_name: str
    level: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DemoLogger:
    """
    Enhanced logger that captures structured logs for demo visualization.
    """

    def __init__(self, name: str):
        self.name = name
        self.entries: List[LogEntry] = []
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    def log(self, level: str, message: str, **metadata):
        """Log a message with metadata."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            agent_name=self.name,
            level=level,
            message=message,
            metadata=metadata
        )
        self.entries.append(entry)
        self.logger.log(getattr(logging, level.upper()), message)

    def info(self, message: str, **metadata):
        """Log info level message."""
        self.log("INFO", message, **metadata)

    def warning(self, message: str, **metadata):
        """Log warning level message."""
        self.log("WARNING", message, **metadata)

    def error(self, message: str, **metadata):
        """Log error level message."""
        self.log("ERROR", message, **metadata)

    def debug(self, message: str, **metadata):
        """Log debug level message."""
        self.log("DEBUG", message, **metadata)

    def get_entries(self) -> List[LogEntry]:
        """Get all log entries."""
        return self.entries

    def clear(self):
        """Clear all log entries."""
        self.entries = []
