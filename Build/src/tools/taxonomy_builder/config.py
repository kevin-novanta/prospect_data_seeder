#
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    profile: str
    output_dir: Path
    schema_path: Path
    log_level: str

    @classmethod
    def load(cls):
        """
        Load configuration from environment variables.
        """
        return cls(
            profile=os.getenv("PROFILE", "dev"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./data")),
            schema_path=Path(os.getenv("SCHEMA_PATH", "./schema/taxonomy.schema.json")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @staticmethod
    def load_settings():
        """
        Return a dict of configuration settings from environment variables.
        """
        return {
            "PROFILE": os.getenv("PROFILE", "dev"),
            "OUTPUT_DIR": os.getenv("OUTPUT_DIR", "./data"),
            "SCHEMA_PATH": os.getenv("SCHEMA_PATH", "./schema/taxonomy.schema.json"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }


# Module-level helpers for callers expecting functions

def load():
    """Return a Config instance resolved from environment variables."""
    return Config.load()


def load_settings():
    """Return a dict of configuration settings from environment variables."""
    return Config.load_settings()
