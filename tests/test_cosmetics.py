"""
Tests for cosmetics checker.

Comprehensive tests for the cosmetics checker including
unit tests for all cosmetic rules.
"""

import pytest
from yamlguard.cosmetics import CosmeticsChecker, CosmeticsError


class TestCosmeticsChecker:
    """Test cases for CosmeticsChecker."""
    
    def test_init(self):
        """Test CosmeticsChecker initialization."""
        checker = CosmeticsChecker(line_length=120, strict=False)
        assert checker.line_length == 120
        assert checker.strict is False
        assert checker.errors == []
    
    def test_trailing_spaces(self):
        """Test detection of trailing spaces."""
        checker = CosmeticsChecker()
        
        yaml_with_trailing = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test  
  namespace: default
data:
  key1: value1
  key2: value2
"""
        
        errors = checker.check_content(yaml_with_trailing)
        trailing_errors = [e for e in errors if e.rule == 'trailing-spaces']
        assert len(trailing_errors) > 0
    
    def test_tabs(self):
        """Test detection of tab characters."""
        checker = CosmeticsChecker()
        
        yaml_with_tabs = """
apiVersion: v1
kind: ConfigMap
metadata:
	name: test
	namespace: default
data:
	key1: value1
	key2: value2
"""
        
        errors = checker.check_content(yaml_with_tabs)
        tab_errors = [e for e in errors if e.rule == 'tabs']
        assert len(tab_errors) > 0
    
    def test_bom(self):
        """Test detection of BOM (Byte Order Mark)."""
        checker = CosmeticsChecker()
        
        yaml_with_bom = "\ufeffapiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test"
        
        errors = checker.check_content(yaml_with_bom)
        bom_errors = [e for e in errors if e.rule == 'bom']
        assert len(bom_errors) > 0
    
    def test_line_length(self):
        """Test detection of overly long lines."""
        checker = CosmeticsChecker(line_length=50)
        
        long_line = "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: " + "x" * 100
        
        errors = checker.check_content(long_line)
        length_errors = [e for e in errors if e.rule == 'line-length']
        assert len(length_errors) > 0
    
    def test_duplicate_keys(self):
        """Test detection of duplicate keys."""
        checker = CosmeticsChecker()
        
        yaml_with_duplicates = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  name: test2  # Duplicate key
data:
  key1: value1
  key1: value2  # Duplicate key
"""
        
        errors = checker.check_content(yaml_with_duplicates)
        duplicate_errors = [e for e in errors if e.rule == 'duplicate-key']
        assert len(duplicate_errors) > 0
    
    def test_mixed_quotes(self):
        """Test detection of mixed quote usage."""
        checker = CosmeticsChecker()
        
        yaml_with_mixed_quotes = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: "test"
  namespace: 'default'
data:
  key1: "value1"
  key2: 'value2'
"""
        
        errors = checker.check_content(yaml_with_mixed_quotes)
        quote_errors = [e for e in errors if e.rule == 'mixed-quotes']
        assert len(quote_errors) > 0
    
    def test_boolean_format(self):
        """Test detection of non-canonical boolean values."""
        checker = CosmeticsChecker()
        
        yaml_with_booleans = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
data:
  enabled: yes
  disabled: no
  active: on
  inactive: off
"""
        
        errors = checker.check_content(yaml_with_booleans)
        boolean_errors = [e for e in errors if e.rule == 'boolean-format']
        assert len(boolean_errors) > 0
    
    def test_fix_cosmetics(self):
        """Test fixing cosmetics issues."""
        checker = CosmeticsChecker()
        
        yaml_with_issues = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test  
  namespace: default
data:
	key1: value1
	key2: value2
