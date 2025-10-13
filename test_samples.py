#!/usr/bin/env python3
"""
Test script for YAMLGuard samples.

This script demonstrates YAMLGuard functionality using the sample files
in the samples/ directory.
"""

import sys
from pathlib import Path

# Add the yamlguard package to the path
sys.path.insert(0, str(Path(__file__).parent))

from yamlguard import YAMLGuard, Config
from yamlguard.reporters import StylishReporter


def test_indentation_samples():
    """Test indentation samples."""
    print("🔍 Testing Indentation Samples")
    print("=" * 50)
    
    config = Config()
    config.indent.step = 2
    config.cosmetics.enabled = True
    
    yamlguard = YAMLGuard(config=config)
    reporter = StylishReporter(color=True, verbose=True)
    
    # Test good indentation
    print("\n📄 Testing good indentation...")
    results = yamlguard.lint_files([Path("samples/indentation/good.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test bad indentation
    print("\n📄 Testing bad indentation...")
    results = yamlguard.lint_files([Path("samples/indentation/bad_indentation.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test mixed tabs and spaces
    print("\n📄 Testing mixed tabs and spaces...")
    results = yamlguard.lint_files([Path("samples/indentation/mixed_tabs_spaces.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test sequence indentation
    print("\n📄 Testing sequence indentation...")
    results = yamlguard.lint_files([Path("samples/indentation/sequence_indentation.yaml")])
    report = reporter.report(results)
    print(report)


def test_cosmetics_samples():
    """Test cosmetics samples."""
    print("\n🎨 Testing Cosmetics Samples")
    print("=" * 50)
    
    config = Config()
    config.cosmetics.enabled = True
    config.cosmetics.line_length = 100  # Lower limit for testing
    
    yamlguard = YAMLGuard(config=config)
    reporter = StylishReporter(color=True, verbose=True)
    
    # Test trailing spaces
    print("\n📄 Testing trailing spaces...")
    results = yamlguard.lint_files([Path("samples/cosmetics/trailing_spaces.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test duplicate keys
    print("\n📄 Testing duplicate keys...")
    results = yamlguard.lint_files([Path("samples/cosmetics/duplicate_keys.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test long lines
    print("\n📄 Testing long lines...")
    results = yamlguard.lint_files([Path("samples/cosmetics/long_lines.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test mixed quotes
    print("\n📄 Testing mixed quotes...")
    results = yamlguard.lint_files([Path("samples/cosmetics/mixed_quotes.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test boolean format
    print("\n📄 Testing boolean format...")
    results = yamlguard.lint_files([Path("samples/cosmetics/boolean_format.yaml")])
    report = reporter.report(results)
    print(report)


def test_kubernetes_samples():
    """Test Kubernetes samples."""
    print("\n🚀 Testing Kubernetes Samples")
    print("=" * 50)
    
    config = Config()
    config.kubernetes.enabled = True
    config.kubernetes.version = "1.30"
    config.kubernetes.strict = False
    
    yamlguard = YAMLGuard(config=config)
    reporter = StylishReporter(color=True, verbose=True)
    
    # Test valid deployment
    print("\n📄 Testing valid deployment...")
    results = yamlguard.kube_validate_files([Path("samples/kubernetes/valid_deployment.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test invalid deployment
    print("\n📄 Testing invalid deployment...")
    results = yamlguard.kube_validate_files([Path("samples/kubernetes/invalid_deployment.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test multi-document
    print("\n📄 Testing multi-document...")
    results = yamlguard.kube_validate_files([Path("samples/kubernetes/multi_document.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test invalid types
    print("\n📄 Testing invalid types...")
    results = yamlguard.kube_validate_files([Path("samples/kubernetes/invalid_types.yaml")])
    report = reporter.report(results)
    print(report)


def test_secrets_samples():
    """Test secrets samples."""
    print("\n🔐 Testing Secrets Samples")
    print("=" * 50)
    
    config = Config()
    config.secrets.enabled = True
    config.secrets.entropy_threshold = 4.0  # Lower threshold for demo
    
    yamlguard = YAMLGuard(config=config)
    reporter = StylishReporter(color=True, verbose=True)
    
    # Test AWS credentials
    print("\n📄 Testing AWS credentials...")
    results = yamlguard.scan_secrets_files([Path("samples/secrets/aws_credentials.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test GitHub tokens
    print("\n📄 Testing GitHub tokens...")
    results = yamlguard.scan_secrets_files([Path("samples/secrets/github_tokens.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test database credentials
    print("\n📄 Testing database credentials...")
    results = yamlguard.scan_secrets_files([Path("samples/secrets/database_credentials.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test private keys
    print("\n📄 Testing private keys...")
    results = yamlguard.scan_secrets_files([Path("samples/secrets/private_keys.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test API keys
    print("\n📄 Testing API keys...")
    results = yamlguard.scan_secrets_files([Path("samples/secrets/api_keys.yaml")])
    report = reporter.report(results)
    print(report)


def test_auto_fix():
    """Test auto-fix functionality."""
    print("\n🔧 Testing Auto-fix")
    print("=" * 50)
    
    config = Config()
    config.indent.step = 2
    
    yamlguard = YAMLGuard(config=config)
    
    # Test fixing indentation
    print("\n📄 Testing indentation fix...")
    results = yamlguard.fix_files([Path("samples/indentation/bad_indentation.yaml")], in_place=False)
    
    for result in results:
        if result['success']:
            print(f"✅ Fixed: {result['file']}")
            if 'content' in result:
                print("Fixed content preview:")
                print("-" * 30)
                print(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
        else:
            print(f"❌ Failed: {result['file']} - {result['error']}")
    
    # Test fixing cosmetics
    print("\n📄 Testing cosmetics fix...")
    results = yamlguard.fix_files([Path("samples/cosmetics/trailing_spaces.yaml")], in_place=False)
    
    for result in results:
        if result['success']:
            print(f"✅ Fixed: {result['file']}")
            if 'content' in result:
                print("Fixed content preview:")
                print("-" * 30)
                print(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
        else:
            print(f"❌ Failed: {result['file']} - {result['error']}")


def test_complex_samples():
    """Test complex samples."""
    print("\n🏗️ Testing Complex Samples")
    print("=" * 50)
    
    config = Config()
    config.indent.step = 2
    config.cosmetics.enabled = True
    
    yamlguard = YAMLGuard(config=config)
    reporter = StylishReporter(color=True, verbose=True)
    
    # Test large config
    print("\n📄 Testing large config...")
    results = yamlguard.lint_files([Path("samples/complex/large_config.yaml")])
    report = reporter.report(results)
    print(report)
    
    # Test multi-document complex
    print("\n📄 Testing multi-document complex...")
    results = yamlguard.lint_files([Path("samples/complex/multi_document_complex.yaml")])
    report = reporter.report(results)
    print(report)


def main():
    """Run all tests."""
    print("🎯 YAMLGuard Sample Testing")
    print("=" * 60)
    
    try:
        # Test indentation samples
        test_indentation_samples()
        
        # Test cosmetics samples
        test_cosmetics_samples()
        
        # Test Kubernetes samples
        test_kubernetes_samples()
        
        # Test secrets samples
        test_secrets_samples()
        
        # Test auto-fix
        test_auto_fix()
        
        # Test complex samples
        test_complex_samples()
        
        print("\n✅ All sample tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Sample testing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
