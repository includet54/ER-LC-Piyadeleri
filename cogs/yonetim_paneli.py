import discord
from discord.ext import commands
from discord import app_commands

# YETKİLİ ROLLERİ (KİM KULLANABİLİR)
KURUCU_ROL_ID = 1529546007635824680
UST_YONETIM_ROL_ID = 1539167256246747186

# VERİLECEK ROLLER
TRIAL_STAFF_ID = 1551241468985737376
STAFF_ID = 1551241634094645288
SENIOR_STAFF_ID = 1551241753137254611
WHITELIST_YETKILISI_ID = 1551242344190189718
MESAJ_DENETIMCISI_ID = 1542249243702726796
SES_KANALI_YETKILISI_ID = 1547526649459777556
TAKMA_AD_YETKILISI_ID = 1543075759508164659

TICKET_YETKILISI_ID = 1553333289798869032
KAPISMA_TALEP_YETKILISI_ID = 1553427352044707840
DESTEK_BEKLEME_YETKILISI_ID = 1553473785527537765

def paneli_kullanabilir_mi(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(rol.id in [KURUCU_ROL_ID, UST_YONETIM_ROL_ID] for rol in member.roles)

class YonetimUserSelect(discord.ui.UserSelect):
    def __init__(self, islem_turu: str):
        super().__init__(placeholder="Lütfen işlem yapılacak kullanıcıyı seçin", min_values=1, max_values=1)
        self.islem_turu = islem_turu

    async def callback(self, interaction: discord.Interaction):
        hedef_uye = self.values[0]
        guild = interaction.guild

        if not isinstance(hedef_uye, discord.Member):
            return await interaction.response.send_message("❌ Lütfen sunucuda bulunan geçerli bir üyeyi seçin.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # Roller
        trial_rol = guild.get_role(TRIAL_STAFF_ID)
        staff_rol = guild.get_role(STAFF_ID)
        senior_rol = guild.get_role(SENIOR_STAFF_ID)
        wl_rol = guild.get_role(WHITELIST_YETKILISI_ID)
        mesaj_rol = guild.get_role(MESAJ_DENETIMCISI_ID)
        ses_rol = guild.get_role(SES_KANALI_YETKILISI_ID)
        takma_ad_rol = guild.get_role(TAKMA_AD_YETKILISI_ID)
        ticket_yetk_rol = guild.get_role(TICKET_YETKILISI_ID)
        kapisma_yetk_rol = guild.get_role(KAPISMA_TALEP_YETKILISI_ID)
        destek_bekleme_rol = guild.get_role(DESTEK_BEKLEME_YETKILISI_ID)

        uye_rol_idleri = [r.id for r in hedef_uye.roles]
        
        has_staff_base = any(rid in uye_rol_idleri for rid in [TRIAL_STAFF_ID, STAFF_ID, SENIOR_STAFF_ID])

        mesaj = ""

        try:
            if self.islem_turu == "trial":
                if trial_rol: await hedef_uye.add_roles(trial_rol)
                if wl_rol: await hedef_uye.add_roles(wl_rol)
                if ticket_yetk_rol: await hedef_uye.add_roles(ticket_yetk_rol)
                if kapisma_yetk_rol: await hedef_uye.add_roles(kapisma_yetk_rol)
                mesaj = f"✅  {hedef_uye.mention} başarıyla **Trial Staff**, **Whitelist Yetkilisi**, **Ticket Yetkilisi** ve **Kapışma Talep Yetkilisi** yapıldı."

            elif self.islem_turu == "staff":
                if TRIAL_STAFF_ID not in uye_rol_idleri:
                    return await interaction.followup.send("❌ Bu kişiye **Staff** verebilmek için üzerinde **Trial Staff** rolü olması ZORUNLUDUR!", ephemeral=True)
                if staff_rol: await hedef_uye.add_roles(staff_rol)
                if trial_rol: await hedef_uye.remove_roles(trial_rol)
                if destek_bekleme_rol: await hedef_uye.add_roles(destek_bekleme_rol)
                mesaj = f"✅  {hedef_uye.mention} başarıyla **Staff** ve **Destek Bekleme Yetkilisi** yapıldı (Trial Staff alındı)."

            elif self.islem_turu == "senior":
                if STAFF_ID not in uye_rol_idleri:
                    return await interaction.followup.send("❌ Bu kişiye **Senior Staff** verebilmek için üzerinde **Staff** rolü olması ZORUNLUDUR!", ephemeral=True)
                if senior_rol: await hedef_uye.add_roles(senior_rol)
                if staff_rol: await hedef_uye.remove_roles(staff_rol)
                mesaj = f"✅ {hedef_uye.mention} başarıyla **Senior Staff** yapıldı (Staff alındı)."

            elif self.islem_turu == "mesaj":
                if not has_staff_base:
                    return await interaction.followup.send("❌ Bu rolü alacak kişinin Staff rollerinden birine (Trial Staff, Staff, Senior Staff) sahip olması ZORUNLUDUR!", ephemeral=True)
                if mesaj_rol: await hedef_uye.add_roles(mesaj_rol)
                mesaj = f"✅ {hedef_uye.mention} başarıyla **Mesaj Denetimcisi** yapıldı."

            elif self.islem_turu == "ses":
                if not has_staff_base:
                    return await interaction.followup.send("❌ Bu rolü alacak kişinin Staff rollerinden birine (Trial Staff, Staff, Senior Staff) sahip olması ZORUNLUDUR!", ephemeral=True)
                if ses_rol: await hedef_uye.add_roles(ses_rol)
                mesaj = f"✅ {hedef_uye.mention} başarıyla **Ses Kanalı Yetkilisi** yapıldı."

            elif self.islem_turu == "takma_ad":
                if not has_staff_base:
                    return await interaction.followup.send("❌ Bu rolü alacak kişinin Staff rollerinden birine (Trial Staff, Staff, Senior Staff) sahip olması ZORUNLUDUR!", ephemeral=True)
                if takma_ad_rol: await hedef_uye.add_roles(takma_ad_rol)
                mesaj = f"✅ {hedef_uye.mention} başarıyla **Takma Ad Yetkilisi** yapıldı."

            await interaction.followup.send(mesaj, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Botun bu rolleri verme/alma yetkisi yok (Botun rolü, verilecek rolden daha üstte olmalı).", ephemeral=True)

class YonetimSelectView(discord.ui.View):
    def __init__(self, islem_turu: str):
        super().__init__(timeout=120)
        self.add_item(YonetimUserSelect(islem_turu))

class YonetimButonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Trial Staff", style=discord.ButtonStyle.primary, custom_id="ybtn_trial")
    async def btn_trial(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Trial Staff** yapılacak kişiyi seçin:", view=YonetimSelectView("trial"), ephemeral=True)

    @discord.ui.button(label="Staff", style=discord.ButtonStyle.primary, custom_id="ybtn_staff")
    async def btn_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Staff** yapılacak kişiyi seçin:", view=YonetimSelectView("staff"), ephemeral=True)

    @discord.ui.button(label="Senior Staff", style=discord.ButtonStyle.primary, custom_id="ybtn_senior")
    async def btn_senior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Senior Staff** yapılacak kişiyi seçin:", view=YonetimSelectView("senior"), ephemeral=True)

    @discord.ui.button(label="Mesaj Denetimcisi", style=discord.ButtonStyle.secondary, custom_id="ybtn_mesaj")
    async def btn_mesaj(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Mesaj Denetimcisi** yapılacak kişiyi seçin:", view=YonetimSelectView("mesaj"), ephemeral=True)

    @discord.ui.button(label="Ses Kanalı Yetkilisi", style=discord.ButtonStyle.secondary, custom_id="ybtn_ses")
    async def btn_ses(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Ses Kanalı Yetkilisi** yapılacak kişiyi seçin:", view=YonetimSelectView("ses"), ephemeral=True)

    @discord.ui.button(label="Takma Ad Yetkilisi", style=discord.ButtonStyle.secondary, custom_id="ybtn_takma_ad")
    async def btn_takma_ad(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu paneli kullanma yetkiniz yok.", ephemeral=True)
        await interaction.response.send_message("Lütfen **Takma Ad Yetkilisi** yapılacak kişiyi seçin:", view=YonetimSelectView("takma_ad"), ephemeral=True)


class YonetimPaneli(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="yonetim-panel", description="Yönetim kadro belirleme panelini gönderir.")
    async def yonetim_panel(self, interaction: discord.Interaction):
        if not discord.utils.get(interaction.user.roles, id=1529546007635824680):
            return await interaction.response.send_message("❌ Bu komutu sadece **Kurucu** kullanabilir!", ephemeral=True)

        if not paneli_kullanabilir_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu komutu kullanma yetkiniz yok.", ephemeral=True)

        desc = (
            "Lütfen terfi ettirmek istediğiniz rütbenin butonuna basın, ardından açılacak menüden kullanıcıyı seçin.\n\n"
            "🔸 **Trial Staff:** Seçilen kişiye Trial Staff, Registration Manager (Whitelist Yetkilisi), Ticket Yetkilisi ve Kapışma Talep Yetkilisi verir.\n"
            "🔸 **Staff:** Seçilen kişinin Staff ve Destek Bekleme Yetkilisi olmasını sağlar. *(Trial Staff zorunludur)*.\n"
            "🔸 **Senior Staff:** Seçilen kişinin Senior Staff olmasını sağlar. *(Staff zorunludur)*.\n"
            "🔸 **Mesaj Denetimcisi:** Seçilen kişiye Mesaj Denetimcisi rolü verilir. *(Staff rollerinden biri zorunludur)*.\n"
            "🔸 **Ses Kanalı Yetkilisi:** Seçilen kişiye Ses Kanalı Yetkilisi rolü verilir. *(Staff rollerinden biri zorunludur)*.\n"
            "🔸 **Takma Ad Yetkilisi:** Seçilen kişiye Takma Ad Yetkilisi rolü verilir. *(Staff rollerinden biri zorunludur)*."
        )

        embed = discord.Embed(
            title="Yönetim Kadro Belirleme",
            description=desc,
            color=discord.Color.gold()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        await interaction.channel.send(embed=embed, view=YonetimButonView())
        await interaction.response.send_message("Yönetim paneli gönderildi.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YonetimPaneli(bot))
