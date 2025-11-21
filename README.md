# YAMLGuard

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your friendly neighborhood YAML validator.** Because YAML indentation errors shouldn't ruin your day.

Ever spent hours debugging a Kubernetes deployment, only to discover it was a single space that broke everything? Or accidentally committed an API key because your YAML linter didn't catch it? We've been there too. That's why we built YAMLGuard.

YAMLGuard is a fast, accurate CLI tool that watches your back when working with YAML files. It catches indentation mistakes before they catch you, validates your Kubernetes manifests against official schemas, and scans for secrets that shouldn't be there. Think of it as a spell-checker for YAML, but one that actually understands what you're trying to do.

## Why YAMLGuard?

YAML is deceptively simple. Two spaces here, four spaces there—it all looks fine until it doesn't. And when it breaks, the error messages aren't always helpful. YAMLGuard changes that by giving you precise, actionable feedback exactly where problems occur.

But it's not just about indentation. Modern YAML files often contain sensitive information, Kubernetes configurations, and complex nested structures. YAMLGuard handles all of this, making it the one tool you need to keep your YAML files clean, secure, and valid.

## What Can It Do?

**Catch indentation errors before they catch you.** YAMLGuard uses tree-walking validation to understand your YAML structure, not just count spaces. It tells you exactly which line and column has the problem, and what it should be instead.

**Validate Kubernetes manifests like a pro.** Working with K8s? YAMLGuard validates your manifests against official Kubernetes schemas, so you know your deployments will actually work before you push them.

**Find secrets before they leak.** Accidentally committing credentials is a nightmare scenario. YAMLGuard scans for AWS keys, GitHub tokens, private keys, and other sensitive data using pattern matching and entropy analysis.

**Fix things automatically (when you want it to).** Not just a linter—YAMLGuard can actually fix indentation issues for you, safely preserving your comments and structure. **Important:** Always use `--backup` when fixing files in-place, especially for complex or large YAML files. Review the changes before committing.

**Play nice with your workflow.** Beautiful colored output for humans, JSON/JSONL formats for your CI/CD pipelines. It fits wherever you need it.

## Getting Started

Installation is straightforward—install from source:

```bash
git clone https://github.com/yamlguard/yamlguard.git
cd yamlguard
pip install -e .
```

This installs YAMLGuard in editable mode, so you can make changes and they'll be reflected immediately.

Once installed, you're ready to go. Let's walk through the basics.

### Basic Linting

Start simple—just point YAMLGuard at your YAML files:

```bash
# Check a directory of YAML files
yamlguard lint manifests/

# Check a single file
yamlguard lint config.yaml

# Want to auto-fix issues? Just add --fix
yamlguard lint manifests/ --fix

# Customize indentation (default is 2 spaces)
yamlguard lint manifests/ --indent 4
```

The output is clear and actionable. You'll see exactly what's wrong, where it's wrong, and how to fix it.

### Kubernetes Validation

If you're working with Kubernetes, YAMLGuard can validate your manifests against official schemas:

```bash
yamlguard kube-validate manifests/ --kube-version 1.30
```

This catches schema violations before they cause deployment failures. 

**⚠️ Current Limitations:** 

Kubernetes validation in v0.1.0 works well for core API resources (Deployments, Services, ConfigMaps, Secrets, etc.), but has some limitations:
- **CRD Support**: Custom Resource Definitions may not validate fully due to schema reference handling that's still being refined
- **Complex References**: Manifests with deeply nested or circular references may have validation gaps
- **Version Coverage**: Some Kubernetes versions may have incomplete schema coverage

**For production use, we recommend:**
- Using it as a first-pass validation alongside `kubectl --dry-run`
- Testing critical manifests in a staging environment
- Reporting any validation issues you encounter so we can improve coverage

We're continuously improving this feature and welcome feedback on edge cases you encounter.

### Secrets Scanning

This one could save you from a security incident. YAMLGuard scans for common secret patterns:

```bash
yamlguard scan-secrets manifests/
```

It detects AWS credentials, GitHub tokens, private keys, API keys (Slack, Twilio, JWT), and even high-entropy strings that might be secrets. You can adjust the sensitivity with the `--entropy` flag if you want to tune the detection.

**Understanding False Positives and False Negatives:**

Secret scanning uses pattern matching and entropy analysis, which means:
- **False Positives:** Some legitimate strings (like UUIDs, hashes, or random IDs) might trigger alerts. Review each finding carefully—not every match is a secret.
- **False Negatives:** Not all secret formats are covered. Custom or proprietary secret formats may not be detected. Always use this as part of a broader security strategy, not as the only defense.

