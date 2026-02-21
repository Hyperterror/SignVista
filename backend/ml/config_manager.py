"""
Configuration Manager for ISL Unified Models Integration.

This module handles loading, validation, and access to configuration for
the ISL detection, recognition, and translation modules.
"""

import json
import os
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    """Configuration for a single ISL module."""
    enabled: bool = True
    priority: int = 1
    confidence_threshold: float = 0.7
    model_path: str = ""
    preprocessing_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ISLModulesConfig:
    """Top-level configuration for ISL integration."""
    modules: Dict[str, ModuleConfig] = field(default_factory=dict)
    prediction_strategy: str = "priority"
    enable_parallel_execution: bool = False
    performance_monitoring: bool = True
    fallback_to_existing_lstm: bool = True


class ConfigurationManager:
    """Manages configuration for ISL modules."""
    
    DEFAULT_CONFIG = {
        "modules": {
            "detection": {
                "enabled": True,
                "priority": 2,
                "confidence_threshold": 0.7,
                "model_path": "ISL-Unified-Project/models/detection/gesture_classifier.h5",
                "preprocessing_params": {
                    "max_num_hands": 2,
                    "model_complexity": 0
                }
            },
            "recognition": {
                "enabled": True,
                "priority": 1,
                "confidence_threshold": 0.6,
                "model_path": "ISL-Unified-Project/models/recognition/lstm_word_model.hdf5",
                "preprocessing_params": {
                    "buffer_size": 45,
                    "feature_count": 258
                }
            },
            "translation": {
                "enabled": False,
                "priority": 3,
                "confidence_threshold": 0.7,
                "model_path": "ISL-Unified-Project/models/translation/squeezenet_model",
                "preprocessing_params": {
                    "yolo_confidence": 0.5,
                    "yolo_threshold": 0.3,
                    "yolo_size": 416
                }
            }
        },
        "prediction_strategy": "priority",
        "enable_parallel_execution": False,
        "performance_monitoring": True,
        "fallback_to_existing_lstm": True
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration JSON file. If None, uses default path.
        """
        self.config_path = config_path or "backend/config/isl_modules.json"
        self.config: ISLModulesConfig = self._load_config()
        
    def _load_config(self) -> ISLModulesConfig:
        """Load configuration from file or environment variables."""
        config_dict = self.DEFAULT_CONFIG.copy()
        
        # Try to load from environment variable first
        env_config = os.environ.get("ISL_MODULE_CONFIG")
        if env_config:
            try:
                env_dict = json.loads(env_config)
                config_dict = self._merge_configs(config_dict, env_dict)
                logger.info("Loaded configuration from ISL_MODULE_CONFIG environment variable")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse ISL_MODULE_CONFIG: {e}. Using defaults.")
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_dict = json.load(f)
                config_dict = self._merge_configs(config_dict, file_dict)
                logger.info(f"Loaded configuration from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
        else:
            logger.info(f"Configuration file {self.config_path} not found. Using defaults.")
        
        # Convert to dataclass
        return self._dict_to_config(config_dict)
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Merge override config into base config."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _dict_to_config(self, config_dict: Dict) -> ISLModulesConfig:
        """Convert dictionary to ISLModulesConfig dataclass."""
        modules = {}
        for module_name, module_data in config_dict.get("modules", {}).items():
            modules[module_name] = ModuleConfig(**module_data)
        
        return ISLModulesConfig(
            modules=modules,
            prediction_strategy=config_dict.get("prediction_strategy", "priority"),
            enable_parallel_execution=config_dict.get("enable_parallel_execution", False),
            performance_monitoring=config_dict.get("performance_monitoring", True),
            fallback_to_existing_lstm=config_dict.get("fallback_to_existing_lstm", True)
        )
    
    def is_module_enabled(self, module_name: str) -> bool:
        """
        Check if a module is enabled.
        
        Args:
            module_name: Name of the module (detection, recognition, translation)
            
        Returns:
            True if module is enabled, False otherwise
        """
        if module_name not in self.config.modules:
            return False
        return self.config.modules[module_name].enabled
    
    def get_module_config(self, module_name: str) -> Optional[ModuleConfig]:
        """
        Get configuration for a specific module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            ModuleConfig if module exists, None otherwise
        """
        return self.config.modules.get(module_name)
    
    def get_prediction_strategy(self) -> str:
        """
        Get the configured prediction selection strategy.
        
        Returns:
            Strategy name: "priority", "highest_confidence", or "voting"
        """
        return self.config.prediction_strategy
    
    def get_confidence_threshold(self, module_name: str) -> float:
        """
        Get confidence threshold for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Confidence threshold (0.0 to 1.0), or 0.7 as default
        """
        module_config = self.get_module_config(module_name)
        if module_config:
            return module_config.confidence_threshold
        return 0.7
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate prediction strategy
        valid_strategies = ["priority", "highest_confidence", "voting"]
        if self.config.prediction_strategy not in valid_strategies:
            errors.append(
                f"Invalid prediction_strategy: {self.config.prediction_strategy}. "
                f"Must be one of {valid_strategies}"
            )
        
        # Validate module configurations
        for module_name, module_config in self.config.modules.items():
            # Validate confidence threshold
            if not 0.0 <= module_config.confidence_threshold <= 1.0:
                errors.append(
                    f"Module {module_name}: confidence_threshold must be between 0.0 and 1.0, "
                    f"got {module_config.confidence_threshold}"
                )
            
            # Validate priority
            if module_config.priority < 1:
                errors.append(
                    f"Module {module_name}: priority must be >= 1, got {module_config.priority}"
                )
            
            # Validate model path (if enabled)
            if module_config.enabled and not module_config.model_path:
                errors.append(f"Module {module_name}: model_path is required when enabled")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Configuration validation failed: {errors}")
        
        return is_valid, errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Return configuration status for health endpoint.
        
        Returns:
            Dictionary with configuration health information
        """
        is_valid, errors = self.validate()
        
        enabled_modules = [
            name for name, config in self.config.modules.items() 
            if config.enabled
        ]
        
        return {
            "config_valid": is_valid,
            "config_errors": errors,
            "config_path": self.config_path,
            "enabled_modules": enabled_modules,
            "prediction_strategy": self.config.prediction_strategy,
            "parallel_execution": self.config.enable_parallel_execution,
            "performance_monitoring": self.config.performance_monitoring
        }
