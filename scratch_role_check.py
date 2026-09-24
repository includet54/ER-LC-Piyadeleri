import os
import re

files_to_check = [
    'cogs/cete_sistemi.py',
    'cogs/registration.py',
    'cogs/rol_secim.py',
    'cogs/tickets.py',
    'cogs/izin_yonetimi.py',
    'cogs/yonetim_paneli.py'
]

funcs = [
    'async def cete_panel_kur(self, interaction: discord.Interaction):',
    'async def kayit_panel(self, interaction: discord.Interaction):',
    'async def rol_paneli_kur(self, interaction: discord.Interaction):',
    'async def ticket_panel(self, interaction: discord.Interaction):',
    'async def izin_paneli_kur(self, interaction: discord.Interaction):',
    'async def yonetim_panel(self, interaction: discord.Interaction):'
]

injection = '''
        if not discord.utils.get(interaction.user.roles, id=1529546007635824680):
            return await interaction.response.send_message("❌ Bu komutu sadece **Kurucu** kullanabilir!", ephemeral=True)
'''

for file_path in files_to_check:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for func in funcs:
        if func in content:
            # check if already injected
            if "id=1529546007635824680" in content.split(func)[1][:200]:
                continue
                
            content = content.replace(func, func + injection)
            modified = True
            print(f"Injected into {file_path} for {func}")
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
