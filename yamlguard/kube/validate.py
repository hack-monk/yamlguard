"""
Kubernetes manifest validation using JSON Schema and kubeconform.

Provides validation of Kubernetes manifests against official schemas
with support for both Python jsonschema and external kubeconform binary.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import jsonschema
from pydantic import BaseModel, Field

from yamlguard.kube.schemas import KubernetesSchemaManager


class KubernetesValidationError(BaseModel):
    """Represents a Kubernetes validation error."""
    
    line: int = Field(..., description="Line number (1-based)")
    column: int = Field(..., description="Column number (1-based)")
    path: str = Field(..., description="JSON path to the error")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="error", description="Error severity")
    rule: str = Field(..., description="Validation rule that failed")


class KubernetesValidator:
    """
    Validates Kubernetes manifests against official schemas.
    
    Supports both Python jsonschema validation and external kubeconform
    for comprehensive validation including CRDs and latest schemas.
    """
    
    def __init__(self, version: str = "1.30", use_kubeconform: bool = True, 
                 strict: bool = False):
        """
        Initialize the Kubernetes validator.
        
        Args:
            version: Kubernetes version to validate against
            use_kubeconform: Whether to use kubeconform for validation
            strict: Whether to use strict validation mode
        """
        self.version = version
        self.use_kubeconform = use_kubeconform
        self.strict = strict
        self.schema_manager = KubernetesSchemaManager()
        
        # Check if kubeconform is available
        self.kubeconform_available = self._check_kubeconform()
    
    def _check_kubeconform(self) -> bool:
        """Check if kubeconform binary is available."""
        try:
            result = subprocess.run(
                ['kubeconform', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def validate_file(self, file_path: Union[str, Path]) -> List[KubernetesValidationError]:
        """
        Validate a Kubernetes manifest file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            List of validation errors
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.validate_content(content, str(file_path))
    
    def validate_content(self, content: str, source: str = "<string>") -> List[KubernetesValidationError]:
        """
        Validate Kubernetes manifest content.
        
        Args:
            content: YAML content to validate
            source: Source identifier for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Parse YAML documents
        documents = self._parse_yaml_documents(content)
        
        for doc_index, doc in enumerate(documents):
            if not self._is_kubernetes_manifest(doc):
                continue
            
            # Validate each document
            doc_errors = self._validate_document(doc, source, doc_index)
            errors.extend(doc_errors)
        
        return errors
    
    def _parse_yaml_documents(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML content into separate documents."""
        from ruamel.yaml import YAML
        
        yaml = YAML()
        documents = []
        
        # Split by document separators
        parts = content.split('---')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            try:
                doc = yaml.load(part)
                if doc is not None:
                    documents.append(doc)
            except Exception:
                # Skip invalid documents
                continue
        
        return documents
    
    def _is_kubernetes_manifest(self, doc: Dict[str, Any]) -> bool:
        """Check if a document is a Kubernetes manifest."""
        return (
            isinstance(doc, dict) and
            'apiVersion' in doc and
            'kind' in doc and
            'metadata' in doc
        )
    
    def _validate_document(self, doc: Dict[str, Any], source: str, 
                          doc_index: int) -> List[KubernetesValidationError]:
        """Validate a single Kubernetes document."""
        errors = []
        
        # Get basic manifest info
        api_version = doc.get('apiVersion', '')
        kind = doc.get('kind', '')
        
        if not api_version or not kind:
            errors.append(KubernetesValidationError(
                line=1,
                column=1,
                path="",
                message="Missing required fields: apiVersion or kind",
                severity="error",
                rule="required-fields"
            ))
            return errors
        
        # Use kubeconform if available and preferred
        if self.use_kubeconform and self.kubeconform_available:
            kubeconform_errors = self._validate_with_kubeconform(doc, source, doc_index)
            errors.extend(kubeconform_errors)
        else:
            # Fall back to Python jsonschema validation
            schema_errors = self._validate_with_schema(doc, api_version, kind, source, doc_index)
            errors.extend(schema_errors)
        
        return errors
    
    def _validate_with_kubeconform(self, doc: Dict[str, Any], source: str, 
                                  doc_index: int) -> List[KubernetesValidationError]:
        """Validate using kubeconform binary."""
        errors = []
        
        try:
            # Write document to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                import yaml
                yaml.dump(doc, f, default_flow_style=False)
                temp_file = f.name
            
            # Run kubeconform
            cmd = [
                'kubeconform',
                '-kubernetes-version', self.version,
                '-output', 'json',
                temp_file
            ]
            
            if self.strict:
                cmd.append('-strict')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse kubeconform output
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    for item in output:
                        if item.get('status') == 'FAIL':
                            errors.append(KubernetesValidationError(
                                line=1,  # kubeconform doesn't provide line numbers
                                column=1,
                                path=item.get('path', ''),
                                message=item.get('msg', 'Validation failed'),
                                severity="error",
                                rule=item.get('rule', 'unknown')
                            ))
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as error
                    errors.append(KubernetesValidationError(
                        line=1,
                        column=1,
                        path="",
                        message=f"kubeconform validation failed: {result.stderr}",
                        severity="error",
                        rule="kubeconform-error"
                    ))
            
            # Clean up temporary file
            Path(temp_file).unlink()
            
        except subprocess.TimeoutExpired:
            errors.append(KubernetesValidationError(
                line=1,
                column=1,
                path="",
                message="kubeconform validation timed out",
                severity="error",
                rule="timeout"
            ))
        except Exception as e:
            errors.append(KubernetesValidationError(
                line=1,
                column=1,
                path="",
                message=f"kubeconform validation error: {str(e)}",
                severity="error",
                rule="kubeconform-error"
            ))
        
        return errors
    
    def _validate_with_schema(self, doc: Dict[str, Any], api_version: str, 
                             kind: str, source: str, doc_index: int) -> List[KubernetesValidationError]:
        """Validate using Python jsonschema."""
        errors = []
        
        try:
            # Get schema for the resource
            schema = self.schema_manager.get_resource_schema(self.version, api_version, kind)
            
            if not schema:
                errors.append(KubernetesValidationError(
                    line=1,
                    column=1,
                    path="",
                    message=f"No schema found for {api_version}/{kind}",
                    severity="warning",
                    rule="missing-schema"
                ))
                return errors
            
            # Validate against schema
            validator = jsonschema.Draft7Validator(schema)
            
            for error in validator.iter_errors(doc):
                # Convert jsonschema error to our format
                path = '.'.join(str(p) for p in error.absolute_path)
                
                errors.append(KubernetesValidationError(
                    line=1,  # jsonschema doesn't provide line numbers
                    column=1,
                    path=path,
                    message=error.message,
                    severity="error",
                    rule=error.validator
                ))
        
        except Exception as e:
            errors.append(KubernetesValidationError(
                line=1,
                column=1,
                path="",
                message=f"Schema validation error: {str(e)}",
                severity="error",
                rule="schema-error"
            ))
        
        return errors
    
    def validate_batch(self, file_paths: List[Union[str, Path]]) -> Dict[str, List[KubernetesValidationError]]:
        """
        Validate multiple files in batch.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to validation errors
        """
        results = {}
        
        for file_path in file_paths:
            try:
                errors = self.validate_file(file_path)
                results[str(file_path)] = errors
            except Exception as e:
                # Add error for file processing failure
                results[str(file_path)] = [KubernetesValidationError(
                    line=1,
                    column=1,
                    path="",
                    message=f"Failed to process file: {str(e)}",
                    severity="error",
                    rule="file-error"
                )]
        
        return results
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported Kubernetes versions."""
        return self.schema_manager.list_available_versions()
    
    def is_version_supported(self, version: str) -> bool:
        """Check if a Kubernetes version is supported."""
        return self.schema_manager.validate_version(version)