"""
        
        fixed_yaml = checker.fix_cosmetics(yaml_with_issues)
        
        # Check that trailing spaces are removed
        assert not fixed_yaml.endswith('  ')
        
        # Check that tabs are replaced with spaces
        assert '\t' not in fixed_yaml
    
    def test_empty_content(self):
        """Test checking empty content."""
        checker = CosmeticsChecker()
        
        errors = checker.check_content("")
        assert len(errors) == 0
        
        errors = checker.check_content("\n\n")
        assert len(errors) == 0
    
    def test_valid_content(self):
        """Test checking valid YAML content."""
        checker = CosmeticsChecker()
        
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
    
    def test_error_properties(self):
        """Test that errors have the correct properties."""
        checker = CosmeticsChecker()
        
        yaml_with_issues = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test  
"""
        
        errors = checker.check_content(yaml_with_issues)
        assert len(errors) > 0
        
        error = errors[0]
        assert hasattr(error, 'line')
        assert hasattr(error, 'column')
        assert hasattr(error, 'rule')
        assert hasattr(error, 'message')
        assert hasattr(error, 'severity')
        assert hasattr(error, 'fix')
        
        # Check that the error has reasonable values
        assert error.line > 0
        assert error.column > 0
        assert error.rule in ['trailing-spaces', 'tabs', 'bom', 'line-length', 'duplicate-key', 'mixed-quotes', 'boolean-format']
        assert error.severity in ['error', 'warning', 'info']
    
    def test_to_dict(self):
        """Test converting errors to dictionaries."""
        error = CosmeticsError(
            line=5,
            column=10,
            rule='trailing-spaces',
            message='Trailing spaces found',
            severity='warning',
            fix='  name: test'
        )
        
        error_dict = error.to_dict()
        assert error_dict['type'] == 'cosmetics'
        assert error_dict['line'] == 5
        assert error_dict['column'] == 10
        assert error_dict['rule'] == 'trailing-spaces'
        assert error_dict['message'] == 'Trailing spaces found'
        assert error_dict['severity'] == 'warning'
        assert error_dict['fix'] == '  name: test'
    
    def test_get_rule_documentation(self):
        """Test getting rule documentation."""
        checker = CosmeticsChecker()
        
        docs = checker.get_rule_documentation()
        assert isinstance(docs, dict)
        assert 'trailing-spaces' in docs
        assert 'tabs' in docs
        assert 'bom' in docs
        assert 'line-length' in docs
        assert 'duplicate-key' in docs
        assert 'mixed-quotes' in docs
        assert 'boolean-format' in docs
    
    def test_different_line_lengths(self):
        """Test different line length limits."""
        checker_short = CosmeticsChecker(line_length=20)
        checker_long = CosmeticsChecker(line_length=200)
        
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  namespace: default
data:
  key1: value1
  key2: value2
"""
        
        errors_short = checker_short.check_content(yaml_content)
        errors_long = checker_long.check_content(yaml_content)
        
        # Short line length should produce more errors
        short_length_errors = [e for e in errors_short if e.rule == 'line-length']
        long_length_errors = [e for e in errors_long if e.rule == 'line-length']
        
        assert len(short_length_errors) >= len(long_length_errors)
    
    def test_strict_mode(self):
        """Test strict mode behavior."""
        checker_strict = CosmeticsChecker(strict=True)
        checker_normal = CosmeticsChecker(strict=False)
        
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  namespace: default
data:
  key1: value1
  key2: value2
"""
        
        errors_strict = checker_strict.check_content(yaml_content)
        errors_normal = checker_normal.check_content(yaml_content)
        
        # Strict mode should be more aggressive
        assert len(errors_strict) >= len(errors_normal)
    
    def test_context_preservation(self):
        """Test that context is preserved during fixing."""
        checker = CosmeticsChecker()
        
        yaml_with_context = """
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
        
        fixed_yaml = checker.fix_cosmetics(yaml_with_context)
        
        # Check that comments are preserved
        assert "# This is a comment" in fixed_yaml
        assert "# Another comment" in fixed_yaml
    
    def test_multiple_issues(self):
        """Test detection of multiple issues in the same file."""
        checker = CosmeticsChecker()
        
        yaml_with_multiple_issues = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test  
  namespace: default
data:
	key1: value1
	key2: value2
"""
        
        errors = checker.check_content(yaml_with_multiple_issues)
        
        # Should detect both trailing spaces and tabs
        trailing_errors = [e for e in errors if e.rule == 'trailing-spaces']
        tab_errors = [e for e in errors if e.rule == 'tabs']
        
        assert len(trailing_errors) > 0
        assert len(tab_errors) > 0
