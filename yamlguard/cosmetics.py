"""
YAML cosmetics linter for style and formatting issues.

Provides checks for trailing spaces, tab usage, BOM presence, duplicate keys,
and other YAML style issues that complement indentation checking.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


class CosmeticsError:
    """Represents a cosmetics error with detailed information."""
    
    def __init__(self, line: int, column: int, rule: str, message: str, 
                 severity: str = "warning", fix: Optional[str] = None):
        """
        Initialize a cosmetics error.
        
        Args:
            line: Line number (1-based)
            column: Column number (1-based)
            rule: Rule name that triggered the error
            message: Human-readable error message
            severity: Error severity (error, warning, info)
            fix: Suggested fix (optional)
        """
        self.line = line
        self.column = column
        self.rule = rule
        self.message = message
        self.severity = severity
        self.fix = fix
    
    def __repr__(self) -> str:
        return (f"CosmeticsError(line={self.line}, column={self.column}, "
                f"rule='{self.rule}', message='{self.message}')")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'type': 'cosmetics',
            'line': self.line,
            'column': self.column,
            'rule': self.rule,
            'message': self.message,
            'severity': self.severity,
            'fix': self.fix
        }


class CosmeticsChecker:
    """
    YAML cosmetics checker for style and formatting issues.
    
    Provides comprehensive style checking including trailing spaces, tab usage,
    BOM presence, duplicate keys, and line length validation.
    """
    
    def __init__(self, line_length: int = 120, strict: bool = False):
        """
        Initialize the cosmetics checker.
        
        Args:
            line_length: Maximum allowed line length
            strict: Whether to use strict mode (more warnings)
        """
        self.line_length = line_length
        self.strict = strict
        self.errors: List[CosmeticsError] = []
    
    def check_file(self, file_path: Union[str, Path]) -> List[CosmeticsError]:
        """
        Check cosmetics in a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            List of cosmetics errors found
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.check_content(content, str(file_path))
    
    def check_content(self, content: str, source: str = "<string>") -> List[CosmeticsError]:
        """
        Check cosmetics in YAML content.
        
        Args:
            content: YAML content as string
            source: Source identifier for error reporting
            
        Returns:
            List of cosmetics errors found
        """
        self.errors = []
        
        # Check line-by-line issues
        self._check_trailing_spaces(content, source)
        self._check_tabs(content, source)
        self._check_bom(content, source)
        self._check_line_length(content, source)
        
        # Check YAML structure issues
        self._check_duplicate_keys(content, source)
        self._check_quotes(content, source)
        self._check_booleans(content, source)
        
        return self.errors
    
    def _check_trailing_spaces(self, content: str, source: str) -> None:
        """Check for trailing spaces."""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            if line.endswith(' ') or line.endswith('\t'):
                # Find the last non-whitespace character
                stripped = line.rstrip()
                if stripped:  # Don't flag empty lines
                    column = len(stripped) + 1
                    self._add_error(
                        i, column, 'trailing-spaces',
                        f"Trailing spaces found at end of line",
                        "warning",
                        stripped
                    )
    
    def _check_tabs(self, content: str, source: str) -> None:
        """Check for tab usage."""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            if '\t' in line:
                # Find first tab
                tab_pos = line.find('\t') + 1
                self._add_error(
                    i, tab_pos, 'tabs',
                    f"Tab character found (use spaces instead)",
                    "error",
                    line.replace('\t', '    ')  # Replace tabs with 4 spaces
                )
    
    def _check_bom(self, content: str, source: str) -> None:
        """Check for BOM (Byte Order Mark) presence."""
        if content.startswith('\ufeff'):
            self._add_error(
                1, 1, 'bom',
                "BOM (Byte Order Mark) found at beginning of file",
                "warning",
                content[1:]  # Remove BOM
            )
    
    def _check_line_length(self, content: str, source: str) -> None:
        """Check for overly long lines."""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            if len(line) > self.line_length:
                self._add_error(
                    i, self.line_length + 1, 'line-length',
                    f"Line too long ({len(line)} characters, max {self.line_length})",
                    "warning"
                )
    
    def _check_duplicate_keys(self, content: str, source: str) -> None:
        """Check for duplicate keys in YAML."""
        try:
            yaml = YAML()
            yaml.allow_duplicate_keys = True  # Allow parsing with duplicates
            
            # Parse and check for duplicates
            data = yaml.load(content)
            self._find_duplicate_keys(data, [], source)
            
        except Exception:
            # If parsing fails, skip duplicate key checking
            pass
    
    def _find_duplicate_keys(self, obj: Any, path: List[str], source: str) -> None:
        """Recursively find duplicate keys in YAML structure."""
        if isinstance(obj, CommentedMap):
            seen_keys: Set[str] = set()
            
            for key, value in obj.items():
                key_str = str(key)
                if key_str in seen_keys:
                    # Found duplicate key
                    self._add_error(
                        1, 1, 'duplicate-key',
                        f"Duplicate key '{key_str}' found at path {'.'.join(path)}",
                        "error"
                    )
                else:
                    seen_keys.add(key_str)
                
                # Recursively check nested structures
                self._find_duplicate_keys(value, path + [key_str], source)
                
        elif isinstance(obj, CommentedSeq):
            for i, item in enumerate(obj):
                self._find_duplicate_keys(item, path + [f"[{i}]"], source)
    
    def _check_quotes(self, content: str, source: str) -> None:
        """Check for inconsistent quote usage."""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Check for mixed quotes in the same line
            if "'" in line and '"' in line:
                # Look for potential string values
                if ':' in line:
                    key, value = line.split(':', 1)
                    if value.strip().startswith(("'", '"')):
                        self._add_error(
                            i, 1, 'mixed-quotes',
                            "Mixed quote usage found in same line",
                            "info"
                        )
    
    def _check_booleans(self, content: str, source: str) -> None:
        """Check for inconsistent boolean representation."""
        lines = content.splitlines()
        
        # Common boolean patterns
        boolean_patterns = [
            (r'\btrue\b', 'true'),
            (r'\bfalse\b', 'false'),
            (r'\byes\b', 'yes'),
            (r'\bno\b', 'no'),
            (r'\bon\b', 'on'),
            (r'\boff\b', 'off'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, canonical in boolean_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's a value (after colon)
                    if ':' in line:
                        key, value = line.split(':', 1)
                        value = value.strip()
                        if re.match(pattern, value, re.IGNORECASE):
                            # Suggest canonical form
                            suggested = line.replace(value, canonical)
                            self._add_error(
                                i, 1, 'boolean-format',
                                f"Use canonical boolean format: {canonical}",
                                "info",
                                suggested
                            )
    
    def _add_error(self, line: int, column: int, rule: str, message: str,
                   severity: str, fix: Optional[str] = None) -> None:
        """Add a cosmetics error to the list."""
        error = CosmeticsError(
            line=line,
            column=column,
            rule=rule,
            message=message,
            severity=severity,
            fix=fix
        )
        self.errors.append(error)
    
    def fix_cosmetics(self, content: str) -> str:
        """
        Fix cosmetics issues in YAML content.
        
        Args:
            content: YAML content to fix
            
        Returns:
            Fixed YAML content
        """
        lines = content.splitlines()
        fixed_lines = []
        
        for line in lines:
            # Remove trailing spaces
            line = line.rstrip()
            
            # Replace tabs with spaces
            line = line.replace('\t', '    ')
            
            # Remove BOM from first line
            if line.startswith('\ufeff'):
                line = line[1:]
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def get_rule_documentation(self) -> Dict[str, str]:
        """Get documentation for all cosmetic rules."""
        return {
            'trailing-spaces': 'Remove trailing spaces at end of lines',
            'tabs': 'Replace tab characters with spaces',
            'bom': 'Remove Byte Order Mark from beginning of file',
            'line-length': f'Keep lines under {self.line_length} characters',
            'duplicate-key': 'Remove duplicate keys in mappings',
            'mixed-quotes': 'Use consistent quote style',
            'boolean-format': 'Use canonical boolean values (true/false)',
        }
