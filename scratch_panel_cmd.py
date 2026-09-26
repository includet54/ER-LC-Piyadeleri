import re

file_path = r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\vs_talep.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# First, remove setup_vs_talep function
content = re.sub(r'async def setup_vs_talep.*?class VSTalepCog\(commands\.Cog\):', 'class VSTalepCog(commands.Cog):', content, flags=re.DOTALL)

# Add command to VSTalepCog
command_str = """
    @app_commands.command(name="vs_talep_panel_kur", description="VS Talep panelini kurar")
    async def vs_talep_panel_kur(self, interaction: discord.Interaction):
        # Yetki kontrolü (sadece Kurucu - 1529546007635824680)
        if not interaction.user.guild_permissions.administrator and not any(rol.id == 1529546007635824680 for rol in interaction.user.roles):
            await interaction.response.send_message("Bu komutu kullanma yetkin yok.", ephemeral=True)
            return

        embed = discord.Embed(
            description=(
                "# PRP | VS Talep\\n\\n"
                "> Hoş geldiniz. Size en iyi ve en hızlı kapışmayı sunabilmemiz için aşağıdaki kurallara dikkat edin.\\n\\n"
                "---\\n\\n"
                "**Kurallar**\\n"
                "> • Gereksiz, trolleme amaçlı veya konu dışı talep açmak yasaktır.\\n"
                "> • Talep açıldıktan sonra 2 gün süresi vardır. Süre dolunca sorgusuz kapanır.\\n"
                "> • Managerlara ya da <@&1553427352044707840>'ne kanıt göstermek zorundasınız.\\n\\n"
                "---\\n\\n"
                "Aşağıdaki butona tıklayarak kişiyi ve uygun kısmı seçerek talep oluşturabilirsiniz."
            ),
            color=0x9B59B6
        )
        embed.set_image(url=VS_LOGO_URL)

        view = VSSetupView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("VS Talep paneli başarıyla kuruldu.", ephemeral=True)
"""

content = content.replace('    @tasks.loop(minutes=30)', command_str + '\n    @tasks.loop(minutes=30)')

# Remove on_ready event in setup function
setup_str = """async def setup(bot: commands.Bot):
    await bot.add_cog(VSTalepCog(bot))"""

content = re.sub(r'async def setup\(bot: commands\.Bot\):.*', setup_str, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modified vs_talep.py successfully.")
