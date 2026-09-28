import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\yardim_bekleme.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\yardim_bekleme.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the problematic bot.add_view line
        content = re.sub(r'bot\.add_view\(DestekAktifView\(.*?\)\)', '# bot.add_view(DestekAktifView(...) removed to fix cog loading', content)

        # Also add custom_id to the button just in case
        content = content.replace(
            '@discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success, emoji="✅")',
            '@discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success, emoji="✅", custom_id="destek_bitir_btn")'
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")

    except Exception as e:
        print(e)