**Best Practices:**
- Start with default settings and adjust `--entropy` based on your codebase
- Use custom rules (see Advanced Features) for team-specific patterns
- Review findings manually—automated tools are helpers, not replacements for security reviews
- Consider this a first line of defense alongside other security tools
- For high-security environments, combine with tools like `detect-secrets` or `gitleaks` (integrations coming soon)

## Configuration

YAMLGuard works great out of the box, but you can customize it to match your team's preferences. Create a `.yamlguard.yml` file in your project root:

```yaml
# Indentation settings
indent:
  step: 2              # How many spaces per indentation level
  strict: true         # Enforce consistent indentation
  fix: false           # Auto-fix by default? (you can override with --fix)

# Style checking
cosmetics:
  enabled: true
  trailing_spaces: true    # Complain about trailing whitespace
  tabs: true               # Complain about tabs (spaces are better)
  line_length: 120         # Maximum line length

# Kubernetes validation
kubernetes:
  enabled: false           # Enable for K8s projects
  version: "1.30"          # Which K8s version to validate against
  strict: false            # Strict mode catches more issues

# Secrets scanning
secrets:
  enabled: false           # Enable automatic secret scanning
  entropy_threshold: 4.5   # How sensitive should detection be?
  custom_rules: []         # Add your own patterns

# Output preferences
reporter:
  format: "stylish"        # stylish, json, or jsonl
  color: true              # Pretty colors (disable for CI)
  verbose: false           # More details when needed
```

## Command Reference

### `yamlguard lint`

The workhorse command. Lints YAML files for indentation and style issues.

```bash
yamlguard lint [paths...] [OPTIONS]

Options:
  -i, --indent INTEGER        Indentation step size [default: 2]
  --strict                    Enable strict mode
  --fix                       Auto-fix indentation issues
  -f, --format TEXT           Output format (stylish, json, jsonl) [default: stylish]
  --color / --no-color        Enable/disable colored output
  -v, --verbose               Verbose output
  -c, --config PATH           Configuration file path
```

### `yamlguard kube-validate`

Validates Kubernetes manifests against official schemas.

```bash
yamlguard kube-validate [paths...] [OPTIONS]

Options:
  -k, --kube-version TEXT     Kubernetes version [default: 1.30]
  --strict                    Enable strict validation mode
  -f, --format TEXT           Output format (stylish, json, jsonl) [default: stylish]
  --color / --no-color        Enable/disable colored output
  -v, --verbose               Verbose output
  -c, --config PATH           Configuration file path
```

### `yamlguard scan-secrets`

Scans YAML files for secrets and credentials.

```bash
yamlguard scan-secrets [paths...] [OPTIONS]

Options:
  -e, --entropy FLOAT         Entropy threshold for detection [default: 4.5]
  -f, --format TEXT           Output format (stylish, json, jsonl) [default: stylish]
  --color / --no-color        Enable/disable colored output
  -v, --verbose               Verbose output
  -c, --config PATH           Configuration file path
```

### `yamlguard fix`

Fixes indentation issues in YAML files. This preserves comments and structure, but **always use `--backup`** when modifying files in-place.

**⚠️ Safety First:**
- Auto-fixing is powerful but can be risky on complex or large YAML files
- Always create backups with `--backup` flag
- Review changes with `git diff` before committing
- Test fixed files to ensure they still work as expected
- Consider fixing files one at a time for critical configurations

```bash
yamlguard fix [paths...] [OPTIONS]

Options:
  -i, --indent INTEGER        Indentation step size [default: 2]
  --in-place                  Modify files in place
  --backup                    Create backup files (HIGHLY RECOMMENDED!)
  -c, --config PATH           Configuration file path
```

### `yamlguard init`

Quick setup for a new project. Creates a `.yamlguard.yml` file with sensible defaults.

```bash
yamlguard init [path] [OPTIONS]

Options:
  -i, --indent INTEGER         Default indentation step size [default: 2]
  -k, --kube-version TEXT     Default Kubernetes version [default: 1.30]
  -f, --format TEXT           Default output format [default: stylish]
```

## Real-World Examples

### The Daily Workflow

Most of the time, you'll just want to check your files:

```bash
# Quick check before committing
yamlguard lint .

# Found issues? Fix them automatically (with backup!)
yamlguard fix . --in-place --backup

# Always review changes before committing
git diff
```

### Kubernetes Projects

For Kubernetes work, validation is crucial:

```bash
# Validate all manifests
yamlguard kube-validate manifests/ --kube-version 1.30

# Combine with linting for comprehensive checks
yamlguard lint manifests/ && yamlguard kube-validate manifests/
```

### Security Audits

