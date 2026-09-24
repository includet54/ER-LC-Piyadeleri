import os

files = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\vs_talep.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\vs_talep.py'
]

injection = """        # Zaten açık bir talebi olup olmadığını kontrol et
        kategori = guild.get_channel(VS_KATEGORI_ID)
        if kategori:
            for channel in kategori.text_channels:
                rid, vid, vtype = parse_channel_topic(channel)
                if rid == requester.id:
                    await interaction.followup.send("❌ Zaten açık bir VS talebiniz bulunuyor. Mevcut kanalınız kapanmadan yenisini açamazsınız!", ephemeral=True)
                    return

        # Kanal ismi"""

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the channel_name line with the check and the channel_name line
        if "# Kanal ismi" in content and "Zaten açık bir talebi olup olmadığını kontrol et" not in content:
            content = content.replace("        # Kanal ismi", injection)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Injected check into {file_path}")
