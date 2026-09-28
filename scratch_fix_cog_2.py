import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\yardim_bekleme.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\yardim_bekleme.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = re.sub(r'bot\.add_view\(DevralView\(.*?\)\)', '# bot.add_view(DevralView(...) removed to fix cog loading', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")

    except Exception as e:
        print(e)