Before pushing to production, scan for secrets:

```bash
# Quick security check
yamlguard scan-secrets config/

# More sensitive detection
yamlguard scan-secrets config/ --entropy 4.0
```

### CI/CD Integration

YAMLGuard fits seamlessly into your pipelines. Here are ready-to-use configurations:

#### GitHub Actions

```yaml
# .github/workflows/yamlguard.yml
name: YAMLGuard Validation

on:
  pull_request:
    paths:
      - '**.yaml'
      - '**.yml'
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install YAMLGuard
        run: |
          pip install git+https://github.com/yamlguard/yamlguard.git
      
      - name: Lint YAML files
        run: yamlguard lint . --format json --no-color
      
      - name: Scan for secrets
        run: yamlguard scan-secrets . --format json --no-color
        continue-on-error: true  # Don't fail the build, but report findings
      
      - name: Validate Kubernetes manifests
        if: contains(github.event.head_commit.message, 'k8s') || contains(github.event.head_commit.message, 'kubernetes')
        run: yamlguard kube-validate manifests/ --format json --no-color
        continue-on-error: true  # K8s validation is still evolving
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - validate

yamlguard:
  stage: validate
  image: python:3.10
  before_script:
    - pip install git+https://github.com/yamlguard/yamlguard.git
  script:
    - yamlguard lint . --format json --no-color
    - yamlguard scan-secrets . --format json --no-color || true
  artifacts:
    when: always
    reports:
      junit: yamlguard-report.json
  only:
    changes:
      - "**/*.yaml"
      - "**/*.yml"
```

#### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('YAML Validation') {
            steps {
                sh 'pip install git+https://github.com/yamlguard/yamlguard.git'
                sh 'yamlguard lint . --format json --no-color'
                sh 'yamlguard scan-secrets . --format json --no-color || true'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'yamlguard-report.json', allowEmptyArchive: true
        }
    }
}
```

#### Command-Line Usage

For custom pipelines or local scripts:

```bash
# JSON output for programmatic handling
yamlguard lint manifests/ --format json --no-color

# JSONL for streaming/processing
yamlguard lint manifests/ --format jsonl --no-color

# Exit codes work for gating (exit 0 = success, exit 1 = errors found)
yamlguard lint manifests/ && echo "✅ All checks passed"
```

## What the Output Looks Like

### Stylish Format (Default)

When you run YAMLGuard, you get clear, colorful output that's easy to read:

```
🔍 YAMLGuard Validation Results
❌ 3 error(s)

📄 manifests/deployment.yaml
  ❌ 5:10  indentation  Indentation mismatch: expected 3, found 5
  ⚠️  8:15  trailing-spaces  Trailing spaces found at end of line

📄 manifests/service.yaml
  ✅ No issues found

==================================================
Files: 2 (1 passed)
Errors: 1
Warnings: 1
Info: 0

❌ Validation failed
```

### JSON Format

For CI/CD pipelines, JSON output gives you structured data:

```json
{
  "files": 2,
  "errors": 1,
  "warnings": 1,
  "info": 0,
  "success": 1
}
```

### JSONL Format

JSONL (JSON Lines) is perfect for streaming and processing:

```jsonl
{"type": "summary", "files": 2, "errors": 1, "warnings": 1, "info": 0, "success": 1}
{"type": "file", "file_path": "manifests/deployment.yaml", "success": false, "errors": [{"line": 5, "column": 10, "rule": "indentation", "message": "Indentation mismatch: expected 3, found 5", "severity": "error"}]}
```

## Advanced Features

### Custom Secret Detection

You can add your own patterns for secret detection. Maybe your team has a specific format for API keys? No problem:

```yaml
# .yamlguard.yml
secrets:
  custom_rules:
    - name: "custom-api-key"
      pattern: "api_key_[a-zA-Z0-9]{32}"
      confidence: 0.8
      context_keys: ["api", "key"]
```

### Pre-commit Integration

Catch issues before they even make it to your repository. Add YAMLGuard to your pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/hack-monk/yamlguard
    rev: v0.1.0
    hooks:
      - id: yamlguard-lint
        args: [--indent, 2, --strict]
      - id: yamlguard-kube-validate
        args: [--kube-version, 1.30]
      - id: yamlguard-scan-secrets
        args: [--entropy, 4.5]
```

Now every commit is automatically checked. No more "oops, forgot to lint" moments.

## Current Status & Maturity

YAMLGuard v0.1.0 is ready for real-world use. Core indentation, style checks, and secret scanning are stable, and Kubernetes validation is under active improvement. Here's what you should know:

### ✅ Stable Features

