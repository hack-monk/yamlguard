# YAMLGuard Architecture

This document describes the architecture and design decisions for YAMLGuard, a comprehensive YAML validation and linting tool.

## Overview

YAMLGuard is designed as a modular, extensible system for validating YAML files with focus on:

1. **Precise Indentation Checking**: Tree-walking validation with exact line/column reporting
2. **Kubernetes Schema Validation**: Official OpenAPI/JSON Schema validation with version pinning
3. **Secrets Scanning**: Comprehensive secrets detection with regex patterns and entropy analysis
4. **Auto-fix Mode**: Safe indentation normalization while preserving comments
5. **Rich Output**: Beautiful CLI with colors and detailed error reporting
6. **CI/CD Ready**: Multiple output formats (JSON, JSONL) for pipeline integration

## Architecture Components

### 1. Core System (`yamlguard/core.py`)

The `YAMLGuard` class serves as the main interface, orchestrating all functionality:

- **File Processing**: Handles file discovery, parsing, and validation
- **Error Aggregation**: Combines results from different checkers
- **Configuration Management**: Applies user configuration to all components
- **Result Formatting**: Converts internal results to standardized format

### 2. Configuration System (`yamlguard/config.py`)

Pydantic-based configuration with validation:

- **IndentConfig**: Indentation settings (step, strict mode, auto-fix)
- **CosmeticsConfig**: Style checking (trailing spaces, tabs, line length)
- **KubernetesConfig**: K8s validation (version, strict mode, kubeconform)
- **SecretsConfig**: Secrets scanning (entropy, baselines, external tools)
- **ReporterConfig**: Output formatting (format, colors, verbosity)

### 3. YAML Loading (`yamlguard/loader.py`)

Dual-loader system for different use cases:

- **YAMLLoader**: ruamel.yaml-based loader with position tracking
- **SafeYAMLLoader**: PyYAML fallback for speed when comments aren't needed
- **Position Tracking**: Captures line/column information for precise error reporting

### 4. Indentation Engine (`yamlguard/indent_checker.py`)

Tree-walking indentation validation:

- **Token Analysis**: Uses ruamel.yaml tokens for precise position tracking
- **Rule Engine**: Configurable indentation rules (step size, strict mode)
- **Error Reporting**: Detailed error information with suggested fixes
- **Auto-fix**: Safe indentation normalization while preserving comments

### 5. Cosmetics Linter (`yamlguard/cosmetics.py`)

Style and formatting checks:

- **Trailing Spaces**: Detection and removal of trailing whitespace
- **Tab Usage**: Detection and conversion of tabs to spaces
- **BOM Detection**: Byte Order Mark detection and removal
- **Line Length**: Configurable line length limits
- **Duplicate Keys**: Detection of duplicate mapping keys
- **Quote Consistency**: Mixed quote usage detection
- **Boolean Format**: Canonical boolean value enforcement

### 6. Kubernetes Validator (`yamlguard/kube/`)

Comprehensive Kubernetes manifest validation:

- **Schema Management**: Downloads and caches Kubernetes OpenAPI schemas
- **Version Support**: Multiple Kubernetes version support
- **Dual Validation**: Python jsonschema + kubeconform integration
- **CRD Support**: Custom Resource Definition validation
- **Multi-document**: Support for YAML documents with multiple manifests

### 7. Secrets Scanner (`yamlguard/secrets/`)

Multi-engine secrets detection:

- **Rule Engine**: Curated regex patterns for common secrets
- **Entropy Analysis**: Shannon entropy calculation for unknown patterns
- **Context Awareness**: Confidence scoring based on surrounding context
- **External Integration**: detect-secrets and gitleaks adapters
- **Baseline Support**: Known secrets management

### 8. Reporter System (`yamlguard/reporters/`)

Multiple output formats for different use cases:

- **StylishReporter**: eslint/yamllint-like colored output
- **JSONLReporter**: Machine-readable JSON Lines format
- **BaseReporter**: Abstract base class for extensibility
- **Rich Integration**: Beautiful terminal output with colors and formatting

### 9. CLI Interface (`yamlguard/cli.py`)

Typer-based command-line interface:

- **Multiple Commands**: lint, kube-validate, scan-secrets, fix, init
- **Rich Options**: Comprehensive configuration via CLI flags
- **Configuration Integration**: Automatic config file discovery
- **Exit Codes**: Proper exit codes for CI/CD integration

## Design Principles

### 1. Modularity

Each component is designed as a separate module with clear interfaces:

