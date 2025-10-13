"""
Indentation checker for YAML files.

Provides precise indentation validation with tree walking and detailed
error reporting including exact line/column positions and suggested fixes.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ruamel.yaml import YAML
from ruamel.yaml.tokens import Token


class IndentationError:
    """Represents an indentation error with detailed information."""
    
    def __init__(self, line: int, column: int, expected: int, actual: int, 
                 path: str, message: str, severity: str = "error"):
        """
        Initialize an indentation error.
        
        Args:
            line: Line number (1-based)
            column: Column number (1-based)
            expected: Expected indentation level
            actual: Actual indentation level
            path: YAML path to the error
            message: Human-readable error message
            severity: Error severity (error, warning, info)
        """
        self.line = line
        self.column = column
        self.expected = expected
        self.actual = actual
        self.path = path
        self.message = message
        self.severity = severity
    
    def __repr__(self) -> str:
        return (f"IndentationError(line={self.line}, column={self.column}, "
                f"expected={self.expected}, actual={self.actual}, path='{self.path}')")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'type': 'indentation',
            'line': self.line,
            'column': self.column,
            'expected': self.expected,
            'actual': self.actual,
            'path': self.path,
            'message': self.message,
            'severity': self.severity
        }


class IndentationChecker:
    """
    Core indentation checker with tree walking and validation rules.
    
    Analyzes YAML structure to detect indentation inconsistencies and
    provides detailed error reporting with suggested fixes.
    """
    
    def __init__(self, indent_step: int = 2, strict: bool = True):
        """
        Initialize the indentation checker.
        
        Args:
            indent_step: Number of spaces per indentation level
            strict: Whether to enforce strict indentation rules
        """
        self.indent_step = indent_step
        self.strict = strict
        self.errors: List[IndentationError] = []
        
    def check_file(self, file_path: Union[str, Path]) -> List[IndentationError]:
        """
        Check indentation in a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            List of indentation errors found
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.check_content(content, str(file_path))
    
    def check_content(self, content: str, source: str = "<string>") -> List[IndentationError]:
        """
        Check indentation in YAML content.
        
        Args:
            content: YAML content as string
            source: Source identifier for error reporting
            
        Returns:
            List of indentation errors found
        """
        self.errors = []
        
        try:
            # Parse with ruamel.yaml to get token-level information
            yaml = YAML()
            yaml.preserve_quotes = True
            
            # Parse to get tokens
            tokens = list(yaml.parse(content))
            
            # Analyze indentation
            self._analyze_tokens(tokens, content, source)
            
        except Exception as e:
            # If parsing fails, fall back to line-by-line analysis
            self._analyze_lines(content, source)
        
        return self.errors
    
    def _analyze_tokens(self, tokens: List[Token], content: str, source: str) -> None:
        """
        Analyze YAML tokens for indentation issues.
        
        Args:
            tokens: List of YAML tokens
            content: Original YAML content
            source: Source identifier
        """
        lines = content.splitlines()
        indent_stack = [0]  # Track expected indentation levels
        path_stack = []  # Track YAML path
        
        for token in tokens:
            if token.id == 'BLOCK_MAPPING_START':
                # Mapping start - expect keys at current level
                pass
            elif token.id == 'BLOCK_SEQUENCE_START':
                # Sequence start - expect items at current level
                pass
            elif token.id == 'BLOCK_ENTRY':
                # Sequence item marker (-)
                line_num = token.start_mark.line + 1
                col_num = token.start_mark.column + 1
                
                # Check if the dash is properly indented
                expected_col = indent_stack[-1] + 1
                actual_col = token.start_mark.column + 1
                
                if actual_col != expected_col:
                    self._add_error(
                        line_num, col_num, expected_col, actual_col,
                        '.'.join(path_stack) if path_stack else 'root',
                        f"Sequence item indentation mismatch: expected column {expected_col}, found {actual_col}",
                        source
                    )
                
                # Next item should be indented by indent_step
                indent_stack.append(indent_stack[-1] + self.indent_step)
                
            elif token.id == 'KEY':
                # Mapping key
                line_num = token.start_mark.line + 1
                col_num = token.start_mark.column + 1
                
                # Check key indentation
                expected_col = indent_stack[-1] + 1
                actual_col = token.start_mark.column + 1
                
                if actual_col != expected_col:
                    self._add_error(
                        line_num, col_num, expected_col, actual_col,
                        '.'.join(path_stack) if path_stack else 'root',
                        f"Key indentation mismatch: expected column {expected_col}, found {actual_col}",
                        source
                    )
                
                # Value should be indented by indent_step
                indent_stack.append(indent_stack[-1] + self.indent_step)
                
            elif token.id == 'VALUE':
                # Mapping value
                line_num = token.start_mark.line + 1
                col_num = token.start_mark.column + 1
                
                # Check value indentation
                expected_col = indent_stack[-1] + 1
                actual_col = token.start_mark.column + 1
                
                if actual_col != expected_col:
                    self._add_error(
                        line_num, col_num, expected_col, actual_col,
                        '.'.join(path_stack) if path_stack else 'root',
                        f"Value indentation mismatch: expected column {expected_col}, found {actual_col}",
                        source
                    )
                
            elif token.id in ['BLOCK_MAPPING_END', 'BLOCK_SEQUENCE_END']:
                # End of mapping or sequence - pop indent level
                if len(indent_stack) > 1:
                    indent_stack.pop()
    
    def _analyze_lines(self, content: str, source: str) -> None:
        """
        Fallback line-by-line indentation analysis.
        
        Args:
            content: YAML content
            source: Source identifier
        """
        lines = content.splitlines()
        indent_stack = [0]
        path_stack = []
        
        for i, line in enumerate(lines, 1):
            if not line.strip():  # Skip empty lines
                continue
            
            # Calculate actual indentation
            actual_indent = len(line) - len(line.lstrip())
            
            # Check for sequence items
            if line.strip().startswith('-'):
                # Sequence item
                expected_indent = indent_stack[-1]
                if actual_indent != expected_indent:
                    self._add_error(
                        i, actual_indent + 1, expected_indent + 1, actual_indent + 1,
                        '.'.join(path_stack) if path_stack else 'root',
                        f"Sequence item indentation mismatch: expected {expected_indent + 1}, found {actual_indent + 1}",
                        source
                    )
                
                # Next level should be indented by indent_step
                indent_stack.append(expected_indent + self.indent_step)
                
            elif ':' in line and not line.strip().startswith('#'):
                # Potential mapping key
                key_part = line.split(':')[0]
                if key_part.strip():
                    expected_indent = indent_stack[-1]
                    if actual_indent != expected_indent:
                        self._add_error(
                            i, actual_indent + 1, expected_indent + 1, actual_indent + 1,
                            '.'.join(path_stack) if path_stack else 'root',
                            f"Key indentation mismatch: expected {expected_indent + 1}, found {actual_indent + 1}",
                            source
                        )
                    
                    # Value should be indented by indent_step
                    indent_stack.append(expected_indent + self.indent_step)
            else:
                # Check if this line should be indented
                if actual_indent > 0 and actual_indent not in indent_stack:
                    # Find closest expected indentation
                    closest_expected = min(indent_stack, key=lambda x: abs(x - actual_indent))
                    if abs(actual_indent - closest_expected) > 0:
                        self._add_error(
                            i, actual_indent + 1, closest_expected + 1, actual_indent + 1,
                            '.'.join(path_stack) if path_stack else 'root',
                            f"Indentation mismatch: expected {closest_expected + 1}, found {actual_indent + 1}",
                            source
                        )
    
    def _add_error(self, line: int, column: int, expected: int, actual: int,
                   path: str, message: str, source: str) -> None:
        """Add an indentation error to the list."""
        error = IndentationError(
            line=line,
            column=column,
            expected=expected,
            actual=actual,
            path=path,
            message=message,
            severity="error"
        )
        self.errors.append(error)
    
    def fix_indentation(self, content: str, indent_step: Optional[int] = None) -> str:
        """
        Fix indentation issues in YAML content.
        
        Args:
            content: YAML content to fix
            indent_step: Override indent step (uses instance default if None)
            
        Returns:
            Fixed YAML content
        """
        if indent_step is None:
            indent_step = self.indent_step
        
        try:
            # Use ruamel.yaml to normalize indentation
            yaml = YAML()
            yaml.indent(mapping=indent_step, sequence=indent_step, offset=indent_step)
            yaml.preserve_quotes = True
            
            # Parse and re-emit to normalize indentation
            data = yaml.load(content)
            
            import io
            stream = io.StringIO()
            yaml.dump(data, stream)
            return stream.getvalue()
            
        except Exception:
            # If parsing fails, return original content
            return content
    
    def get_suggested_fix(self, error: IndentationError, line_content: str) -> str:
        """
        Get suggested fix for an indentation error.
        
        Args:
            error: The indentation error
            line_content: Content of the line with the error
            
        Returns:
            Suggested fixed line content
        """
        # Calculate the difference
        diff = error.expected - error.actual
        
        if diff > 0:
            # Need to add spaces
            spaces_to_add = ' ' * diff
            return spaces_to_add + line_content.lstrip()
        elif diff < 0:
            # Need to remove spaces
            spaces_to_remove = abs(diff)
            stripped = line_content.lstrip()
            return ' ' * (error.expected - 1) + stripped
        else:
            return line_content
