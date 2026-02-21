"""
Unit tests for Configuration Manager.
"""

import json
import os
import tempfile
import pytest
from backend.ml.config_manager import ConfigurationManager, ModuleConfig, ISLModulesConfig


class TestConfigurationManager:
    """Test suite for ConfigurationManager."""
    
    def test_load_default_config(self):
        """Test loading default configuration when no file exists."""
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        assert config_manager.is_module_enabled("detection")
        assert config_manager.is_module_enabled("recognition")
        assert not config_manager.is_module_enabled("translation")
        assert config_manager.get_prediction_strategy() == "priority"
    
    def test_load_config_from_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "modules": {
                "detection": {
                    "enabled": False,
                    "priority": 3,
                    "confidence_threshold": 0.8,
                    "model_path": "test/path.h5",
                    "preprocessing_params": {}
                }
            },
            "prediction_strategy": "highest_confidence"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            
            assert not config_manager.is_module_enabled("detection")
            assert config_manager.get_prediction_strategy() == "highest_confidence"
            
            detection_config = config_manager.get_module_config("detection")
            assert detection_config.priority == 3
            assert detection_config.confidence_threshold == 0.8
        finally:
            os.unlink(temp_path)
    
    def test_load_config_from_environment(self, monkeypatch):
        """Test loading configuration from environment variable."""
        env_config = json.dumps({
            "modules": {
                "translation": {
                    "enabled": True,
                    "priority": 1,
                    "confidence_threshold": 0.9,
                    "model_path": "env/path.h5",
                    "preprocessing_params": {}
                }
            },
            "prediction_strategy": "voting"
        })
        
        monkeypatch.setenv("ISL_MODULE_CONFIG", env_config)
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        assert config_manager.is_module_enabled("translation")
        assert config_manager.get_prediction_strategy() == "voting"
    
    def test_get_module_config(self):
        """Test retrieving module configuration."""
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        detection_config = config_manager.get_module_config("detection")
        assert detection_config is not None
        assert isinstance(detection_config, ModuleConfig)
        assert detection_config.enabled is True
        
        nonexistent_config = config_manager.get_module_config("nonexistent")
        assert nonexistent_config is None
    
    def test_get_confidence_threshold(self):
        """Test retrieving confidence threshold for modules."""
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        detection_threshold = config_manager.get_confidence_threshold("detection")
        assert detection_threshold == 0.7
        
        recognition_threshold = config_manager.get_confidence_threshold("recognition")
        assert recognition_threshold == 0.6
        
        # Test default for nonexistent module
        default_threshold = config_manager.get_confidence_threshold("nonexistent")
        assert default_threshold == 0.7
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        is_valid, errors = config_manager.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_invalid_strategy(self):
        """Test validation catches invalid prediction strategy."""
        config_data = {
            "modules": {},
            "prediction_strategy": "invalid_strategy"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            is_valid, errors = config_manager.validate()
            
            assert not is_valid
            assert len(errors) > 0
            assert any("prediction_strategy" in error for error in errors)
        finally:
            os.unlink(temp_path)
    
    def test_validate_invalid_confidence_threshold(self):
        """Test validation catches invalid confidence threshold."""
        config_data = {
            "modules": {
                "detection": {
                    "enabled": True,
                    "priority": 1,
                    "confidence_threshold": 1.5,
                    "model_path": "test.h5",
                    "preprocessing_params": {}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            is_valid, errors = config_manager.validate()
            
            assert not is_valid
            assert len(errors) > 0
            assert any("confidence_threshold" in error for error in errors)
        finally:
            os.unlink(temp_path)
    
    def test_validate_invalid_priority(self):
        """Test validation catches invalid priority."""
        config_data = {
            "modules": {
                "detection": {
                    "enabled": True,
                    "priority": 0,
                    "confidence_threshold": 0.7,
                    "model_path": "test.h5",
                    "preprocessing_params": {}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            is_valid, errors = config_manager.validate()
            
            assert not is_valid
            assert len(errors) > 0
            assert any("priority" in error for error in errors)
        finally:
            os.unlink(temp_path)
    
    def test_validate_missing_model_path(self):
        """Test validation catches missing model path for enabled module."""
        config_data = {
            "modules": {
                "detection": {
                    "enabled": True,
                    "priority": 1,
                    "confidence_threshold": 0.7,
                    "model_path": "",
                    "preprocessing_params": {}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            is_valid, errors = config_manager.validate()
            
            assert not is_valid
            assert len(errors) > 0
            assert any("model_path" in error for error in errors)
        finally:
            os.unlink(temp_path)
    
    def test_get_health_status(self):
        """Test health status reporting."""
        config_manager = ConfigurationManager(config_path="nonexistent.json")
        
        health_status = config_manager.get_health_status()
        
        assert "config_valid" in health_status
        assert "config_errors" in health_status
        assert "enabled_modules" in health_status
        assert "prediction_strategy" in health_status
        
        assert health_status["config_valid"] is True
        assert "detection" in health_status["enabled_modules"]
        assert "recognition" in health_status["enabled_modules"]
        assert health_status["prediction_strategy"] == "priority"
    
    def test_merge_configs(self):
        """Test configuration merging from multiple sources."""
        base_config = {
            "modules": {
                "detection": {
                    "enabled": True,
                    "priority": 2,
                    "confidence_threshold": 0.7,
                    "model_path": "base/path.h5",
                    "preprocessing_params": {"param1": 1}
                }
            },
            "prediction_strategy": "priority"
        }
        
        override_config = {
            "modules": {
                "detection": {
                    "enabled": False,
                    "confidence_threshold": 0.9
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(base_config, f)
            temp_path = f.name
        
        try:
            # Create config manager with base file
            config_manager = ConfigurationManager(config_path=temp_path)
            
            # Manually merge override
            merged = config_manager._merge_configs(base_config, override_config)
            
            # Check that override values are applied
            assert merged["modules"]["detection"]["enabled"] is False
            assert merged["modules"]["detection"]["confidence_threshold"] == 0.9
            # Check that non-overridden values are preserved
            assert merged["modules"]["detection"]["priority"] == 2
            assert merged["modules"]["detection"]["model_path"] == "base/path.h5"
        finally:
            os.unlink(temp_path)
