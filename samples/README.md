# YAMLGuard Test Samples

This directory contains sample YAML files to test YAMLGuard functionality. The files are organized by category and include both valid and invalid examples.

## File Categories

### 1. Indentation Issues (`indentation/`)
- Files with various indentation problems
- Mixed indentation (spaces and tabs)
- Inconsistent indentation levels
- Sequence item indentation issues

### 2. Cosmetics Issues (`cosmetics/`)
- Files with trailing spaces
- Files with tab characters
- Files with BOM (Byte Order Mark)
- Files with overly long lines
- Files with duplicate keys

### 3. Kubernetes Manifests (`kubernetes/`)
- Valid Kubernetes manifests
- Invalid Kubernetes manifests
- Multi-document YAML files
- CRD examples

### 4. Secrets Examples (`secrets/`)
- Files with hardcoded secrets
- Files with API keys
- Files with database credentials
- Files with private keys

### 5. Complex Examples (`complex/`)
- Large, complex YAML files
- Nested structures
- Multi-document files
- Edge cases

## Testing Commands

```bash
# Test indentation checking
yamlguard lint samples/indentation/

# Test cosmetics checking
yamlguard lint samples/cosmetics/

# Test Kubernetes validation
yamlguard kube-validate samples/kubernetes/

# Test secrets scanning
yamlguard scan-secrets samples/secrets/

# Test auto-fix
yamlguard fix samples/indentation/ --in-place

# Test all samples
yamlguard lint samples/
```

## Expected Results

Each sample file is designed to trigger specific validation rules. The expected results are documented in the individual file comments.
