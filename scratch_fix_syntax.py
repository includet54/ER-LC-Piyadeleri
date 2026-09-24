import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\cete_sistemi.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\cete_sistemi.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the bad backslash escaping
        content = content.replace(r'f\"🎉', 'f"🎉')
        content = content.replace(r'atabilirsiniz.\",', 'atabilirsiniz.",')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")
    except Exception as e:
        print(e)
