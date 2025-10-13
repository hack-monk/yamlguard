"""
Base reporter class for YAMLGuard.

Provides abstract base class for all reporters and common functionality
for formatting validation results.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Represents a validation result with detailed information."""
    
    file_path: str = Field(..., description="Path to the validated file")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="List of warnings")
    info: List[Dict[str, Any]] = Field(default_factory=list, description="List of info messages")
    success: bool = Field(default=True, description="Whether validation was successful")
    duration: float = Field(default=0.0, description="Validation duration in seconds")


class Reporter(ABC):
    """
    Abstract base class for all reporters.
    
    Provides common functionality for formatting and outputting validation results
    in different formats (stylish, JSON, JSONL, etc.).
    """
    
    def __init__(self, color: bool = True, verbose: bool = False):
        """
        Initialize the reporter.
        
        Args:
            color: Whether to use colored output
            verbose: Whether to use verbose output
        """
        self.color = color
        self.verbose = verbose
    
    @abstractmethod
    def report(self, results: List[ValidationResult]) -> str:
        """
        Generate a report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Formatted report string
        """
        pass
    
    def report_file(self, file_path: Union[str, Path], errors: List[Dict[str, Any]]) -> str:
        """
        Generate a report for a single file.
        
        Args:
            file_path: Path to the file
            errors: List of errors for the file
            
        Returns:
            Formatted report string
        """
        # Categorize errors by severity
        categorized = self._categorize_errors(errors)
        
        result = ValidationResult(
            file_path=str(file_path),
            errors=categorized['errors'],
            warnings=categorized['warnings'],
            info=categorized['info'],
            success=len(categorized['errors']) == 0
        )
        
        return self.report([result])
    
    def _categorize_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize errors by severity.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Dictionary with categorized errors
        """
        categorized = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        for error in errors:
            severity = error.get('severity', 'error')
            if severity in categorized:
                categorized[severity].append(error)
            else:
                categorized['errors'].append(error)
        
        return categorized
    
    def _format_error(self, error: Dict[str, Any]) -> str:
        """
        Format a single error for display.
        
        Args:
            error: Error dictionary
            
        Returns:
            Formatted error string
        """
        line = error.get('line', 0)
        column = error.get('column', 0)
        message = error.get('message', 'Unknown error')
        rule = error.get('rule', 'unknown')
        
        if line > 0 and column > 0:
            return f"  {line}:{column}  {rule}  {message}"
        else:
            return f"  {rule}  {message}"
    
    def _get_severity_color(self, severity: str) -> str:
        """
        Get color code for severity level.
        
        Args:
            severity: Severity level
            
        Returns:
            Color code string
        """
        if not self.color:
            return ""
        
        colors = {
            'error': '\033[31m',    # Red
            'warning': '\033[33m',  # Yellow
            'info': '\033[36m',     # Cyan
        }
        
        return colors.get(severity, '')
    
    def _reset_color(self) -> str:
        """Get color reset code."""
        return '\033[0m' if self.color else ''
    
    def _get_summary(self, results: List[ValidationResult]) -> Dict[str, int]:
        """
        Get summary statistics for validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Summary statistics
        """
        summary = {
            'files': len(results),
            'errors': 0,
            'warnings': 0,
            'info': 0,
            'success': 0
        }
        
        for result in results:
            summary['errors'] += len(result.get('errors', []))
            summary['warnings'] += len(result.get('warnings', []))
            summary['info'] += len(result.get('info', []))
            if result.get('success', True):
                summary['success'] += 1
        
        return summary
