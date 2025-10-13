# YAMLGuard Testing Guide

This guide explains how to test YAMLGuard functionality using the sample files in the `samples/` directory.

## Quick Start

### 1. Install YAMLGuard

```bash
# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e .[dev,secrets,kube]
```

### 2. Run Basic Tests

```bash
# Test indentation
yamlguard lint samples/indentation/

# Test cosmetics
yamlguard lint samples/cosmetics/

# Test Kubernetes validation
yamlguard kube-validate samples/kubernetes/

# Test secrets scanning
yamlguard scan-secrets samples/secrets/

# Test all samples
yamlguard lint samples/
```

### 3. Run Comprehensive Tests

```bash
# Run the test script
python test_samples.py

# Or run the shell script
./run_tests.sh
```

## Sample Files Overview

### Indentation Samples (`samples/indentation/`)

- **`good.yaml`**: Perfect indentation (should pass)
- **`bad_indentation.yaml`**: Inconsistent indentation (should fail)
- **`mixed_tabs_spaces.yaml`**: Mixed tabs and spaces (should fail)
- **`sequence_indentation.yaml`**: Sequence indentation issues (should fail)

### Cosmetics Samples (`samples/cosmetics/`)

- **`trailing_spaces.yaml`**: Trailing spaces (should fail)
- **`duplicate_keys.yaml`**: Duplicate keys (should fail)
- **`long_lines.yaml`**: Overly long lines (should fail)
- **`mixed_quotes.yaml`**: Mixed quote usage (should fail)
- **`boolean_format.yaml`**: Non-canonical boolean values (should fail)

### Kubernetes Samples (`samples/kubernetes/`)

- **`valid_deployment.yaml`**: Valid Kubernetes deployment (should pass)
- **`invalid_deployment.yaml`**: Invalid deployment (should fail)
- **`multi_document.yaml`**: Multi-document YAML (should pass)
- **`invalid_types.yaml`**: Wrong data types (should fail)

### Secrets Samples (`samples/secrets/`)

- **`aws_credentials.yaml`**: AWS credentials (should detect secrets)
- **`github_tokens.yaml`**: GitHub tokens (should detect secrets)
- **`database_credentials.yaml`**: Database credentials (should detect secrets)
- **`private_keys.yaml`**: Private keys (should detect secrets)
- **`api_keys.yaml`**: API keys (should detect secrets)

### Complex Samples (`samples/complex/`)

- **`large_config.yaml`**: Large, complex configuration
- **`multi_document_complex.yaml`**: Multi-document with complex structures

## Testing Commands

### Basic Linting

```bash
# Lint with default settings
yamlguard lint samples/indentation/

# Lint with custom indentation
yamlguard lint samples/indentation/ --indent 4

# Lint with strict mode
yamlguard lint samples/indentation/ --strict

# Lint with verbose output
yamlguard lint samples/indentation/ --verbose
```

### Kubernetes Validation

```bash
# Validate against Kubernetes 1.30
yamlguard kube-validate samples/kubernetes/ --kube-version 1.30

# Validate with strict mode
yamlguard kube-validate samples/kubernetes/ --strict

# Validate using kubeconform
yamlguard kube-validate samples/kubernetes/ --kubeconform
```

### Secrets Scanning

```bash
# Scan with default settings
yamlguard scan-secrets samples/secrets/

# Scan with custom entropy threshold
yamlguard scan-secrets samples/secrets/ --entropy 4.0

# Scan using detect-secrets
yamlguard scan-secrets samples/secrets/ --detect-secrets

# Scan using gitleaks
yamlguard scan-secrets samples/secrets/ --gitleaks
```

### Auto-fix

```bash
# Fix indentation issues
yamlguard fix samples/indentation/bad_indentation.yaml --in-place

# Fix with backup
yamlguard fix samples/indentation/bad_indentation.yaml --in-place --backup

# Fix cosmetics issues
yamlguard fix samples/cosmetics/trailing_spaces.yaml --in-place
```

## Output Formats

### Stylish Output (Default)

```bash
yamlguard lint samples/indentation/ --format stylish
```

### JSON Output

```bash
yamlguard lint samples/indentation/ --format json
```

### JSONL Output

```bash
yamlguard lint samples/indentation/ --format jsonl
```

## Configuration Testing

### 1. Create Configuration

```bash
# Initialize configuration
yamlguard init

# Or create custom configuration
yamlguard init --indent 4 --kube-version 1.29 --format json
```

### 2. Test with Configuration

```bash
# Use configuration file
yamlguard lint samples/ --config .yamlguard.yml

# Override configuration
yamlguard lint samples/ --config .yamlguard.yml --indent 4
```

## Expected Results

### Indentation Tests

- **`good.yaml`**: Should pass with no errors
- **`bad_indentation.yaml`**: Should fail with indentation errors
- **`mixed_tabs_spaces.yaml`**: Should fail with tab usage errors
- **`sequence_indentation.yaml`**: Should fail with sequence indentation errors

### Cosmetics Tests

- **`trailing_spaces.yaml`**: Should fail with trailing spaces errors
- **`duplicate_keys.yaml`**: Should fail with duplicate key errors
- **`long_lines.yaml`**: Should fail with line length errors
- **`mixed_quotes.yaml`**: Should fail with mixed quotes errors
- **`boolean_format.yaml`**: Should fail with boolean format errors

### Kubernetes Tests

- **`valid_deployment.yaml`**: Should pass validation
- **`invalid_deployment.yaml`**: Should fail with schema validation errors
- **`multi_document.yaml`**: Should pass validation
- **`invalid_types.yaml`**: Should fail with type validation errors

### Secrets Tests

- **`aws_credentials.yaml`**: Should detect AWS credentials
- **`github_tokens.yaml`**: Should detect GitHub tokens
- **`database_credentials.yaml`**: Should detect database credentials
- **`private_keys.yaml`**: Should detect private keys
- **`api_keys.yaml`**: Should detect API keys

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure YAMLGuard is installed in development mode
2. **Missing Dependencies**: Install optional dependencies with `pip install -e .[secrets,kube]`
3. **Permission Errors**: Make sure test files are readable
4. **Configuration Errors**: Check `.yamlguard.yml` syntax

### Debug Mode

```bash
# Enable verbose output
yamlguard lint samples/ --verbose

# Enable debug logging
export YAMLGUARD_DEBUG=1
yamlguard lint samples/
```

### Performance Testing

```bash
# Test with large files
yamlguard lint samples/complex/large_config.yaml

# Test with multiple files
yamlguard lint samples/ --format json
```

## Advanced Testing

### Custom Rules

```yaml
# .yamlguard.yml
secrets:
  custom_rules:
    - name: "custom-api-key"
      pattern: "api_key_[a-zA-Z0-9]{32}"
      confidence: 0.8
      context_keys: ["api", "key"]
```

### Baseline Testing

```bash
# Create baseline
yamlguard scan-secrets samples/secrets/ --baseline .secrets.baseline

# Use baseline
yamlguard scan-secrets samples/secrets/ --baseline .secrets.baseline
```

### Integration Testing

```bash
# Test with pre-commit
pre-commit run yamlguard-lint

# Test with CI
yamlguard lint samples/ --format json --fail-on error
```

## Contributing

When adding new test cases:

1. Create sample files in appropriate directories
2. Update this testing guide
3. Add test cases to `test_samples.py`
4. Update the README with new examples

## Support

For issues with testing:

1. Check the logs for error messages
2. Verify file permissions
3. Ensure all dependencies are installed
4. Check configuration file syntax
5. Report issues on GitHub
