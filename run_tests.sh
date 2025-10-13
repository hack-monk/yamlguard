#!/bin/bash

# YAMLGuard Test Runner
# This script runs various tests on the sample files

echo "🎯 YAMLGuard Test Runner"
echo "========================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run this script from the YAMLGuard root directory."
    exit 1
fi

# Install YAMLGuard in development mode
echo "📦 Installing YAMLGuard in development mode..."
pip install -e . > /dev/null 2>&1

# Test indentation samples
echo ""
echo "🔍 Testing Indentation Samples"
echo "------------------------------"
yamlguard lint samples/indentation/ --indent 2 --strict

# Test cosmetics samples
echo ""
echo "🎨 Testing Cosmetics Samples"
echo "----------------------------"
yamlguard lint samples/cosmetics/ --indent 2

# Test Kubernetes samples
echo ""
echo "🚀 Testing Kubernetes Samples"
echo "-----------------------------"
yamlguard kube-validate samples/kubernetes/ --kube-version 1.30

# Test secrets samples
echo ""
echo "🔐 Testing Secrets Samples"
echo "-------------------------"
yamlguard scan-secrets samples/secrets/ --entropy 4.0

# Test complex samples
echo ""
echo "🏗️ Testing Complex Samples"
echo "--------------------------"
yamlguard lint samples/complex/ --indent 2

# Test auto-fix
echo ""
echo "🔧 Testing Auto-fix"
echo "-------------------"
yamlguard fix samples/indentation/bad_indentation.yaml --in-place

# Test all samples
echo ""
echo "📋 Testing All Samples"
echo "---------------------"
yamlguard lint samples/ --indent 2

echo ""
echo "✅ All tests completed!"
echo ""
echo "📚 Next steps:"
echo "   1. Run 'python test_samples.py' for detailed testing"
echo "   2. Run 'yamlguard --help' to see all available commands"
echo "   3. Run 'yamlguard init' to create a configuration file"
