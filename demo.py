#!/usr/bin/env python3
"""
Demo script for YAMLGuard functionality.

This script demonstrates the core YAMLGuard functionality including
linting, validation, and secrets scanning.
"""

import sys
from pathlib import Path

# Add the yamlguard package to the path
sys.path.insert(0, str(Path(__file__).parent))

from yamlguard import YAMLGuard, Config
from yamlguard.reporters import StylishReporter


def demo_linting():
    """Demonstrate YAML linting functionality."""
    print("🔍 YAMLGuard Linting Demo")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    config.indent.step = 2
    config.cosmetics.enabled = True
    
    # Initialize YAMLGuard
    yamlguard = YAMLGuard(config=config)
    
    # Lint the example file
    results = yamlguard.lint_files([Path("example.yaml")])
    
    # Create reporter
    reporter = StylishReporter(color=True, verbose=True)
    
    # Generate report
    report = reporter.report(results)
    print(report)


def demo_kubernetes_validation():
    """Demonstrate Kubernetes validation functionality."""
    print("\n🚀 Kubernetes Validation Demo")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    config.kubernetes.enabled = True
    config.kubernetes.version = "1.30"
    config.kubernetes.strict = False
    
    # Initialize YAMLGuard
    yamlguard = YAMLGuard(config=config)
    
    # Validate the example file
    results = yamlguard.kube_validate_files([Path("example.yaml")])
    
    # Create reporter
    reporter = StylishReporter(color=True, verbose=True)
    
    # Generate report
    report = reporter.report(results)
    print(report)


def demo_secrets_scanning():
    """Demonstrate secrets scanning functionality."""
    print("\n🔐 Secrets Scanning Demo")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    config.secrets.enabled = True
    config.secrets.entropy_threshold = 4.0  # Lower threshold for demo
    
    # Initialize YAMLGuard
    yamlguard = YAMLGuard(config=config)
    
    # Scan the example file
    results = yamlguard.scan_secrets_files([Path("example.yaml")])
    
    # Create reporter
    reporter = StylishReporter(color=True, verbose=True)
    
    # Generate report
    report = reporter.report(results)
    print(report)


def demo_auto_fix():
    """Demonstrate auto-fix functionality."""
    print("\n🔧 Auto-fix Demo")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    config.indent.step = 2
    
    # Initialize YAMLGuard
    yamlguard = YAMLGuard(config=config)
    
    # Fix the example file
    results = yamlguard.fix_files([Path("example.yaml")], in_place=False)
    
    for result in results:
        if result['success']:
            print(f"✅ Fixed: {result['file']}")
            if 'content' in result:
                print("Fixed content preview:")
                print("-" * 30)
                print(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])
        else:
            print(f"❌ Failed: {result['file']} - {result['error']}")


def main():
    """Run all demos."""
    print("🎯 YAMLGuard Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Run linting demo
        demo_linting()
        
        # Run Kubernetes validation demo
        demo_kubernetes_validation()
        
        # Run secrets scanning demo
        demo_secrets_scanning()
        
        # Run auto-fix demo
        demo_auto_fix()
        
        print("\n✅ All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
