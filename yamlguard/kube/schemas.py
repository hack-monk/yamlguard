"""
Kubernetes schema management and caching.

Handles downloading, caching, and managing Kubernetes OpenAPI/JSON Schemas
for different versions and resource types.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field


class KubernetesVersion(BaseModel):
    """Represents a Kubernetes version with schema information."""
    
    version: str = Field(..., description="Kubernetes version (e.g., '1.30.2')")
    major: int = Field(..., description="Major version number")
    minor: int = Field(..., description="Minor version number")
    patch: int = Field(..., description="Patch version number")
    schema_url: str = Field(..., description="URL to OpenAPI schema")
    is_stable: bool = Field(default=True, description="Whether this is a stable release")


class KubernetesResource(BaseModel):
    """Represents a Kubernetes resource type with schema information."""
    
    api_version: str = Field(..., description="API version (e.g., 'apps/v1')")
    kind: str = Field(..., description="Resource kind (e.g., 'Deployment')")
    schema: Dict[str, Any] = Field(..., description="JSON Schema for the resource")
    is_custom_resource: bool = Field(default=False, description="Whether this is a CRD")


class KubernetesSchemaManager:
    """
    Manages Kubernetes schemas and versions.
    
    Handles downloading, caching, and providing access to Kubernetes
    OpenAPI/JSON Schemas for validation.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the schema manager.
        
        Args:
            cache_dir: Directory to cache schemas (defaults to ~/.yamlguard/cache)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".yamlguard" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, KubernetesVersion] = {}
        
        # Initialize with known stable versions
        self._initialize_versions()
    
    def _initialize_versions(self) -> None:
        """Initialize known Kubernetes versions."""
        stable_versions = [
            ("1.30", "1.30.0"),
            ("1.29", "1.29.0"),
            ("1.28", "1.28.0"),
            ("1.27", "1.27.0"),
        ]
        
        for major_minor, full_version in stable_versions:
            major, minor = map(int, major_minor.split('.'))
            version = KubernetesVersion(
                version=full_version,
                major=major,
                minor=minor,
                patch=0,
                schema_url=f"https://raw.githubusercontent.com/kubernetes/kubernetes/v{full_version}/api/openapi-spec/swagger.json"
            )
            self.versions[major_minor] = version
    
    def get_schema(self, version: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get Kubernetes schema for a specific version.
        
        Args:
            version: Kubernetes version (e.g., '1.30', '1.30.2')
            force_refresh: Force refresh from remote even if cached
            
        Returns:
            Kubernetes OpenAPI schema
        """
        # Normalize version
        normalized_version = self._normalize_version(version)
        
        if normalized_version in self.schemas and not force_refresh:
            return self.schemas[normalized_version]
        
        # Check cache first
        cache_file = self.cache_dir / f"k8s-schema-{normalized_version}.json"
        if cache_file.exists() and not force_refresh:
            with open(cache_file, 'r') as f:
                schema = json.load(f)
                self.schemas[normalized_version] = schema
                return schema
        
        # Download schema
        schema = self._download_schema(normalized_version)
        
        # Cache schema
        with open(cache_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        self.schemas[normalized_version] = schema
        return schema
    
    def _normalize_version(self, version: str) -> str:
        """
        Normalize Kubernetes version string.
        
        Args:
            version: Version string (e.g., '1.30', '1.30.2')
            
        Returns:
            Normalized version string
        """
        parts = version.split('.')
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}.0"
        elif len(parts) == 3:
            return version
        else:
            raise ValueError(f"Invalid version format: {version}")
    
    def _download_schema(self, version: str) -> Dict[str, Any]:
        """
        Download Kubernetes schema from remote.
        
        Args:
            version: Kubernetes version
            
        Returns:
            Downloaded schema
        """
        # Try different schema sources
        schema_urls = [
            f"https://raw.githubusercontent.com/kubernetes/kubernetes/v{version}/api/openapi-spec/swagger.json",
            f"https://raw.githubusercontent.com/kubernetes/kubernetes/v{version}/api/openapi-spec/v3/api/swagger.json",
            f"https://raw.githubusercontent.com/kubernetes/kubernetes/v{version}/api/openapi-spec/v3/apis/swagger.json",
        ]
        
        for url in schema_urls:
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                continue
        
        raise RuntimeError(f"Failed to download schema for version {version}")
    
    def get_resource_schema(self, version: str, api_version: str, kind: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific Kubernetes resource.
        
        Args:
            version: Kubernetes version
            api_version: API version (e.g., 'apps/v1')
            kind: Resource kind (e.g., 'Deployment')
            
        Returns:
            Resource schema or None if not found
        """
        schema = self.get_schema(version)
        
        # Look for the resource in the schema
        definitions = schema.get('definitions', {})
        
        # Try different naming patterns
        resource_names = [
            f"{api_version}.{kind}",
            f"io.k8s.api.{api_version.replace('/', '.')}.{kind}",
            f"io.k8s.{api_version.replace('/', '.')}.{kind}",
            kind,
        ]
        
        for resource_name in resource_names:
            if resource_name in definitions:
                return definitions[resource_name]
        
        return None
    
    def list_available_versions(self) -> List[str]:
        """Get list of available Kubernetes versions."""
        return list(self.versions.keys())
    
    def get_latest_version(self) -> str:
        """Get the latest available Kubernetes version."""
        versions = self.list_available_versions()
        return max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    
    def validate_version(self, version: str) -> bool:
        """
        Validate if a Kubernetes version is supported.
        
        Args:
            version: Kubernetes version to validate
            
        Returns:
            True if version is supported
        """
        try:
            normalized = self._normalize_version(version)
            return normalized in self.versions or self._is_version_available(version)
        except ValueError:
            return False
    
    def _is_version_available(self, version: str) -> bool:
        """
        Check if a version is available remotely.
        
        Args:
            version: Kubernetes version to check
            
        Returns:
            True if version is available
        """
        try:
            self._download_schema(version)
            return True
        except RuntimeError:
            return False
    
    def clear_cache(self) -> None:
        """Clear the schema cache."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("k8s-schema-*.json"):
                cache_file.unlink()
        
        self.schemas.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached schemas."""
        cache_files = list(self.cache_dir.glob("k8s-schema-*.json"))
        
        return {
            'cache_dir': str(self.cache_dir),
            'cached_versions': [f.stem.replace('k8s-schema-', '') for f in cache_files],
            'total_size': sum(f.stat().st_size for f in cache_files),
            'file_count': len(cache_files),
        }
