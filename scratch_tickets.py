import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\tickets.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\tickets.py'
]

pattern = r'YETKILI_ROL_IDLERI = \[\s*1529546007635824680,.*?\s*1539167256246747186,.*?\s*1534798061845483694,.*?\s*1537934087166369812,.*?\s*\]'

new_code = """YETKILI_ROL_IDLERI = [
    1553333289798869032,  # TICKET YETKILISI
]"""

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(pattern, new_code, content, flags=re.DOTALL)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    except Exception as e:
        print(e)
