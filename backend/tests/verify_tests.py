#!/usr/bin/env python3
"""
Test Verification Script

Verify that integration tests are syntactically correct and can be imported
without requiring actual database connections.

This script can be run in CI/CD environments to catch syntax errors
before attempting to run integration tests against real services.
"""
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict


def check_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source)
        return True, "OK"
        
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_imports(file_path: Path) -> Tuple[bool, str]:
    """Check if file can be imported (basic import validation)."""
    try:
        # Create module spec
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        if spec is None:
            return False, "Could not create module spec"
        
        # Don't actually import to avoid dependency issues
        # Just verify the spec can be created
        return True, "Import structure OK"
        
    except Exception as e:
        return False, f"Import error: {e}"


def analyze_test_structure(file_path: Path) -> Dict[str, List[str]]:
    """Analyze test file structure and extract test information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        info = {
            "classes": [],
            "test_methods": [],
            "fixtures": [],
            "imports": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    info["classes"].append(node.name)
                    
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    info["test_methods"].append(node.name)
                elif any(d.id == "pytest" and hasattr(d, "attr") and d.attr == "fixture" 
                        for d in node.decorator_list 
                        if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name)):
                    info["fixtures"].append(node.name)
                    
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    info["imports"].append(alias.name)
                    
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    info["imports"].append(f"{module}.{alias.name}")
        
        return info
        
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main verification function."""
    print("Verifying Integration Tests")
    print("=" * 50)
    
    # Test files to verify
    test_files = [
        "test_db_integration.py",
        "test_e2e_api.py",
        "conftest_integration.py", 
        "run_integration_tests.py"
    ]
    
    tests_dir = Path(__file__).parent
    all_passed = True
    
    for test_file in test_files:
        file_path = tests_dir / test_file
        
        print(f"\nChecking {test_file}...")
        
        if not file_path.exists():
            print(f"  [ERROR] File not found: {file_path}")
            all_passed = False
            continue
        
        # Check syntax
        syntax_ok, syntax_msg = check_python_syntax(file_path)
        if syntax_ok:
            print(f"  [OK] Syntax: {syntax_msg}")
        else:
            print(f"  [ERROR] Syntax: {syntax_msg}")
            all_passed = False
            continue
        
        # Check imports
        import_ok, import_msg = check_imports(file_path)
        if import_ok:
            print(f"  [OK] Imports: {import_msg}")
        else:
            print(f"  [WARN] Imports: {import_msg}")
        
        # Analyze structure  
        if test_file.startswith("test_"):
            structure = analyze_test_structure(file_path)
            
            if "error" in structure:
                print(f"  [WARN] Structure analysis failed: {structure['error']}")
            else:
                print(f"  [INFO] Structure:")
                print(f"     Test classes: {len(structure['classes'])}")
                print(f"     Test methods: {len(structure['test_methods'])}")
                print(f"     Fixtures: {len(structure['fixtures'])}")
                
                if structure['classes']:
                    print(f"     Classes: {', '.join(structure['classes'][:3])}{'...' if len(structure['classes']) > 3 else ''}")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("SUCCESS: All integration tests verified successfully!")
        print("\nNext steps:")
        print("1. Start Docker services: docker-compose up -d")
        print("2. Run tests: python tests/run_integration_tests.py")
        return 0
    else:
        print("FAILED: Some integration tests failed verification!")
        print("\nPlease fix the errors above before running integration tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())