- **Single Responsibility**: Each module has one clear purpose
- **Loose Coupling**: Modules interact through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Extensibility

The system is designed for easy extension:

- **Plugin Architecture**: Entry points for custom rules and validators
- **Configuration System**: Comprehensive configuration for all components
- **Reporter System**: Easy addition of new output formats
- **Rule Engine**: Pluggable rules for secrets detection

### 3. Performance

Optimized for speed and efficiency:

- **Parallel Processing**: Multi-threaded file scanning
- **Smart Caching**: Kubernetes schema caching
- **Minimal Dependencies**: Lightweight core with optional integrations
- **Streaming**: Support for large file processing

### 4. Accuracy

Precise error reporting and validation:

- **Position Tracking**: Exact line/column information for all errors
- **Context Preservation**: Maintains YAML structure and comments
- **Schema Validation**: Official Kubernetes schema validation
- **False Positive Reduction**: Context-aware secrets detection

## Data Flow

### 1. File Discovery

```
User Input → Path Resolution → File Filtering → YAML File List
```

### 2. Validation Pipeline

```
YAML File → Parser → Indentation Checker → Cosmetics Checker → K8s Validator → Secrets Scanner → Results
```

### 3. Error Aggregation

```
Individual Errors → Categorization → Severity Assignment → Result Objects
```

### 4. Report Generation

```
Result Objects → Reporter Selection → Formatting → Output
```

## Configuration Hierarchy

1. **Default Values**: Built-in sensible defaults
2. **Configuration File**: `.yamlguard.yml` in project root
3. **CLI Arguments**: Command-line overrides
4. **Environment Variables**: Runtime configuration

## Error Handling

### 1. Graceful Degradation

- **Parser Failures**: Fall back to line-by-line analysis
- **Schema Download**: Continue without K8s validation if schemas unavailable
- **External Tools**: Skip if kubeconform/gitleaks not available

### 2. Error Reporting

- **Detailed Information**: Line, column, rule, message, severity
- **Context Preservation**: Surrounding code for better understanding
- **Suggested Fixes**: Auto-fix recommendations where possible

### 3. Exit Codes

- **0**: Success (no errors)
- **1**: Errors found
- **2**: Configuration errors
- **3**: System errors

## Testing Strategy

### 1. Unit Tests

- **Individual Components**: Each module tested in isolation
- **Mocking**: External dependencies mocked for reliable testing
- **Edge Cases**: Boundary conditions and error scenarios

### 2. Integration Tests

- **End-to-End**: Complete validation pipeline testing
- **Configuration**: Different configuration scenarios
- **File Types**: Various YAML file structures

### 3. Property-Based Tests

- **Hypothesis**: Property-based testing for YAML fuzzing
- **Random Generation**: Automatic test case generation
- **Invariant Testing**: System invariants under random inputs

## Future Extensions

### 1. Plugin System

- **Custom Rules**: User-defined validation rules
- **External Validators**: Integration with other validation tools
- **Custom Reporters**: User-defined output formats

### 2. Advanced Features

- **Helm Support**: Helm chart validation
- **Ansible Support**: Ansible playbook validation
- **GitHub Actions**: GitHub Actions workflow validation
- **Policy Engine**: OPA/Rego policy validation

### 3. Performance Improvements

- **Parallel Processing**: Multi-threaded validation
- **Incremental Validation**: Only validate changed files
- **Caching**: Intelligent caching of validation results
- **Streaming**: Large file streaming support

## Security Considerations

### 1. Secrets Handling

- **No Storage**: Secrets are not stored or logged
- **Baseline Support**: Known secrets management
- **False Positive Reduction**: Context-aware detection
- **Audit Trail**: Comprehensive logging of detection rules

### 2. Input Validation

- **File Size Limits**: Protection against large file attacks
- **Path Traversal**: Prevention of directory traversal attacks
- **Content Validation**: YAML structure validation before processing

### 3. External Tool Integration

- **Sandboxing**: External tools run in controlled environment
- **Timeout Protection**: Prevents hanging on external tool calls
- **Error Isolation**: External tool failures don't crash the system

## Conclusion

YAMLGuard is designed as a comprehensive, modular, and extensible system for YAML validation. The architecture supports the core requirements of precise indentation checking, Kubernetes validation, and secrets scanning while providing a foundation for future extensions and improvements.

The system prioritizes accuracy, performance, and usability while maintaining security and reliability. The modular design allows for easy extension and customization while the comprehensive configuration system provides flexibility for different use cases.
