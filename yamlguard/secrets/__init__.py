"""
Secrets scanning module for YAMLGuard.

Provides comprehensive secrets detection using regex patterns, entropy analysis,
and integration with external tools like detect-secrets and gitleaks.
"""

from yamlguard.secrets.rules import SecretsRuleEngine
from yamlguard.secrets.detect_secrets import DetectSecretsAdapter
from yamlguard.secrets.gitleaks import GitleaksAdapter

__all__ = [
    "SecretsRuleEngine",
    "DetectSecretsAdapter", 
    "GitleaksAdapter",
]
