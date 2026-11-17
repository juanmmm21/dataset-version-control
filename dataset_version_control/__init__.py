"""Content-addressed dataset version control: commits, checkout and record-level diffs."""

from .dvc import DatasetVCS, CommitMetadata

__version__ = "0.1.0"

__all__ = ['DatasetVCS', 'CommitMetadata']
