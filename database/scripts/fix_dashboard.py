
import os

file_path = r"c:\Users\deept\OneDrive\Desktop\medical_store_project_Backend\backend\app\routes\dashboard.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first occurrence of `global_search`
first_idx = content.find("def global_search()")
# Find the second (last) occurrence
last_idx = content.rfind("def global_search()")

if first_idx != -1 and first_idx != last_idx:
    # Keep content up to the second definition start (minus the decorator likely above it)
    # The decorator is `@dashboard_bp.route('/api/global_search')`
    # Let's find the decorator
    decorator = "@dashboard_bp.route('/api/global_search')"
    last_decorator_idx = content.rfind(decorator)
    
    if last_decorator_idx != -1:
        new_content = content[:last_decorator_idx]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully removed duplicate global_search")
    else:
        print("Could not find decorator for the second function")
else:
    print("No duplicate global_search found or found only once")
