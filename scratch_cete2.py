import os
import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\cete_sistemi.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\cete_sistemi.py'
]

old_message = 'return await interaction.response.send_message("❌ Geçersiz parsel kodu! Geçerli kodlar: 700, 701, 702, 703, 1104, 1108, 1101, 601, 602, 600, 805, 807, 809, 1003, 1004, 1005, 1006, 1007, 1008, 1009 ve .PNG içerisindeki yazılı parsel kodları.", ephemeral=True)'
new_message = 'return await interaction.response.send_message("❌ Geçersiz parsel kodu! Geçerli kodlar: 700, 701, 702, 703, 1104, 1108, 1101, 601, 602, 600, 805, 807, 809, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 403, 404, 405, 406, 407, 409, 410, 411", ephemeral=True)'

for file_path in file_paths:
    if not os.path.exists(file_path): continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace(old_message, new_message)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated error message in {file_path}")
