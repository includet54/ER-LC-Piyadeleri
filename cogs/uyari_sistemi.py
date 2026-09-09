import discord
from discord.ext import commands
from discord import app_commands

UYARILAR_KANAL_ID = 1532828434739368149
UYARI_1_ROL = 1534715251323572315
UYARI_2_ROL = 1534715383507058749
UYARI_3_ROL = 1534715488716853278
ASKIYA_ALINAN_ROL = 1534715583826759790

# MADDELER VE VERİLECEK UYARI PUANLARI
MADDELER = {
    "M1": {"puan": 1, "aciklama": "Karşıdaki kişi rahatsız olduğu halde küfür/hakarete devam etmek."},
    "M2": {"puan": 2, "aciklama": "Reklam yapmak, hesap/oyun satışı gibi ticari faaliyetlerde bulunmak."},
    "M3": {"puan": 1, "aciklama": "Bir başkasının görüşüne karşı nefret söylemi, hakaret veya küfür etmek."},
    "M4": {"puan": 1, "aciklama": "Cinsiyet fark etmeksizin taciz içeren davranışlarda bulunmak."},
    "M5": {"puan": 1, "aciklama": "Kanalları amacı dışında kullanmak."},
    "M6": {"puan": 1, "aciklama": "Cinsel içerikli herhangi bir paylaşım yapmak."},
    "M7": {"puan": 1, "aciklama": "Yetkiliye veya üyeye muhattap olmak istemediği halde hakaret etmek."},
    "M8": {"puan": 1, "aciklama": "Zorbalık yapmak, üyeyi sunucudan soğutacak davranışlarda bulunmak."},
    "M9": {"puan": 2, "aciklama": "Sunucu üyelerini kendi sunucunuza davet etmek."},
    "M10": {"puan": 1, "aciklama": "+18, cinsel taciz, ırkçılık, cinsiyet/yaş ayrımcılığı içeren içerik paylaşmak."},
    "M11": {"puan": 1, "aciklama": "Irkçılık ve her türlü ayrımcılık yapmak."},
    "M12": {"puan": 99, "aciklama": "1 gün içinde en az 2 uyarı almak (DOĞRUDAN ASKIYA ALINMA)."},
    "D1": {"puan": 1, "aciklama": "Önemli kanallara (duyuru vb.) anlamsız, boş mesajlar atmak."},
    "D2": {"puan": 1, "aciklama": "Ses kanallarında ses panelini veya sohbet kanalını gereksiz yere çağırmak."},
    "D3": {"puan": 1, "aciklama": "Ses kanallarında sürekli yolculuk yaparak gereksiz bildirim yağmuruna sebep olmak."}
}

class SozluUyariModal(discord.ui.Modal, title="Sözlü Uyarı Sebebi"):
    sebep = discord.ui.TextInput(
        label="Uyarı Sebebini Yazın",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Ses kanalında yüksek sesle konuşmak...",
        required=True
    )
    
    def __init__(self, hedef_kullanici: discord.Member):
        super().__init__()
        self.hedef_kullanici = hedef_kullanici

    async def on_submit(self, interaction: discord.Interaction):
        kanal = interaction.guild.get_channel(UYARILAR_KANAL_ID)
        embed = discord.Embed(title="⚠️ Sözlü Uyarı!", color=discord.Color.orange())
        embed.add_field(name="Uyarı Alan", value=self.hedef_kullanici.mention, inline=True)
        embed.add_field(name="İşlem Yapan", value=interaction.user.mention, inline=True)
        embed.add_field(name="İhlal / Sebep", value=self.sebep.value, inline=False)
        
        await kanal.send(content=f"{self.hedef_kullanici.mention}", embed=embed)
        await interaction.response.send_message(f"✅ Sözlü uyarı {self.hedef_kullanici.mention} kişisine başarıyla verildi.", ephemeral=True)


class ResmiUyariModal(discord.ui.Modal, title="Madde Numarası Girin"):
    madde = discord.ui.TextInput(
        label="Madde Numarası (Örn: M1, M2, D1)",
        style=discord.TextStyle.short,
        placeholder="M1",
        required=True
    )

    def __init__(self, hedef_kullanici: discord.Member):
        super().__init__()
        self.hedef_kullanici = hedef_kullanici

    async def on_submit(self, interaction: discord.Interaction):
        madde_kodu = self.madde.value.strip().upper()
        
        if madde_kodu not in MADDELER:
            return await interaction.response.send_message("❌ Girdiğiniz madde numarası sistemde bulunamadı. Lütfen geçerli bir madde numarası girin.", ephemeral=True)
        
        bilgi = MADDELER[madde_kodu]
        eklenen_puan = bilgi["puan"]
        
        roller = [r.id for r in self.hedef_kullanici.roles]
        
        # Mevcut uyarı seviyesini tespit et
        mevcut_seviye = 0
        if UYARI_3_ROL in roller: mevcut_seviye = 3
        elif UYARI_2_ROL in roller: mevcut_seviye = 2
        elif UYARI_1_ROL in roller: mevcut_seviye = 1
        
        yeni_seviye = mevcut_seviye + eklenen_puan
        
        guild = interaction.guild
        verilecek_rol_id = None
        sonuc_metni = ""
        
        if yeni_seviye == 1:
            silinecekler = [guild.get_role(r) for r in [UYARI_1_ROL, UYARI_2_ROL, UYARI_3_ROL] if guild.get_role(r)]
            await self.hedef_kullanici.remove_roles(*[r for r in silinecekler if r is not None])
            verilecek_rol_id = UYARI_1_ROL
            sonuc_metni = "UYARI 1 rolü verildi."
        elif yeni_seviye == 2:
            silinecekler = [guild.get_role(r) for r in [UYARI_1_ROL, UYARI_2_ROL, UYARI_3_ROL] if guild.get_role(r)]
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
            description="**Yapmanız Gerekenler :**
"
                        "-> Uyarı alacak kişiyi seç.
"
                        "-> Karşına çıkan madde numarasını doldur.
"
                        "-> [Sunucu Uyarı Verme Maddeleri](https://canva.link/ma7hw7a6ex9lmmw)
",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed, view=UyariPanel())
        await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UyariSistemi(bot))
