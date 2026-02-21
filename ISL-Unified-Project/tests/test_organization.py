"""
Property-Based Tests for ISL Project Organization
Tests validate the correctness of the project organization structure
"""

import os
import json


def test_file_completeness():
    """
    Property 1: File Completeness
    Validates: Requirements 1.1, 1.2
    
    Verify all essential files from source projects are present in the organized structure.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    essential_files = [
        'detection/isl_detection.py',
        'detection/dataset_keypoint_generation.py',
        'recognition/deploy_code.py',
        'recognition/helper_functions.py',
        'recognition/app.py',
        'translation/main.py',
        'translation/preprocessing.py',
        'translation/yolo.py',
        'models/detection/gesture_classifier.h5',
        'models/recognition/lstm_word_model.hdf5',
        'models/translation/squeezenet_model',
        'config/detection_config.json',
        'config/recognition_config.json',
        'config/translation_config.json',
        'config/translation_classes.json',
        'requirements.txt',
        'README.md',
        '.gitignore'
    ]
    
    missing_files = []
    for file_path in essential_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    assert len(missing_files) == 0, \
        f"Missing essential files: {', '.join(missing_files)}"
    
    print("✓ Property 1 PASSED: All essential files are present")


def test_no_duplicate_dependencies():
    """
    Property 2: No Duplicate Dependencies
    Validates: Requirements 5.1, 5.2
    
    Verify requirements.txt contains no duplicate packages.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(base_path, 'requirements.txt')
    
    with open(requirements_path, 'r') as f:
        lines = f.readlines()
    
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name (before == or >=)
            package_name = line.split('==')[0].split('>=')[0].strip()
            packages.append(package_name.lower())
    
    duplicates = []
    seen = set()
    for pkg in packages:
        if pkg in seen:
            duplicates.append(pkg)
        seen.add(pkg)
    
    assert len(duplicates) == 0, \
        f"Duplicate packages found in requirements.txt: {', '.join(duplicates)}"
    
    print(f"✓ Property 2 PASSED: No duplicate dependencies ({len(packages)} unique packages)")


def test_documentation_completeness():
    """
    Property 3: Documentation Completeness
    Validates: Requirements 6.1, 6.2
    
    Verify all modules have corresponding documentation files.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_docs = [
        'README.md',
        'docs/DETECTION.md',
        'docs/RECOGNITION.md',
        'docs/TRANSLATION.md'
    ]
    
    missing_docs = []
    for doc_path in required_docs:
        full_path = os.path.join(base_path, doc_path)
        if not os.path.exists(full_path):
            missing_docs.append(doc_path)
    
    assert len(missing_docs) == 0, \
        f"Missing documentation files: {', '.join(missing_docs)}"
    
    print("✓ Property 3 PASSED: All required documentation files exist")


def test_configuration_validity():
    """
    Property 4: Configuration Validity
    Validates: Requirements 1.1
    
    Verify all JSON configuration files are valid and contain required keys.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    configs = {
        'config/detection_config.json': ['model_path', 'landmark_count', 'confidence_threshold'],
        'config/recognition_config.json': ['model_path', 'frame_count', 'supported_words'],
        'config/translation_config.json': ['model_path', 'class_mapping', 'yolo_config']
    }
    
    errors = []
    for config_path, required_keys in configs.items():
        full_path = os.path.join(base_path, config_path)
        
        try:
            with open(full_path, 'r') as f:
                config = json.load(f)
            
            for key in required_keys:
                if key not in config:
                    errors.append(f"Missing required key '{key}' in {config_path}")
        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {config_path}: {str(e)}")
        except FileNotFoundError:
            errors.append(f"Configuration file not found: {config_path}")
    
    assert len(errors) == 0, \
        f"Configuration validation errors: {'; '.join(errors)}"
    
    print("✓ Property 4 PASSED: All configuration files are valid")


def test_directory_structure():
    """
    Property 5: Directory Structure
    Validates: Requirements 1.1
    
    Verify all required directories exist in the project structure.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        'detection',
        'detection/data',
        'detection/notebooks',
        'recognition',
        'recognition/data',
        'recognition/notebooks',
        'translation',
        'shared',
        'models',
        'models/detection',
        'models/recognition',
        'models/translation',
        'config',
        'config/yolo',
        'docs',
        'tests'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.isdir(full_path):
            missing_dirs.append(dir_path)
    
    assert len(missing_dirs) == 0, \
        f"Missing required directories: {', '.join(missing_dirs)}"
    
    print("✓ Property 5 PASSED: All required directories exist")


if __name__ == "__main__":
    print("Running ISL Project Organization Property Tests...\n")
    
    try:
        test_file_completeness()
        test_no_duplicate_dependencies()
        test_documentation_completeness()
        test_configuration_validity()
        test_directory_structure()
        
        print("\n" + "="*60)
        print("ALL PROPERTY TESTS PASSED ✓")
        print("="*60)
        print("\nProject organization is valid and complete!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        exit(1)
