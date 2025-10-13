"""
Tests for configuration system.

Comprehensive tests for the configuration system including
loading, validation, and default values.
"""

import pytest
from pathlib import Path
from yamlguard.config import Config, IndentConfig, CosmeticsConfig, KubernetesConfig, SecretsConfig, ReporterConfig


class TestConfig:
    """Test cases for Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        # Test indent config
        assert config.indent.step == 2
        assert config.indent.strict is True
        assert config.indent.fix is False
        
        # Test cosmetics config
        assert config.cosmetics.enabled is True
        assert config.cosmetics.trailing_spaces is True
        assert config.cosmetics.tabs is True
        assert config.cosmetics.bom is True
        assert config.cosmetics.duplicate_keys is True
        assert config.cosmetics.line_length == 120
        
        # Test kubernetes config
        assert config.kubernetes.enabled is False
        assert config.kubernetes.version == "1.30"
        assert config.kubernetes.strict is False
        assert config.kubernetes.use_kubeconform is True
        assert config.kubernetes.cache_schemas is True
        
        # Test secrets config
        assert config.secrets.enabled is False
        assert config.secrets.baseline is None
        assert config.secrets.allowlist == []
        assert config.secrets.entropy_threshold == 4.5
        assert config.secrets.use_detect_secrets is False
        assert config.secrets.use_gitleaks is False
        
        # Test reporter config
        assert config.reporter.format == "stylish"
        assert config.reporter.color is True
        assert config.reporter.verbose is False
        assert config.reporter.fail_on == "error"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = Config()
        
        # Modify indent config
        config.indent.step = 4
        config.indent.strict = False
        config.indent.fix = True
        
        # Modify cosmetics config
        config.cosmetics.enabled = False
        config.cosmetics.line_length = 100
        
        # Modify kubernetes config
        config.kubernetes.enabled = True
        config.kubernetes.version = "1.29"
        config.kubernetes.strict = True
        
        # Modify secrets config
        config.secrets.enabled = True
        config.secrets.entropy_threshold = 5.0
        
        # Modify reporter config
        config.reporter.format = "json"
        config.reporter.color = False
        config.reporter.verbose = True
        
        # Verify changes
        assert config.indent.step == 4
        assert config.indent.strict is False
        assert config.indent.fix is True
        
        assert config.cosmetics.enabled is False
        assert config.cosmetics.line_length == 100
        
        assert config.kubernetes.enabled is True
        assert config.kubernetes.version == "1.29"
        assert config.kubernetes.strict is True
        
        assert config.secrets.enabled is True
        assert config.secrets.entropy_threshold == 5.0
        
        assert config.reporter.format == "json"
        assert config.reporter.color is False
        assert config.reporter.verbose is True
    
    def test_validation(self):
        """Test configuration validation."""
        # Test valid indent step
        config = Config()
        config.indent.step = 4
        assert config.indent.step == 4
        
        # Test invalid indent step (should raise validation error)
        with pytest.raises(ValueError):
            config.indent.step = 0
        
        with pytest.raises(ValueError):
            config.indent.step = 10
        
        # Test valid reporter format
        config.reporter.format = "jsonl"
        assert config.reporter.format == "jsonl"
        
        # Test invalid reporter format
        with pytest.raises(ValueError):
            config.reporter.format = "invalid"
        
        # Test valid kubernetes version
        config.kubernetes.version = "1.30.2"
        assert config.kubernetes.version == "1.30.2"
        
        # Test invalid kubernetes version
        with pytest.raises(ValueError):
            config.kubernetes.version = "invalid"
    
    def test_get_severity_threshold(self):
        """Test getting severity threshold."""
        config = Config()
        
        # Test default threshold
        assert config.get_severity_threshold() == 3  # error
        
        # Test different thresholds
        config.reporter.fail_on = "warning"
        assert config.get_severity_threshold() == 2
        
        config.reporter.fail_on = "info"
        assert config.get_severity_threshold() == 1
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config = Config()
        config.indent.step = 4
        config.kubernetes.version = "1.29"
        config.secrets.enabled = True
        
        # Save configuration
        config_file = tmp_path / "test_config.yml"
        config.save(config_file)
        
        # Load configuration
        loaded_config = Config.from_file(config_file)
        
        # Verify loaded values
        assert loaded_config.indent.step == 4
        assert loaded_config.kubernetes.version == "1.29"
        assert loaded_config.secrets.enabled is True
    
    def test_find_config(self, tmp_path):
        """Test finding configuration in directory hierarchy."""
        # Create a config file in a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        config_file = subdir / ".yamlguard.yml"
        
        config = Config()
        config.indent.step = 4
        config.save(config_file)
        
        # Test finding config from subdirectory
        found_config = Config.find_config(subdir)
        assert found_config is not None
        assert found_config.indent.step == 4
        
        # Test finding config from parent directory
        found_config = Config.find_config(subdir / "nested")
        assert found_config is not None
        assert found_config.indent.step == 4
        
        # Test not finding config
        found_config = Config.find_config(tmp_path / "nonexistent")
        assert found_config is None


class TestIndentConfig:
    """Test cases for IndentConfig class."""
    
    def test_default_values(self):
        """Test default values for IndentConfig."""
        config = IndentConfig()
        assert config.step == 2
        assert config.strict is True
        assert config.fix is False
    
    def test_custom_values(self):
        """Test custom values for IndentConfig."""
        config = IndentConfig(step=4, strict=False, fix=True)
        assert config.step == 4
        assert config.strict is False
        assert config.fix is True
    
    def test_validation(self):
        """Test validation for IndentConfig."""
        # Test valid step
        config = IndentConfig(step=4)
        assert config.step == 4
        
        # Test invalid step
        with pytest.raises(ValueError):
            IndentConfig(step=0)
        
        with pytest.raises(ValueError):
            IndentConfig(step=10)


class TestCosmeticsConfig:
    """Test cases for CosmeticsConfig class."""
    
    def test_default_values(self):
        """Test default values for CosmeticsConfig."""
        config = CosmeticsConfig()
        assert config.enabled is True
        assert config.trailing_spaces is True
        assert config.tabs is True
        assert config.bom is True
        assert config.duplicate_keys is True
        assert config.line_length == 120
    
    def test_custom_values(self):
        """Test custom values for CosmeticsConfig."""
        config = CosmeticsConfig(
            enabled=False,
            trailing_spaces=False,
            tabs=False,
            bom=False,
            duplicate_keys=False,
            line_length=100
        )
        assert config.enabled is False
        assert config.trailing_spaces is False
        assert config.tabs is False
        assert config.bom is False
        assert config.duplicate_keys is False
        assert config.line_length == 100
    
    def test_validation(self):
        """Test validation for CosmeticsConfig."""
        # Test valid line length
        config = CosmeticsConfig(line_length=100)
        assert config.line_length == 100
        
        # Test invalid line length
        with pytest.raises(ValueError):
            CosmeticsConfig(line_length=50)  # Too short
        
        with pytest.raises(ValueError):
            CosmeticsConfig(line_length=0)  # Too short


class TestKubernetesConfig:
    """Test cases for KubernetesConfig class."""
    
    def test_default_values(self):
        """Test default values for KubernetesConfig."""
        config = KubernetesConfig()
        assert config.enabled is False
        assert config.version == "1.30"
        assert config.strict is False
        assert config.use_kubeconform is True
        assert config.cache_schemas is True
    
    def test_custom_values(self):
        """Test custom values for KubernetesConfig."""
        config = KubernetesConfig(
            enabled=True,
            version="1.29",
            strict=True,
            use_kubeconform=False,
            cache_schemas=False
        )
        assert config.enabled is True
        assert config.version == "1.29"
        assert config.strict is True
        assert config.use_kubeconform is False
        assert config.cache_schemas is False


class TestSecretsConfig:
    """Test cases for SecretsConfig class."""
    
    def test_default_values(self):
        """Test default values for SecretsConfig."""
        config = SecretsConfig()
        assert config.enabled is False
        assert config.baseline is None
        assert config.allowlist == []
        assert config.entropy_threshold == 4.5
        assert config.use_detect_secrets is False
        assert config.use_gitleaks is False
    
    def test_custom_values(self):
        """Test custom values for SecretsConfig."""
        baseline_path = Path("/tmp/baseline.json")
        config = SecretsConfig(
            enabled=True,
            baseline=baseline_path,
            allowlist=["*.test.yaml"],
            entropy_threshold=5.0,
            use_detect_secrets=True,
            use_gitleaks=True
        )
        assert config.enabled is True
        assert config.baseline == baseline_path
        assert config.allowlist == ["*.test.yaml"]
        assert config.entropy_threshold == 5.0
        assert config.use_detect_secrets is True
        assert config.use_gitleaks is True
    
    def test_validation(self):
        """Test validation for SecretsConfig."""
        # Test valid entropy threshold
        config = SecretsConfig(entropy_threshold=5.0)
        assert config.entropy_threshold == 5.0
        
        # Test invalid entropy threshold
        with pytest.raises(ValueError):
            SecretsConfig(entropy_threshold=-1.0)
        
        with pytest.raises(ValueError):
            SecretsConfig(entropy_threshold=10.0)


class TestReporterConfig:
    """Test cases for ReporterConfig class."""
    
    def test_default_values(self):
        """Test default values for ReporterConfig."""
        config = ReporterConfig()
        assert config.format == "stylish"
        assert config.color is True
        assert config.verbose is False
        assert config.fail_on == "error"
    
    def test_custom_values(self):
        """Test custom values for ReporterConfig."""
        config = ReporterConfig(
            format="json",
            color=False,
            verbose=True,
            fail_on="warning"
        )
        assert config.format == "json"
        assert config.color is False
        assert config.verbose is True
        assert config.fail_on == "warning"
    
    def test_validation(self):
        """Test validation for ReporterConfig."""
        # Test valid format
        config = ReporterConfig(format="jsonl")
        assert config.format == "jsonl"
        
        # Test invalid format
        with pytest.raises(ValueError):
            ReporterConfig(format="invalid")
        
        # Test valid fail_on
        config = ReporterConfig(fail_on="info")
        assert config.fail_on == "info"
        
        # Test invalid fail_on
        with pytest.raises(ValueError):
            ReporterConfig(fail_on="invalid")
