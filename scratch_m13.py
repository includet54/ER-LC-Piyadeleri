import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\uyari_sistemi.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\uyari_sistemi.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find M12 and insert M13
        pattern = r'("M12":.*?)\n\s*# Kategori 2: Sunucu Düzeni'
        replacement = r'\1\n    "M13": {"puan": 0,  "aciklama": "Sunucuda yapılan etkinliklerde ve kapışmalarda 3. Taraf yazılım kullanmak.", "ozel": "timeout_1gun"},\n    # Kategori 2: Sunucu Düzeni'
        
        # If encoding matches regex pattern properly
        if '"M13"' not in content:
            new_content = re.sub(r'("M12":.*?)\n\s*# Kategori 2', r'\1\n    "M13": {"puan": 0,  "aciklama": "Sunucuda yapılan etkinliklerde ve kapışmalarda 3. Taraf yazılım kullanmak.", "ozel": "timeout_1gun"},\n    # Kategori 2', content, flags=re.DOTALL)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Added M13 to {file_path}")
        else:
            print(f"M13 already exists in {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
