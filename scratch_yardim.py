import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\yardim_bekleme.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\yardim_bekleme.py'
]

pattern = r'ping_msg = f"<@&\{YONETIM_EKIBI_ROL\}>"'
new_code = 'ping_msg = f"<@&{YONETIM_EKIBI_ROL}> <@&1553473785527537765>"'

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(pattern, new_code, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    except Exception as e:
        print(e)
