"""
Integration with detect-secrets library.

Provides adapter for using detect-secrets for comprehensive secrets detection
with baseline support and advanced pattern matching.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from yamlguard.secrets.rules import SecretMatch


class DetectSecretsAdapter:
    """
    Adapter for detect-secrets library.
    
    Provides integration with detect-secrets for comprehensive secrets
    detection with baseline support and advanced pattern matching.
    """
    
    def __init__(self, baseline_file: Optional[Union[str, Path]] = None):
        """
        Initialize the detect-secrets adapter.
        
        Args:
            baseline_file: Path to baseline file for known secrets
        """
        self.baseline_file = Path(baseline_file) if baseline_file else None
        self.available = self._check_detect_secrets()
    
    def _check_detect_secrets(self) -> bool:
        """Check if detect-secrets is available."""
        try:
            result = subprocess.run(
                ['detect-secrets', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan_file(self, file_path: Union[str, Path]) -> List[SecretMatch]:
        """
        Scan a file using detect-secrets.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of detected secrets
        """
        if not self.available:
            raise RuntimeError("detect-secrets is not available")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.scan_content(content, str(file_path))
    
    def scan_content(self, content: str, source: str = "<string>") -> List[SecretMatch]:
        """
        Scan content using detect-secrets.
        
        Args:
            content: Content to scan
            source: Source identifier for error reporting
            
        Returns:
            List of detected secrets
        """
        if not self.available:
            raise RuntimeError("detect-secrets is not available")
        
        matches = []
        
        try:
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run detect-secrets
            cmd = ['detect-secrets', 'scan', '--baseline', temp_file]
            
            if self.baseline_file and self.baseline_file.exists():
                cmd.extend(['--baseline', str(self.baseline_file)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse detect-secrets output
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    matches = self._parse_detect_secrets_output(output, source)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as error
                    matches.append(SecretMatch(
                        line=1,
                        column=1,
                        value="",
                        rule="detect-secrets-error",
                        confidence=0.0,
                        context=f"detect-secrets error: {result.stderr}",
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
                rule="detect-secrets-timeout",
                confidence=0.0,
                context="detect-secrets scan timed out",
                path="",
                severity="error"
            ))
        except Exception as e:
            matches.append(SecretMatch(
                line=1,
                column=1,
                value="",
                rule="detect-secrets-error",
                confidence=0.0,
                context=f"detect-secrets error: {str(e)}",
                path="",
                severity="error"
            ))
        
        return matches
    
    def _parse_detect_secrets_output(self, output: Dict[str, Any], source: str) -> List[SecretMatch]:
        """
        Parse detect-secrets JSON output.
        
        Args:
            output: detect-secrets JSON output
            source: Source identifier
            
        Returns:
            List of secret matches
        """
        matches = []
        
        # Parse results from detect-secrets output
        results = output.get('results', {})
        
        for file_path, file_results in results.items():
            if file_path != source:
                continue
            
            for result in file_results:
                line_num = result.get('line_number', 1)
                secret_type = result.get('type', 'unknown')
                secret_value = result.get('secret', '')
                
                # Get context
                context = self._get_context_from_result(result)
                
                # Calculate confidence based on detect-secrets confidence
                confidence = result.get('confidence', 0.5)
                
                match = SecretMatch(
                    line=line_num,
                    column=1,  # detect-secrets doesn't provide column info
                    value=secret_value,
                    rule=f"detect-secrets-{secret_type}",
                    confidence=confidence,
                    context=context,
                    path="",  # detect-secrets doesn't provide YAML path
                    severity="error" if confidence > 0.8 else "warning"
                )
                
                matches.append(match)
        
        return matches
    
    def _get_context_from_result(self, result: Dict[str, Any]) -> str:
        """Get context from detect-secrets result."""
        # This is a simplified implementation
        # In practice, you'd extract context from the result
        return f"Detected by detect-secrets: {result.get('type', 'unknown')}"
    
    def create_baseline(self, file_paths: List[Union[str, Path]], 
                       output_file: Union[str, Path]) -> None:
        """
        Create a baseline file for known secrets.
        
        Args:
            file_paths: List of files to scan for baseline
            output_file: Output file for baseline
        """
        if not self.available:
            raise RuntimeError("detect-secrets is not available")
        
        output_file = Path(output_file)
        
        # Run detect-secrets to create baseline
        cmd = ['detect-secrets', 'scan', '--baseline', str(output_file)]
        cmd.extend(str(p) for p in file_paths)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create baseline: {result.stderr}")
    
    def audit_baseline(self, baseline_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Audit a baseline file for false positives.
        
        Args:
            baseline_file: Path to baseline file
            
        Returns:
            Audit results
        """
        if not self.available:
            raise RuntimeError("detect-secrets is not available")
        
        baseline_file = Path(baseline_file)
        
        if not baseline_file.exists():
            raise FileNotFoundError(f"Baseline file not found: {baseline_file}")
        
        # Run detect-secrets audit
        cmd = ['detect-secrets', 'audit', str(baseline_file)]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to audit baseline: {result.stderr}")
        
        # Parse audit results
        try:
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            return {
                'total_secrets': len(baseline_data.get('results', {})),
                'audit_output': result.stdout,
                'audit_stderr': result.stderr
            }
        except Exception as e:
            return {
                'error': f"Failed to parse baseline: {str(e)}",
                'audit_output': result.stdout,
                'audit_stderr': result.stderr
            }
