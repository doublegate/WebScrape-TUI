#!/usr/bin/env python3
"""Script to migrate legacy test files to use monolithic scrapetui.py imports.

This script automatically updates legacy test files that import from the scrapetui package
to instead import from the monolithic scrapetui.py file. This is necessary because the
package __init__.py sets many managers to None to prevent loading the monolithic TUI.

Usage:
    python migrate_legacy_tests.py test_filename.py
    python migrate_legacy_tests.py --all  # Migrate all legacy test files
"""

import sys
import re
from pathlib import Path

# Monolithic import template
MONOLITHIC_IMPORT_TEMPLATE = """
# Import from monolithic scrapetui.py file directly
# We need to import the .py file, not the package directory
import importlib.util
_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from the monolithic module
{imports}
""".strip()


def extract_scrapetui_imports(content):
    """Extract all imports from scrapetui in the file."""
    import_pattern = r'from scrapetui import (.+)'
    imports = []

    for line in content.split('\n'):
        match = re.match(import_pattern, line)
        if match:
            # Handle multi-line imports
            import_list = match.group(1)
            if '(' in import_list:
                # Multi-line import - need to find closing paren
                pass  # For now, skip multi-line
            else:
                # Single line
                items = [item.strip() for item in import_list.split(',')]
                imports.extend(items)

    return imports


def generate_monolithic_imports(imports):
    """Generate import statements for monolithic module."""
    lines = []
    for item in imports:
        lines.append(f"{item} = _scrapetui_module.{item}")
    return '\n'.join(lines)


def migrate_test_file(filepath):
    """Migrate a single test file to use monolithic imports."""
    print(f"Migrating {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already migrated
    if '_scrapetui_module' in content:
        print(f"  ✓ Already migrated")
        return

    # Find the import statement
    pattern = r'from scrapetui import \([^)]+\)|from scrapetui import .+'
    match = re.search(pattern, content)

    if not match:
        print(f"  ⚠ No scrapetui imports found")
        return

    # Extract imports
    import_statement = match.group(0)

    # Parse imports
    if '(' in import_statement:
        # Multi-line import
        imports_text = import_statement[import_statement.find('(')+1:import_statement.find(')')]
    else:
        # Single line
        imports_text = import_statement.replace('from scrapetui import ', '')

    imports = [item.strip() for item in imports_text.replace('\n', ',').split(',') if item.strip()]

    # Generate new imports
    import_lines = generate_monolithic_imports(imports)
    new_import = MONOLITHIC_IMPORT_TEMPLATE.format(imports=import_lines)

    # Replace the import
    new_content = content.replace(import_statement, new_import)

    # Ensure Path is imported
    if 'from pathlib import Path' not in new_content and 'import pathlib' not in new_content:
        # Add Path import after other imports
        import_section_end = new_content.find('\n\n')
        if import_section_end > 0:
            new_content = new_content[:import_section_end] + '\nfrom pathlib import Path' + new_content[import_section_end:]

    # Write back
    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"  ✓ Migrated successfully")
    print(f"    Imports: {', '.join(imports)}")


def migrate_all_legacy_tests():
    """Migrate all legacy test files."""
    tests_dir = Path('tests')
    legacy_test_files = [
        'test_scraping.py',
        'test_utils.py',
        'test_bulk_operations.py',
        'test_json_export.py',
        'test_ai_providers.py',
        'test_database.py',
        'test_config_and_presets.py',
        'test_enhanced_export.py',
        'test_topic_modeling.py',
        'test_question_answering.py',
        'test_duplicate_detection.py',
        'test_summary_quality.py',
        'test_advanced_ai.py',
        'test_entity_relationships.py',
    ]

    for test_file in legacy_test_files:
        filepath = tests_dir / test_file
        if filepath.exists():
            try:
                migrate_test_file(filepath)
            except Exception as e:
                print(f"  ✗ Error: {e}")
        else:
            print(f"  ⚠ File not found: {filepath}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            migrate_all_legacy_tests()
        else:
            migrate_test_file(Path(sys.argv[1]))
    else:
        print(__doc__)
        sys.exit(1)