These features are stable and ready for production use:
- **Indentation Detection**: Precise tree-walking validation with exact line/column reporting
- **Style Checking**: Trailing spaces, tabs, line length, boolean format, duplicate keys
- **Secrets Scanning**: Pattern-based detection for common secrets (AWS, GitHub, private keys, API keys)
- **Auto-fix**: Safe indentation normalization that preserves comments
- **CLI Output**: Beautiful colored output with multiple format options (stylish, JSON, JSONL)
- **Configuration**: Flexible YAML-based configuration system

### 🚧 Features in Active Development

These features work but have known limitations:

**Kubernetes Validation:**
- ✅ Core API resources (Deployments, Services, ConfigMaps, etc.) validate correctly
- ⚠️ Custom Resource Definitions (CRDs) may not validate fully—schema reference handling is being refined
- ⚠️ Complex manifests with deeply nested references may have validation gaps
- ⚠️ Some Kubernetes versions may have incomplete schema coverage
- 💡 **Recommendation**: Use alongside `kubectl --dry-run` for critical deployments

**Advanced Secret Detection:**
- Integration with external tools (detect-secrets, gitleaks) is planned for future releases

### 📊 Test Coverage

- 20+ sample files covering edge cases
- 500+ issues detected across all categories
- Complex nested structures handled correctly
- Auto-fix functionality verified
- CI/CD integration tested and ready

### 🎯 Recommended Use Cases

**Great for:**
- Development workflows and pre-commit hooks
- CI/CD pipelines for catching issues early
- Local development and code reviews
- Teams standardizing YAML formatting
- Security scanning as part of a broader strategy

**Use with caution for:**
- Critical production deployments (always validate with `kubectl --dry-run` as well)
- Large-scale automated fixes (test on a subset first)
- As the sole security tool (combine with other security practices)

### 🐛 Reporting Issues

Found a bug? Encountered an edge case? We'd love to hear about it! Open an issue on GitHub with:
- The YAML file (or a minimal example)
- The command you ran
- Expected vs. actual behavior

Your feedback helps us improve faster.

## Performance

YAMLGuard is fast. We use `ruamel.yaml` for efficient parsing, implement smart caching for Kubernetes schemas, and keep dependencies minimal. It's designed to run quickly even on large codebases, so it won't slow down your workflow.

## Security & Privacy

Since YAMLGuard deals with sensitive information (secrets scanning, config validation), here's what you should know:

- **Local Processing**: YAMLGuard runs entirely locally and does not send your YAML files or secrets to any external service. All processing happens on your machine.

- **Secret Detection**: Secret detection is best-effort and rule-based. It should complement, not replace, other security controls (e.g., repository-wide secret scanners, pre-commit hooks, or dedicated security tools).

- **Tuning for Your Environment**: For highly sensitive environments, consider:
  - Adjusting `entropy_threshold` to reduce false positives or catch more potential secrets
  - Adding `custom_rules` that match your internal key formats and naming conventions
  - Using it as part of a layered security approach alongside other tools

- **No Data Collection**: YAMLGuard does not collect, store, or transmit any data about your files or findings.

## Contributing

We'd love your help! Whether it's bug reports, feature ideas, or code contributions, everything is welcome.

**Getting Started:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests (we love tests!)
5. Submit a pull request

**For Contributors:**

Getting started with the codebase is straightforward:
- **Architecture overview**: See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed overview of the system design
- **How to run tests**: See [TESTING.md](TESTING.md) for testing guidelines and examples
- **Sample files and edge cases**: Check out `samples/` directory for test YAML files covering various scenarios
- **Test suite**: Tests are in the `tests/` directory, organized by feature

The codebase is modular—each component has a clear responsibility, making it easy to understand and extend.

**What We're Looking For:**
- Bug fixes and edge case handling
- Improvements to Kubernetes validation coverage
- Additional secret detection patterns
- Performance optimizations
- Documentation improvements
- Integration examples for other CI/CD systems

**Questions?** Open an issue and we'll help you get started!

## License

MIT License - see [LICENSE](LICENSE) file for details. Use it freely, modify it, share it. We're just happy if it helps you avoid YAML headaches.

## Changelog

### v0.1.0 (Initial Release)

The first release of YAMLGuard! This version includes:

- Precise indentation checking with tree-walking validation
- Kubernetes schema validation with version pinning
- Secrets scanning with regex patterns and entropy analysis
- Auto-fix mode for indentation normalization
- Rich CLI with multiple output formats
- Comprehensive configuration system
- CI/CD integration support

---

**Made with ❤️ for developers who just want their YAML to work.**

Questions? Issues? Ideas? Open an issue on GitHub or reach out.
