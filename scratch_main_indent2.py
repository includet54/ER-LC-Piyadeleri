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

    # Fix indentation
    content = content.replace('                        self.add_view(UyariPanel())', '        self.add_view(UyariPanel())')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed indentation in {file_path}")
