import os
import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\main.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\main.py'
]

for file_path in file_paths:
    if not os.path.exists(file_path): continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the import line
    content = re.sub(r'from cogs\.market import.*?\n', '', content)
    
    # Remove the add_view lines
    content = re.sub(r'self\.add_view\(MarketView\(\)\)\n?', '', content)
    content = re.sub(r'self\.add_view\(TotemView\(\)\)\n?', '', content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Removed market references from {file_path}")
