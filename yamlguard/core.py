"""
Core YAMLGuard class.

Provides the main interface for all YAMLGuard functionality including
linting, validation, secrets scanning, and fixing.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from yamlguard.config import Config
from yamlguard.cosmetics import CosmeticsChecker
from yamlguard.indent_checker import IndentationChecker
from yamlguard.kube import KubernetesValidator
from yamlguard.loader import YAMLLoader
from yamlguard.reporters import Reporter, StylishReporter, JSONLReporter
from yamlguard.secrets import SecretsRuleEngine, DetectSecretsAdapter, GitleaksAdapter


class YAMLGuard:
    """
    Main YAMLGuard class providing comprehensive YAML validation.
    
    Integrates all YAMLGuard functionality including indentation checking,
    cosmetics linting, Kubernetes validation, and secrets scanning.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize YAMLGuard.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or Config()
        
        # Initialize components
        self.indent_checker = IndentationChecker(
            indent_step=self.config.indent.step,
            strict=self.config.indent.strict
        )
        
        self.cosmetics_checker = CosmeticsChecker(
            line_length=self.config.cosmetics.line_length or 120,
            strict=self.config.cosmetics.enabled
        )
        
        self.kube_validator = KubernetesValidator(
            version=self.config.kubernetes.version,
            use_kubeconform=self.config.kubernetes.use_kubeconform,
            strict=self.config.kubernetes.strict
        )
        
        self.secrets_engine = SecretsRuleEngine(
            entropy_threshold=self.config.secrets.entropy_threshold
        )
        
        self.detect_secrets_adapter = DetectSecretsAdapter(
            baseline_file=self.config.secrets.baseline
        )
        
        self.gitleaks_adapter = GitleaksAdapter()
        
        self.yaml_loader = YAMLLoader()
    
    def lint_files(self, paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Lint YAML files for indentation and style issues.
        
        Args:
            paths: List of file or directory paths to lint
            
        Returns:
            List of validation results
        """
        results = []
        
        for path in paths:
            path = Path(path)
            
            if path.is_file():
                # Lint single file
                result = self._lint_file(path)
                results.append(result)
            elif path.is_dir():
                # Lint directory
                yaml_files = self._find_yaml_files(path)
                for yaml_file in yaml_files:
                    result = self._lint_file(yaml_file)
                    results.append(result)
            else:
                # Path doesn't exist
                results.append({
                    'file_path': str(path),
                    'success': False,
                    'errors': [{'message': f'File not found: {path}', 'severity': 'error'}],
                    'warnings': [],
                    'info': [],
                    'duration': 0.0
                })
        
        return results
    
    def _lint_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Lint a single YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Validation result dictionary
        """
        start_time = time.time()
        
        try:
            # Check indentation
            indent_errors = self.indent_checker.check_file(file_path)
            
            # Check cosmetics
            cosmetics_errors = self.cosmetics_checker.check_file(file_path)
            
            # Combine errors
            all_errors = []
            
            # Add indentation errors
            for error in indent_errors:
                all_errors.append({
                    'type': 'indentation',
                    'line': error.line,
                    'column': error.column,
                    'rule': 'indentation',
                    'message': error.message,
                    'severity': error.severity,
                    'path': error.path
                })
            
            # Add cosmetics errors
            for error in cosmetics_errors:
                all_errors.append({
                    'type': 'cosmetics',
                    'line': error.line,
                    'column': error.column,
                    'rule': error.rule,
                    'message': error.message,
                    'severity': error.severity,
                    'path': ''
                })
            
            # Categorize errors
            errors = [e for e in all_errors if e['severity'] == 'error']
            warnings = [e for e in all_errors if e['severity'] == 'warning']
            info = [e for e in all_errors if e['severity'] == 'info']
            
            duration = time.time() - start_time
            
            return {
                'file_path': str(file_path),
                'success': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'info': info,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'file_path': str(file_path),
                'success': False,
                'errors': [{'message': f'Error processing file: {str(e)}', 'severity': 'error'}],
                'warnings': [],
                'info': [],
                'duration': duration
            }
    
    def kube_validate_files(self, paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Validate Kubernetes manifests.
        
        Args:
            paths: List of file or directory paths to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        for path in paths:
            path = Path(path)
            
            if path.is_file():
                # Validate single file
                result = self._kube_validate_file(path)
                results.append(result)
            elif path.is_dir():
                # Validate directory
                yaml_files = self._find_yaml_files(path)
                for yaml_file in yaml_files:
                    result = self._kube_validate_file(yaml_file)
                    results.append(result)
            else:
                # Path doesn't exist
                results.append({
                    'file_path': str(path),
                    'success': False,
                    'errors': [{'message': f'File not found: {path}', 'severity': 'error'}],
                    'warnings': [],
                    'info': [],
                    'duration': 0.0
                })
        
        return results
    
    def _kube_validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a single Kubernetes manifest file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Validation result dictionary
        """
        start_time = time.time()
        
        try:
            # Validate with Kubernetes validator
            kube_errors = self.kube_validator.validate_file(file_path)
            
            # Convert to our format
            errors = []
            warnings = []
            info = []
            
            for error in kube_errors:
                error_dict = {
                    'type': 'kubernetes',
                    'line': error.line,
                    'column': error.column,
                    'rule': error.rule,
                    'message': error.message,
                    'severity': error.severity,
                    'path': error.path
                }
                
                if error.severity == 'error':
                    errors.append(error_dict)
                elif error.severity == 'warning':
                    warnings.append(error_dict)
                else:
                    info.append(error_dict)
            
            duration = time.time() - start_time
            
            return {
                'file_path': str(file_path),
                'success': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'info': info,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'file_path': str(file_path),
                'success': False,
                'errors': [{'message': f'Error validating file: {str(e)}', 'severity': 'error'}],
                'warnings': [],
                'info': [],
                'duration': duration
            }
    
    def scan_secrets_files(self, paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Scan files for secrets.
        
        Args:
            paths: List of file or directory paths to scan
            
        Returns:
            List of validation results
        """
        results = []
        
        for path in paths:
            path = Path(path)
            
            if path.is_file():
                # Scan single file
                result = self._scan_secrets_file(path)
                results.append(result)
            elif path.is_dir():
                # Scan directory
                yaml_files = self._find_yaml_files(path)
                for yaml_file in yaml_files:
                    result = self._scan_secrets_file(yaml_file)
                    results.append(result)
            else:
                # Path doesn't exist
                results.append({
                    'file_path': str(path),
                    'success': False,
                    'errors': [{'message': f'File not found: {path}', 'severity': 'error'}],
                    'warnings': [],
                    'info': [],
                    'duration': 0.0
                })
        
        return results
    
    def _scan_secrets_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a single file for secrets.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Validation result dictionary
        """
        start_time = time.time()
        
        try:
            # Use different scanners based on configuration
            all_secrets = []
            
            # Use native rules engine
            if not self.config.secrets.use_detect_secrets and not self.config.secrets.use_gitleaks:
                secrets = self.secrets_engine.scan_file(file_path)
                all_secrets.extend(secrets)
            
            # Use detect-secrets if configured
            if self.config.secrets.use_detect_secrets and self.detect_secrets_adapter.available:
                try:
                    secrets = self.detect_secrets_adapter.scan_file(file_path)
                    all_secrets.extend(secrets)
                except Exception as e:
                    all_secrets.append({
                        'message': f'detect-secrets error: {str(e)}',
                        'severity': 'error'
                    })
            
            # Use gitleaks if configured
            if self.config.secrets.use_gitleaks and self.gitleaks_adapter.available:
                try:
                    secrets = self.gitleaks_adapter.scan_file(file_path)
                    all_secrets.extend(secrets)
                except Exception as e:
                    all_secrets.append({
                        'message': f'gitleaks error: {str(e)}',
                        'severity': 'error'
                    })
            
            # Convert to our format
            errors = []
            warnings = []
            info = []
            
            for secret in all_secrets:
                if hasattr(secret, 'dict'):
                    # It's a SecretMatch object
                    secret_dict = secret.dict()
                elif hasattr(secret, 'to_dict'):
                    # It's a SecretMatch object
                    secret_dict = secret.to_dict()
                else:
                    # It's already a dictionary
                    secret_dict = secret
                
                error_dict = {
                    'type': 'secrets',
                    'line': secret_dict.get('line', 0),
                    'column': secret_dict.get('column', 0),
                    'rule': secret_dict.get('rule', 'unknown'),
                    'message': secret_dict.get('message', 'Unknown secret'),
                    'severity': secret_dict.get('severity', 'error'),
                    'path': secret_dict.get('path', ''),
                    'context': secret_dict.get('context', '')
                }
                
                if error_dict['severity'] == 'error':
                    errors.append(error_dict)
                elif error_dict['severity'] == 'warning':
                    warnings.append(error_dict)
                else:
                    info.append(error_dict)
            
            duration = time.time() - start_time
            
            return {
                'file_path': str(file_path),
                'success': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'info': info,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'file_path': str(file_path),
                'success': False,
                'errors': [{'message': f'Error scanning file: {str(e)}', 'severity': 'error'}],
                'warnings': [],
                'info': [],
                'duration': duration
            }
    
    def fix_files(self, paths: List[Union[str, Path]], 
                  in_place: bool = False, backup: bool = False) -> List[Dict[str, Any]]:
        """
        Fix indentation issues in YAML files.
        
        Args:
            paths: List of file or directory paths to fix
            in_place: Whether to modify files in place
            backup: Whether to create backup files
            
        Returns:
            List of fix results
        """
        results = []
        
        for path in paths:
            path = Path(path)
            
            if path.is_file():
                # Fix single file
                result = self._fix_file(path, in_place, backup)
                results.append(result)
            elif path.is_dir():
                # Fix directory
                yaml_files = self._find_yaml_files(path)
                for yaml_file in yaml_files:
                    result = self._fix_file(yaml_file, in_place, backup)
                    results.append(result)
            else:
                # Path doesn't exist
                results.append({
                    'file': str(path),
                    'success': False,
                    'error': f'File not found: {path}'
                })
        
        return results
    
    def _fix_file(self, file_path: Path, in_place: bool, backup: bool) -> Dict[str, Any]:
        """
        Fix a single YAML file.
        
        Args:
            file_path: Path to the YAML file
            in_place: Whether to modify the file in place
            backup: Whether to create a backup
            
        Returns:
            Fix result dictionary
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix indentation
            fixed_content = self.indent_checker.fix_indentation(content, self.config.indent.step)
            
            # Fix cosmetics
            fixed_content = self.cosmetics_checker.fix_cosmetics(fixed_content)
            
            if in_place:
                # Create backup if requested
                if backup:
                    backup_path = file_path.with_suffix(f'{file_path.suffix}.bak')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                return {
                    'file': str(file_path),
                    'success': True,
                    'error': None
                }
            else:
                # Return fixed content
                return {
                    'file': str(file_path),
                    'success': True,
                    'error': None,
                    'content': fixed_content
                }
                
        except Exception as e:
            return {
                'file': str(file_path),
                'success': False,
                'error': str(e)
            }
    
    def _find_yaml_files(self, directory: Path) -> List[Path]:
        """
        Find YAML files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of YAML file paths
        """
        yaml_files = []
        
        # Get include patterns
        include_patterns = self.config.include
        exclude_patterns = self.config.exclude
        
        # Find files matching include patterns
        for pattern in include_patterns:
            if pattern.startswith('**/'):
                # Recursive pattern
                pattern = pattern[3:]  # Remove '**/'
                for file_path in directory.rglob(pattern):
                    if file_path.is_file():
                        yaml_files.append(file_path)
            else:
                # Non-recursive pattern
                for file_path in directory.glob(pattern):
                    if file_path.is_file():
                        yaml_files.append(file_path)
        
        # Remove files matching exclude patterns
        for pattern in exclude_patterns:
            if pattern.startswith('**/'):
                # Recursive pattern
                pattern = pattern[3:]  # Remove '**/'
                yaml_files = [f for f in yaml_files if not f.match(pattern)]
            else:
                # Non-recursive pattern
                yaml_files = [f for f in yaml_files if not f.match(pattern)]
        
        return yaml_files
