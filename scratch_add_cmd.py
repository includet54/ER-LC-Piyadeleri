import re

with open('cogs/cete_sistemi.py', 'r', encoding='utf-8') as f:
    content = f.read()

insert_str = '''
    @app_commands.command(name="cete-panel-gonder", description="Yetkili çete yönetim panelini gönderir.")
    @app_commands.default_permissions(administrator=True)
    async def cete_panel_gonder(self, interaction: discord.Interaction):
        await interaction.response.send_message("Panel güncelleniyor...", ephemeral=True)
        await update_admin_gang_panel(interaction.client)
'''

idx = content.find('class CeteSistemi(commands.Cog):')
if idx != -1:
    uye_idx = content.find('def uye_cikar', idx)
    if uye_idx != -1:
        decorator_idx = content.rfind('@app_commands', idx, uye_idx)
        if decorator_idx != -1:
            new_content = content[:decorator_idx] + insert_str + content[decorator_idx:]
            with open('cogs/cete_sistemi.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print('Command added!')
        else:
            print('Decorator not found')
    else:
        print('uye_cikar not found')
else:
    print('class CeteSistemi not found')
