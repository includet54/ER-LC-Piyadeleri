 in [UYARI_1_ROL, UYARI_2_ROL, UYARI_3_ROL] if guild.get_role(r)]
            await self.hedef_kullanici.remove_roles(*[r for r in silinecekler if r is not None])
            verilecek_rol_id = UYARI_2_ROL
            sonuc_metni = "UYARI 2 rolü verildi."
        elif yeni_seviye == 3:
            silinecekler = [guild.get_role(r) for r in [UYARI_1_ROL, UYARI_2_ROL, UYARI_3_ROL] if guild.get_role(r)]
            await self.hedef_kullanici.remove_roles(*[r for r in silinecekler if r is not None])
            verilecek_rol_id = UYARI_3_ROL
            sonuc_metni = "UYARI 3 rolü verildi."
        else: # 4 veya daha fazla, ASKIYA ALINAN
            # Tum rolleri sil
            silinecek_roller = [rol for rol in self.hedef_kullanici.roles if rol.id != guild.id and not rol.is_integration() and not rol.is_premium_subscriber()]
            try:
                await self.hedef_kullanici.remove_roles(*silinecek_roller, reason="Askıya alındığı için tüm roller temizlendi")
            except discord.Forbidden:
                pass # Bazi rolleri (or. botun kendinden ustte olanlari) silemeyebilir
            verilecek_rol_id = ASKIYA_ALINAN_ROL
            sonuc_metni = "TÜM ROLLERİ ALINDI ve ASKIYA ALINAN ELEMAN rolü verildi."
            
        verilecek_rol = guild.get_role(verilecek_rol_id)
        if verilecek_rol:
            try:
                await self.hedef_kullanici.add_roles(verilecek_rol)
            except discord.Forbidden:
                pass
            
        # Log Kanalına Gönder
        kanal = interaction.guild.get_channel(UYARILAR_KANAL_ID)
        embed = discord.Embed(title="🚨 Resmi Uyarı Verildi!", color=discord.Color.red())
        embed.add_field(name="Uyarı Alan", value=self.hedef_kullanici.mention, inline=True)
        embed.add_field(name="İşlem Yapan", value=interaction.user.mention, inline=True)
        embed.add_field(name="Madde / İhlal", value=f"**{madde_kodu}** - {bilgi['aciklama']}", inline=False)
        embed.add_field(name="Sonuç", value=sonuc_metni, inline=False)
        
        if kanal:
            await kanal.send(content=f"{self.hedef_kullanici.mention}", embed=embed)
        await interaction.response.send_message(f"✅ Uyarı başarıyla işlendi ve {sonuc_metni}", ephemeral=True)


# Seçim Menüleri
class KullaniciSecView_Sozlu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Sözlü uyarı verilecek kişiyi seçin")
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        kullanici = select.values[0]
        if isinstance(kullanici, discord.Member):
            await interaction.response.send_modal(SozluUyariModal(kullanici))
        else:
            await interaction.response.send_message("Lütfen sunucudaki bir üyeyi seçin.", ephemeral=True)

class KullaniciSecView_Resmi(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Uyarı verilecek kişiyi seçin")
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        kullanici = select.values[0]
        if isinstance(kullanici, discord.Member):
            await interaction.response.send_modal(ResmiUyariModal(kullanici))
        else:
            await interaction.response.send_message("Lütfen sunucudaki bir üyeyi seçin.", ephemeral=True)


class UyariPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sözlü Uyarı ver", style=discord.ButtonStyle.secondary, custom_id="sozlu_uyari_btn")
    async def sozlu_uyari(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kimi uyarmak istiyorsunuz?", view=KullaniciSecView_Sozlu(), ephemeral=True)

    @discord.ui.button(label="Uyarı Ver", style=discord.ButtonStyle.danger, custom_id="resmi_uyari_btn")
    async def resmi_uyari(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kime uyarı vermek istiyorsunuz?", view=KullaniciSecView_Resmi(), ephemeral=True)


class UyariSistemi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="uyari-panel", description="Uyarı panelini kanala gönderir.")
    @app_commands.default_permissions(administrator=True)
    async def uyari_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Sunucu Uyarı Paneli",
            description="""**Yapmanız Gerekenler :**
-> Uyarı alacak kişiyi seç.
-> Karşına çıkan madde numarasını doldur.
-> [Sunucu Uyarı Verme Maddeleri](https://canva.link/ma7hw7a6ex9lmmw)""",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed, view=UyariPanel())
        await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UyariSistemi(bot))
