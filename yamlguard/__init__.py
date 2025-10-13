"""
YAMLGuard: Fast, accurate CLI for YAML indentation and Kubernetes manifest validation.

A comprehensive tool for validating YAML files with focus on:
- Precise indentation checking and auto-fixing
- Kubernetes manifest schema validation
- Optional secrets scanning
- CI/CD integration with rich reporting
"""

__version__ = "0.1.0"
__author__ = "YAMLGuard Team"
__email__ = "team@yamlguard.dev"

from yamlguard.core import YAMLGuard
from yamlguard.config import Config
from yamlguard.reporters import Reporter, StylishReporter, JSONLReporter

__all__ = [
    "YAMLGuard",
    "Config", 
    "Reporter",
    "StylishReporter",
    "JSONLReporter",
]
