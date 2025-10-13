"""
JSONL reporter for YAMLGuard.

Provides JSON Lines output format suitable for machine processing
and integration with CI/CD pipelines.
"""

import json
from typing import List

from yamlguard.reporters.base import Reporter, ValidationResult


class JSONLReporter(Reporter):
    """
    JSONL reporter for machine-readable output.
    
    Provides JSON Lines output format suitable for machine processing
    and integration with CI/CD pipelines.
    """
    
    def __init__(self, color: bool = False, verbose: bool = False):
        """
        Initialize the JSONL reporter.
        
        Args:
            color: Whether to use colored output (ignored for JSONL)
            verbose: Whether to use verbose output
        """
        super().__init__(color=False, verbose=verbose)  # JSONL doesn't use colors
    
    def report(self, results: List[ValidationResult]) -> str:
        """
        Generate a JSONL report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            JSONL formatted report string
        """
        if not results:
            return ""
        
        # Get summary statistics
        summary = self._get_summary(results)
        
        # Generate JSONL output
        lines = []
        
        # Add summary line
        summary_line = {
            "type": "summary",
            "files": summary['files'],
            "errors": summary['errors'],
            "warnings": summary['warnings'],
            "info": summary['info'],
            "success": summary['success'],
            "total_issues": summary['errors'] + summary['warnings'] + summary['info']
        }
        lines.append(json.dumps(summary_line))
        
        # Add file results
        for result in results:
            if result.get('errors') or result.get('warnings') or result.get('info'):
                file_line = {
                    "type": "file",
                    "file_path": result.get('file_path', 'unknown'),
                    "success": result.get('success', True),
                    "duration": result.get('duration', 0.0),
                    "errors": result.get('errors', []),
                    "warnings": result.get('warnings', []),
                    "info": result.get('info', [])
                }
                lines.append(json.dumps(file_line))
        
        return "\n".join(lines)
    
    def report_file(self, file_path: str, errors: List[dict]) -> str:
        """
        Generate a JSONL report for a single file.
        
        Args:
            file_path: Path to the file
            errors: List of errors for the file
            
        Returns:
            JSONL formatted report string
        """
        # Categorize errors by severity
        categorized = self._categorize_errors(errors)
        
        # Create file result
        file_result = {
            "type": "file",
            "file_path": file_path,
            "success": len(categorized['errors']) == 0,
            "errors": categorized['errors'],
            "warnings": categorized['warnings'],
            "info": categorized['info']
        }
        
        return json.dumps(file_result)
    
    def report_error(self, error: dict) -> str:
        """
        Generate a JSONL report for a single error.
        
        Args:
            error: Error dictionary
            
        Returns:
            JSONL formatted error string
        """
        error_line = {
            "type": "error",
            "file_path": error.get('file_path', ''),
            "line": error.get('line', 0),
            "column": error.get('column', 0),
            "rule": error.get('rule', 'unknown'),
            "message": error.get('message', 'Unknown error'),
            "severity": error.get('severity', 'error'),
            "path": error.get('path', ''),
            "context": error.get('context', '')
        }
        
        return json.dumps(error_line)
    
    def report_summary(self, results: List[ValidationResult]) -> str:
        """
        Generate a summary-only JSONL report.
        
        Args:
            results: List of validation results
            
        Returns:
            JSONL formatted summary string
        """
        summary = self._get_summary(results)
        
        summary_line = {
            "type": "summary",
            "files": summary['files'],
            "errors": summary['errors'],
            "warnings": summary['warnings'],
            "info": summary['info'],
            "success": summary['success'],
            "total_issues": summary['errors'] + summary['warnings'] + summary['info']
        }
        
        return json.dumps(summary_line)
    
    def report_compact(self, results: List[ValidationResult]) -> str:
        """
        Generate a compact JSONL report with minimal information.
        
        Args:
            results: List of validation results
            
        Returns:
            Compact JSONL formatted report string
        """
        if not results:
            return ""
        
        lines = []
        
        # Add only files with issues
        for result in results:
            if result.get('errors') or result.get('warnings') or result.get('info'):
                compact_line = {
                    "file": result.get('file_path', 'unknown'),
                    "errors": len(result.get('errors', [])),
                    "warnings": len(result.get('warnings', [])),
                    "info": len(result.get('info', [])),
                    "success": result.get('success', True)
                }
                lines.append(json.dumps(compact_line))
        
        return "\n".join(lines)
    
    def report_detailed(self, results: List[ValidationResult]) -> str:
        """
        Generate a detailed JSONL report with full error information.
        
        Args:
            results: List of validation results
            
        Returns:
            Detailed JSONL formatted report string
        """
        if not results:
            return ""
        
        lines = []
        
        # Add summary
        summary = self._get_summary(results)
        summary_line = {
            "type": "summary",
            "files": summary['files'],
            "errors": summary['errors'],
            "warnings": summary['warnings'],
            "info": summary['info'],
            "success": summary['success'],
            "total_issues": summary['errors'] + summary['warnings'] + summary['info']
        }
        lines.append(json.dumps(summary_line))
        
        # Add detailed file results
        for result in results:
            if result.get('errors') or result.get('warnings') or result.get('info'):
                # Add file header
                file_header = {
                    "type": "file_header",
                    "file_path": result.file_path,
                    "success": result.success,
                    "duration": result.duration
                }
                lines.append(json.dumps(file_header))
                
                # Add individual errors
                for error in result.get('errors', []):
                    error_line = {
                        "type": "error",
                        "file_path": result.get('file_path', 'unknown'),
                        "line": error.get('line', 0),
                        "column": error.get('column', 0),
                        "rule": error.get('rule', 'unknown'),
                        "message": error.get('message', 'Unknown error'),
                        "severity": "error",
                        "path": error.get('path', ''),
                        "context": error.get('context', '')
                    }
                    lines.append(json.dumps(error_line))
                
                # Add individual warnings
                for warning in result.warnings:
                    warning_line = {
                        "type": "warning",
                        "file_path": result.get('file_path', 'unknown'),
                        "line": warning.get('line', 0),
                        "column": warning.get('column', 0),
                        "rule": warning.get('rule', 'unknown'),
                        "message": warning.get('message', 'Unknown warning'),
                        "severity": "warning",
                        "path": warning.get('path', ''),
                        "context": warning.get('context', '')
                    }
                    lines.append(json.dumps(warning_line))
                
                # Add individual info messages
                for info in result.info:
                    info_line = {
                        "type": "info",
                        "file_path": result.get('file_path', 'unknown'),
                        "line": info.get('line', 0),
                        "column": info.get('column', 0),
                        "rule": info.get('rule', 'unknown'),
                        "message": info.get('message', 'Unknown info'),
                        "severity": "info",
                        "path": info.get('path', ''),
                        "context": info.get('context', '')
                    }
                    lines.append(json.dumps(info_line))
        
        return "\n".join(lines)
