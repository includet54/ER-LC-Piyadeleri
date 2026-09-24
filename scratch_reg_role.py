import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\registration.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\registration.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r"        try:\s+await uye\.add_roles\(\*verilecek_roller, reason=\"Kay(?:ı|)t onayland(?:ı|)\"\)\s+except discord\.Forbidden:\s+pass"
        new_code = """        try:
            await uye.add_roles(*verilecek_roller, reason="Kayıt onaylandı")
        except discord.Forbidden:
            pass

        # Kayıtsız rolünü sil
        kayitsiz_rol = guild.get_role(1542271426386591894)
        if kayitsiz_rol in uye.roles:
            try:
                await uye.remove_roles(kayitsiz_rol, reason="Kayıt tamamlandı")
            except Exception:
                pass"""

        if "1542271426386591894" not in content:
            content = re.sub(pattern, new_code, content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Injected Kayıtsız removal into {file_path}")
        else:
            print(f"Already injected into {file_path}")
    except Exception as e:
        print(f"Error {file_path}: {e}")
