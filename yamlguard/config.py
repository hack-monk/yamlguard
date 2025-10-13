"""
Configuration management for YAMLGuard.

Handles loading and validation of configuration from .yamlguard.yml files
and command-line arguments.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import tomli
import tomli_w
from pydantic import BaseModel, Field, validator


class IndentConfig(BaseModel):
    """Configuration for indentation checking."""
    
    step: int = Field(default=2, ge=1, le=8, description="Indentation step size in spaces")
    strict: bool = Field(default=True, description="Enforce consistent indentation")
    fix: bool = Field(default=False, description="Auto-fix indentation issues")


class CosmeticsConfig(BaseModel):
    """Configuration for YAML cosmetics checking."""
    
    enabled: bool = Field(default=True, description="Enable cosmetics checks")
    trailing_spaces: bool = Field(default=True, description="Check for trailing spaces")
    tabs: bool = Field(default=True, description="Check for tab usage")
    bom: bool = Field(default=True, description="Check for BOM presence")
    duplicate_keys: bool = Field(default=True, description="Check for duplicate keys")
    line_length: Optional[int] = Field(default=120, ge=80, description="Maximum line length")


class KubernetesConfig(BaseModel):
    """Configuration for Kubernetes validation."""
    
    enabled: bool = Field(default=False, description="Enable Kubernetes validation")
    version: str = Field(default="1.30", description="Kubernetes version to validate against")
    strict: bool = Field(default=False, description="Strict mode for schema validation")
    use_kubeconform: bool = Field(default=True, description="Use kubeconform for validation")
    cache_schemas: bool = Field(default=True, description="Cache downloaded schemas")


class SecretsConfig(BaseModel):
    """Configuration for secrets scanning."""
    
    enabled: bool = Field(default=False, description="Enable secrets scanning")
    baseline: Optional[Path] = Field(default=None, description="Baseline file for secrets")
    allowlist: List[str] = Field(default_factory=list, description="Paths to exclude from scanning")
    entropy_threshold: float = Field(default=4.5, ge=0.0, le=8.0, description="Entropy threshold for detection")
    use_detect_secrets: bool = Field(default=False, description="Use detect-secrets library")
    use_gitleaks: bool = Field(default=False, description="Use gitleaks binary")


class ReporterConfig(BaseModel):
    """Configuration for output reporting."""
    
    format: str = Field(default="stylish", description="Output format (stylish, json, jsonl)")
    color: bool = Field(default=True, description="Enable colored output")
    verbose: bool = Field(default=False, description="Verbose output")
    fail_on: str = Field(default="error", description="Fail on severity (error, warning, info)")


class Config(BaseModel):
    """Main YAMLGuard configuration."""
    
    # Core settings
    indent: IndentConfig = Field(default_factory=IndentConfig)
    cosmetics: CosmeticsConfig = Field(default_factory=CosmeticsConfig)
    kubernetes: KubernetesConfig = Field(default_factory=KubernetesConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    reporter: ReporterConfig = Field(default_factory=ReporterConfig)
    
    # File patterns
    include: List[str] = Field(default_factory=lambda: ["**/*.yaml", "**/*.yml"])
    exclude: List[str] = Field(default_factory=lambda: ["**/node_modules/**", "**/.git/**"])
    
    # CI settings
    ci: bool = Field(default=False, description="CI mode (non-interactive)")
    
    @validator("reporter")
    def validate_reporter_format(cls, v):
        """Validate reporter format."""
        valid_formats = ["stylish", "json", "jsonl"]
        if v.format not in valid_formats:
            raise ValueError(f"Invalid reporter format: {v.format}. Must be one of {valid_formats}")
        return v
    
    @validator("kubernetes")
    def validate_k8s_version(cls, v):
        """Validate Kubernetes version format."""
        # Basic version format validation (e.g., "1.30", "1.30.2")
        import re
        if not re.match(r"^\d+\.\d+(\.\d+)?$", v.version):
            raise ValueError(f"Invalid Kubernetes version format: {v.version}")
        return v
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "Config":
        """Load configuration from a TOML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix in [".yml", ".yaml"]:
                import yaml
                data = yaml.safe_load(f)
            elif config_path.suffix == ".toml":
                data = tomli.load(f)
            else:
                # Try to parse as TOML anyway
                data = tomli.load(f)
        
        return cls(**data)
    
    @classmethod
    def find_config(cls, start_path: Union[str, Path] = ".") -> Optional["Config"]:
        """Find and load configuration file from directory hierarchy."""
        start_path = Path(start_path).resolve()
        
        # Look for configuration files in order of preference
        config_names = [".yamlguard.yml", ".yamlguard.toml", "yamlguard.yml", "yamlguard.toml"]
        
        for path in [start_path] + list(start_path.parents):
            for config_name in config_names:
                config_file = path / config_name
                if config_file.exists():
                    try:
                        return cls.from_file(config_file)
                    except Exception as e:
                        print(f"Warning: Failed to load config from {config_file}: {e}")
                        continue
        
        return None
    
    def save(self, config_path: Union[str, Path]) -> None:
        """Save configuration to a TOML file."""
        config_path = Path(config_path)
        
        # Convert to dict and write as TOML
        data = self.dict()
        
        with open(config_path, "wb") as f:
            tomli_w.dump(data, f)
    
    def get_severity_threshold(self) -> int:
        """Get numeric severity threshold for filtering issues."""
        severity_map = {
            "error": 3,
            "warning": 2, 
            "info": 1,
        }
        return severity_map.get(self.reporter.fail_on, 3)
