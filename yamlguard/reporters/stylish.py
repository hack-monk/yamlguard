"""
Stylish reporter for YAMLGuard.

Provides eslint/yamllint-like output formatting with colors and detailed
error information including line numbers and context.
"""

from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from yamlguard.reporters.base import Reporter, ValidationResult


class StylishReporter(Reporter):
    """
    Stylish reporter with eslint/yamllint-like output.
    
    Provides colored, formatted output similar to eslint and yamllint
    with detailed error information and context.
    """
    
    def __init__(self, color: bool = True, verbose: bool = False):
        """
        Initialize the stylish reporter.
        
        Args:
            color: Whether to use colored output
            verbose: Whether to use verbose output
        """
        super().__init__(color, verbose)
        self.console = Console(force_terminal=color)
    
    def report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a stylish report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Formatted report string
        """
        if not results:
            return "No files to validate.\n"
        
        # Get summary statistics
        summary = self._get_summary_dict(results)
        
        # Generate report content
        report_lines = []
        
        # Add header
        report_lines.append(self._format_header(summary))
        
        # Add file results
        for result in results:
            if result.get('errors') or result.get('warnings') or result.get('info'):
                report_lines.append(self._format_file_result(result))
        
        # Add summary
        report_lines.append(self._format_summary(summary))
        
        return "\n".join(report_lines)
    
    def _format_header(self, summary: dict) -> str:
        """Format the report header."""
        if summary['errors'] > 0:
            status = f"❌ {summary['errors']} error(s)"
            color = "red"
        elif summary['warnings'] > 0:
            status = f"⚠️  {summary['warnings']} warning(s)"
            color = "yellow"
        else:
            status = "✅ No issues found"
            color = "green"
        
        return f"\n🔍 YAMLGuard Validation Results\n{status}\n"
    
    def _get_summary_dict(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary statistics for validation results (dictionary format)."""
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
    
    def _format_file_result(self, result: Dict[str, Any]) -> str:
        """Format a single file result."""
        lines = []
        
        # File header
        file_path = result.get('file_path', 'unknown')
        lines.append(f"\n📄 {file_path}")
        
        # Add errors
        for error in result.get('errors', []):
            lines.append(self._format_error_line(error, "error"))
        
        # Add warnings
        for warning in result.get('warnings', []):
            lines.append(self._format_error_line(warning, "warning"))
        
        # Add info messages
        for info in result.get('info', []):
            lines.append(self._format_error_line(info, "info"))
        
        return "\n".join(lines)
    
    def _format_error_line(self, error: dict, severity: str) -> str:
        """Format a single error line."""
        line = error.get('line', 0)
        column = error.get('column', 0)
        message = error.get('message', 'Unknown error')
        rule = error.get('rule', 'unknown')
        
        # Severity indicator
        if severity == "error":
            indicator = "❌"
        elif severity == "warning":
            indicator = "⚠️ "
        else:
            indicator = "ℹ️ "
        
        # Position information
        if line > 0 and column > 0:
            position = f"{line}:{column}"
        else:
            position = "0:0"
        
        # Format the line
        formatted_line = f"  {indicator} {position}  {rule}  {message}"
        
        # Add context if available
        context = error.get('context', '')
        if context and self.verbose:
            formatted_line += f"\n    {context}"
        
        return formatted_line
    
    def _format_summary(self, summary: dict) -> str:
        """Format the summary section."""
        lines = []
        lines.append("\n" + "="*50)
        
        # Files summary
        files_text = f"Files: {summary['files']}"
        if summary['success'] > 0:
            files_text += f" ({summary['success']} passed)"
        lines.append(files_text)
        
        # Issues summary
        if summary['errors'] > 0:
            lines.append(f"Errors: {summary['errors']}")
        if summary['warnings'] > 0:
            lines.append(f"Warnings: {summary['warnings']}")
        if summary['info'] > 0:
            lines.append(f"Info: {summary['info']}")
        
        # Overall status
        if summary['errors'] > 0:
            lines.append("\n❌ Validation failed")
        elif summary['warnings'] > 0:
            lines.append("\n⚠️  Validation passed with warnings")
        else:
            lines.append("\n✅ Validation passed")
        
        return "\n".join(lines)
    
    def report_with_rich(self, results: List[ValidationResult]) -> None:
        """
        Generate a rich-formatted report using Rich library.
        
        Args:
            results: List of validation results
        """
        if not results:
            self.console.print("No files to validate.")
            return
        
        # Get summary statistics
        summary = self._get_summary_dict(results)
        
        # Create summary table
        table = Table(title="YAMLGuard Validation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Files", str(summary['files']))
        table.add_row("Errors", str(summary['errors']), style="red" if summary['errors'] > 0 else "green")
        table.add_row("Warnings", str(summary['warnings']), style="yellow" if summary['warnings'] > 0 else "green")
        table.add_row("Info", str(summary['info']), style="blue")
        table.add_row("Success", str(summary['success']), style="green")
        
        self.console.print(table)
        
        # Add file details
        for result in results:
            if result.get('errors') or result.get('warnings') or result.get('info'):
                self._print_file_result_rich(result)
    
    def _print_file_result_rich(self, result: ValidationResult) -> None:
        """Print a single file result using Rich."""
        # File header
        self.console.print(f"\n[bold blue]📄 {result.get('file_path', 'unknown')}[/bold blue]")
        
        # Add errors
        for error in result.get('errors', []):
            self._print_error_rich(error, "error")
        
        # Add warnings
        for warning in result.get('warnings', []):
            self._print_error_rich(warning, "warning")
        
        # Add info messages
        for info in result.get('info', []):
            self._print_error_rich(info, "info")
    
    def _print_error_rich(self, error: dict, severity: str) -> None:
        """Print a single error using Rich."""
        line = error.get('line', 0)
        column = error.get('column', 0)
        message = error.get('message', 'Unknown error')
        rule = error.get('rule', 'unknown')
        
        # Severity indicator
        if severity == "error":
            indicator = "❌"
            style = "red"
        elif severity == "warning":
            indicator = "⚠️ "
            style = "yellow"
        else:
            indicator = "ℹ️ "
            style = "blue"
        
        # Position information
        if line > 0 and column > 0:
            position = f"{line}:{column}"
        else:
            position = "0:0"
        
        # Format the line
        text = Text()
        text.append(f"  {indicator} ", style=style)
        text.append(f"{position}  ", style="dim")
        text.append(f"{rule}  ", style="bold")
        text.append(message, style=style)
        
        self.console.print(text)
        
        # Add context if available
        context = error.get('context', '')
        if context and self.verbose:
            self.console.print(f"    {context}", style="dim")
