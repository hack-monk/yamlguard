"""
Integration with gitleaks for fast secrets detection.

Provides adapter for using gitleaks binary for comprehensive secrets
detection with high performance and extensive pattern coverage.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from yamlguard.secrets.rules import SecretMatch


class GitleaksAdapter:
    """
    Adapter for gitleaks binary.
    
    Provides integration with gitleaks for fast and comprehensive secrets
    detection with extensive pattern coverage and high performance.
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize the gitleaks adapter.
        
        Args:
            config_file: Path to gitleaks configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self.available = self._check_gitleaks()
    
    def _check_gitleaks(self) -> bool:
        """Check if gitleaks is available."""
        try:
            result = subprocess.run(
                ['gitleaks', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan_file(self, file_path: Union[str, Path]) -> List[SecretMatch]:
        """
        Scan a file using gitleaks.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of detected secrets
        """
        if not self.available:
            raise RuntimeError("gitleaks is not available")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.scan_content(content, str(file_path))
    
    def scan_content(self, content: str, source: str = "<string>") -> List[SecretMatch]:
        """
        Scan content using gitleaks.
        
        Args:
            content: Content to scan
            source: Source identifier for error reporting
            
        Returns:
            List of detected secrets
        """
        if not self.available:
            raise RuntimeError("gitleaks is not available")
        
        matches = []
        
        try:
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run gitleaks
            cmd = [
                'gitleaks', 'detect',
                '--source', temp_file,
                '--report-format', 'json',
                '--no-git'
            ]
            
            if self.config_file and self.config_file.exists():
                cmd.extend(['--config', str(self.config_file)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse gitleaks output
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    matches = self._parse_gitleaks_output(output, source)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as error
                    matches.append(SecretMatch(
                        line=1,
                        column=1,
                        value="",
                        rule="gitleaks-error",
                        confidence=0.0,
                        context=f"gitleaks error: {result.stderr}",
                        path="",
                        severity="error"
                    ))
            
            # Clean up temporary file
            Path(temp_file).unlink()
            
        except subprocess.TimeoutExpired:
            matches.append(SecretMatch(
                line=1,
                column=1,
                value="",
                rule="gitleaks-timeout",
                confidence=0.0,
                context="gitleaks scan timed out",
                path="",
                severity="error"
            ))
        except Exception as e:
            matches.append(SecretMatch(
                line=1,
                column=1,
                value="",
                rule="gitleaks-error",
                confidence=0.0,
                context=f"gitleaks error: {str(e)}",
                path="",
                severity="error"
            ))
        
        return matches
    
    def _parse_gitleaks_output(self, output: Dict[str, Any], source: str) -> List[SecretMatch]:
        """
        Parse gitleaks JSON output.
        
        Args:
            output: gitleaks JSON output
            source: Source identifier
            
        Returns:
            List of secret matches
        """
        matches = []
        
        # Parse results from gitleaks output
        results = output.get('results', [])
        
        for result in results:
            line_num = result.get('line', 1)
            secret_type = result.get('ruleID', 'unknown')
            secret_value = result.get('secret', '')
            
            # Get context
            context = self._get_context_from_result(result)
            
            # Calculate confidence based on gitleaks confidence
            confidence = result.get('confidence', 0.5)
            
            match = SecretMatch(
                line=line_num,
                column=1,  # gitleaks doesn't provide column info
                value=secret_value,
                rule=f"gitleaks-{secret_type}",
                confidence=confidence,
                context=context,
                path="",  # gitleaks doesn't provide YAML path
                severity="error" if confidence > 0.8 else "warning"
            )
            
            matches.append(match)
        
        return matches
    
    def _get_context_from_result(self, result: Dict[str, Any]) -> str:
        """Get context from gitleaks result."""
        # This is a simplified implementation
        # In practice, you'd extract context from the result
        return f"Detected by gitleaks: {result.get('ruleID', 'unknown')}"
    
    def scan_directory(self, directory: Union[str, Path], 
                      output_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Scan a directory for secrets using gitleaks.
        
        Args:
            directory: Directory to scan
            output_file: Optional output file for results
            
        Returns:
            Scan results
        """
        if not self.available:
            raise RuntimeError("gitleaks is not available")
        
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        cmd = ['gitleaks', 'detect', '--source', str(directory)]
        
        if self.config_file and self.config_file.exists():
            cmd.extend(['--config', str(self.config_file)])
        
        if output_file:
            output_file = Path(output_file)
            cmd.extend(['--report-path', str(output_file)])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for directory scan
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"gitleaks scan failed: {result.stderr}")
        
        # Parse results if output file was specified
        if output_file and output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    results = json.load(f)
                return {
                    'success': True,
                    'results': results,
                    'output': result.stdout,
                    'stderr': result.stderr
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to parse results: {str(e)}",
                    'output': result.stdout,
                    'stderr': result.stderr
                }
        
        return {
            'success': True,
            'output': result.stdout,
            'stderr': result.stderr
        }
    
    def get_supported_rules(self) -> List[str]:
        """
        Get list of supported gitleaks rules.
        
        Returns:
            List of rule names
        """
        if not self.available:
            return []
        
        try:
            result = subprocess.run(
                ['gitleaks', 'help', 'detect'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse help output to extract rule information
            # This is a simplified implementation
            return ["aws-access-key", "github-token", "slack-token", "generic-api-key"]
        except Exception:
            return []
    
    def create_config(self, output_file: Union[str, Path], 
                     custom_rules: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Create a gitleaks configuration file.
        
        Args:
            output_file: Output file for configuration
            custom_rules: Optional custom rules to include
        """
        output_file = Path(output_file)
        
        # Default gitleaks configuration
        config = {
            "version": "8.18.0",
            "rules": [
                {
                    "id": "aws-access-key",
                    "description": "AWS Access Key",
                    "regex": "AKIA[0-9A-Z]{16}",
                    "severity": "high"
                },
                {
                    "id": "github-token",
                    "description": "GitHub Token",
                    "regex": "ghp_[A-Za-z0-9]{36}",
                    "severity": "high"
                }
            ]
        }
        
        # Add custom rules if provided
        if custom_rules:
            config["rules"].extend(custom_rules)
        
        # Write configuration file
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
