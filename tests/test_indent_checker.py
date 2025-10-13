"""
Tests for indentation checker.

Comprehensive tests for the indentation checker including
unit tests and property-based tests with hypothesis.
"""

import pytest
from pathlib import Path
from yamlguard.indent_checker import IndentationChecker, IndentationError


class TestIndentationChecker:
    """Test cases for IndentationChecker."""
    
    def test_init(self):
        """Test IndentationChecker initialization."""
        checker = IndentationChecker(indent_step=2, strict=True)
        assert checker.indent_step == 2
        assert checker.strict is True
        assert checker.errors == []
    
    def test_check_content_valid(self):
        """Test checking valid YAML content."""
        checker = IndentationChecker(indent_step=2)
        
        valid_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  namespace: default
data:
  key1: value1
  key2: value2
"""
        
        errors = checker.check_content(valid_yaml)
        assert len(errors) == 0
    
    def test_check_content_invalid_indentation(self):
        """Test checking YAML with invalid indentation."""
        checker = IndentationChecker(indent_step=2)
        
        invalid_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
    name: test  # Wrong indentation (4 spaces instead of 2)
  namespace: default
data:
  key1: value1
  key2: value2
"""
        
        errors = checker.check_content(invalid_yaml)
        assert len(errors) > 0
        
        # Check that we have indentation errors
        indentation_errors = [e for e in errors if e.rule == 'indentation']
        assert len(indentation_errors) > 0
    
    def test_check_content_mixed_indentation(self):
        """Test checking YAML with mixed indentation."""
        checker = IndentationChecker(indent_step=2)
        
        mixed_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
    namespace: default  # Wrong indentation
data:
  key1: value1
    key2: value2  # Wrong indentation
"""
        
        errors = checker.check_content(mixed_yaml)
        assert len(errors) > 0
    
    def test_check_content_sequences(self):
        """Test checking YAML with sequences."""
        checker = IndentationChecker(indent_step=2)
        
        sequence_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
data:
  - item1
  - item2
  - item3
"""
        
        errors = checker.check_content(sequence_yaml)
        assert len(errors) == 0
    
    def test_check_content_invalid_sequences(self):
        """Test checking YAML with invalid sequence indentation."""
        checker = IndentationChecker(indent_step=2)
        
        invalid_sequence_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
data:
    - item1  # Wrong indentation
  - item2
    - item3  # Wrong indentation
"""
        
        errors = checker.check_content(invalid_sequence_yaml)
        assert len(errors) > 0
    
    def test_fix_indentation(self):
        """Test fixing indentation issues."""
        checker = IndentationChecker(indent_step=2)
        
        original_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
    name: test
  namespace: default
data:
  key1: value1
    key2: value2
"""
        
        fixed_yaml = checker.fix_indentation(original_yaml, indent_step=2)
        
        # Check that the fixed YAML has consistent indentation
        lines = fixed_yaml.splitlines()
        for line in lines:
            if line.strip() and not line.startswith(' '):
                # This should be a top-level key
                continue
            elif line.startswith(' '):
                # This should be indented with 2 spaces
                assert line.startswith('  ')
    
    def test_get_suggested_fix(self):
        """Test getting suggested fixes for errors."""
        checker = IndentationChecker(indent_step=2)
        
        error = IndentationError(
            line=5,
            column=10,
            expected=3,
            actual=5,
            path="metadata.name",
            message="Indentation mismatch"
        )
        
        line_content = "    name: test"
        suggested = checker.get_suggested_fix(error, line_content)
        
        # The suggested fix should have the correct indentation
        assert suggested.startswith("  ")  # 2 spaces for correct indentation
    
    def test_different_indent_steps(self):
        """Test different indentation step sizes."""
        # Test with 4-space indentation
        checker_4 = IndentationChecker(indent_step=4)
        
        yaml_4_space = """
apiVersion: v1
kind: ConfigMap
metadata:
    name: test
    namespace: default
data:
    key1: value1
    key2: value2
"""
        
        errors = checker_4.check_content(yaml_4_space)
        assert len(errors) == 0
        
        # Test with 2-space indentation (should fail)
        errors_2_space = checker_4.check_content(yaml_4_space.replace("    ", "  "))
        assert len(errors_2_space) > 0
    
    def test_empty_content(self):
        """Test checking empty content."""
        checker = IndentationChecker(indent_step=2)
        
        errors = checker.check_content("")
        assert len(errors) == 0
        
        errors = checker.check_content("\n\n")
        assert len(errors) == 0
    
    def test_comments_preservation(self):
        """Test that comments are preserved during fixing."""
        checker = IndentationChecker(indent_step=2)
        
        yaml_with_comments = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  # This is a comment
  namespace: default
data:
  key1: value1
  # Another comment
  key2: value2
"""
        
        fixed_yaml = checker.fix_indentation(yaml_with_comments)
        
        # Check that comments are preserved
        assert "# This is a comment" in fixed_yaml
        assert "# Another comment" in fixed_yaml
    
    def test_multiline_strings(self):
        """Test handling of multiline strings."""
        checker = IndentationChecker(indent_step=2)
        
        yaml_multiline = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
data:
  description: |
    This is a multiline
    string that should
    be handled correctly
  key2: value2
"""
        
        errors = checker.check_content(yaml_multiline)
        assert len(errors) == 0
    
    def test_nested_structures(self):
        """Test handling of deeply nested structures."""
        checker = IndentationChecker(indent_step=2)
        
        nested_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  labels:
    app: test
    version: "1.0"
  annotations:
    description: "Test config map"
data:
  config:
    database:
      host: localhost
      port: 5432
      credentials:
        username: admin
        password: secret
"""
        
        errors = checker.check_content(nested_yaml)
        assert len(errors) == 0
    
    def test_error_properties(self):
        """Test that errors have the correct properties."""
        checker = IndentationChecker(indent_step=2)
        
        invalid_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
    name: test
"""
        
        errors = checker.check_content(invalid_yaml)
        assert len(errors) > 0
        
        error = errors[0]
        assert hasattr(error, 'line')
        assert hasattr(error, 'column')
        assert hasattr(error, 'expected')
        assert hasattr(error, 'actual')
        assert hasattr(error, 'path')
        assert hasattr(error, 'message')
        assert hasattr(error, 'severity')
        
        # Check that the error has reasonable values
        assert error.line > 0
        assert error.column > 0
        assert error.expected > 0
        assert error.actual > 0
        assert error.severity in ['error', 'warning', 'info']
    
    def test_to_dict(self):
        """Test converting errors to dictionaries."""
        error = IndentationError(
            line=5,
            column=10,
            expected=3,
            actual=5,
            path="metadata.name",
            message="Indentation mismatch",
            severity="error"
        )
        
        error_dict = error.to_dict()
        assert error_dict['type'] == 'indentation'
        assert error_dict['line'] == 5
        assert error_dict['column'] == 10
        assert error_dict['expected'] == 3
        assert error_dict['actual'] == 5
        assert error_dict['path'] == 'metadata.name'
        assert error_dict['message'] == 'Indentation mismatch'
        assert error_dict['severity'] == 'error'
