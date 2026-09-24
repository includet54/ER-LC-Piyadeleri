import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

UYARILAR_KANAL_ID = 1532828434739368149
UYARI_1_ROL = 1534715251323572315
UYARI_2_ROL = 1534715383507058749
UYARI_3_ROL = 1534715488716853278
ASKIYA_ALINAN_ROL = 1534715583826759790

SICIL_DATA_FILE = "data/sicil_data.json"

if not os.path.exists("data"):
    os.makedirs("data")

def load_sicil():
    if not os.path.exists(SICIL_DATA_FILE):
        return {}
    with open(SICIL_DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_sicil(data):
    with open(SICIL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_sicil_record(user_id: int, madde: str, aciklama: str, yetkili_id: int, sonuc: str):
    data = load_sicil()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    
    data[uid].append({
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "madde": madde,
        "aciklama": aciklama,
        "yetkili_id": yetkili_id,
        "sonuc": sonuc
    })
    save_sicil(data)

# MADDELER VE VERİLECEK UYARI PUANLARI
MADDELER = {
    "M1": {"puan": 1, "aciklama": "Sunucumuzda küfür/hakarete başvurmak."},
    "M2": {"puan": 1, "aciklama": "Reklam yapmak, hesap/oyun satışı gibi ticari faaliyetlerde bulunmak (Özel mesajda dahil)."},
    "M3": {"puan": 1, "aciklama": "Bir başkasının görüşüne karşı nefret söylemi, hakaret veya küfür etmek."},
    "M4": {"puan": 1, "aciklama": "Cinsiyet fark etmeksizin taciz içeren davranışlarda bulunmak."},
    "M5": {"puan": 1, "aciklama": "Kanalları amacı dışında kullanmak (Örn: #bot-komut'da sohbet etmek)."},
    "M6": {"puan": 1, "aciklama": "Cinsel içerikli herhangi bir paylaşım (görsel, yazı, link) yapmak."},
    "M7": {"puan": 1, "aciklama": "Yetkiliye, muhattap olmak istemediği halde sunucu içinde hakaret etmek veya kavga ortamı yaratmak."},
    "M8": {"puan": 1, "aciklama": "Zorbalık yapmak, başka bir üyeyi sunucudan soğutacak davranışlarda bulunmak."},
    "M9": {"puan": 1, "aciklama": "<@&1529546007635824680> ve <@&1539167256246747186>'in bilgisi dışında sunucu üyelerini kendi sunucunuza veya grubunuza davet etmek."},
    "M10": {"puan": 1, "aciklama": "+18, cinsel taciz, ırkçılık, cinsiyet/yaş ayrımcılığı içeren içerik paylaşmak."},
    "M11": {"puan": 1, "aciklama": "Irkçılık ve her türlü ayrımcılık yapmak."},
    "M12": {"puan": 99, "aciklama": "1 gün içinde en az 2 uyarı almak."},
    "M13": {"puan": 1, "aciklama": "Sunucuda bulunan kişilerin piskolojisini etkileyecek argo, küçümseme ve dalga geçme gibi faliyetler yapmak."},
    "M14": {"puan": 1, "aciklama": "Sunucumuzda düzenlenen etkinliklerde veya yapılacak olan kapışmalarda karşı taraf rahatsız olduğu halde kendini abartı şekilde övmek."},
    "D1": {"puan": 1, "aciklama": "Önemli kanallara (duyuru vb.) anlamsız, boş mesajlar atmak."},
    "D2": {"puan": 1, "aciklama": "Ses kanallarında ses panelini veya sohbet kanalını gereksiz yere çağırmak (spawnlamak)."},
    "D3": {"puan": 1, "aciklama": "Ses kanallarında sürekli yolculuk yaparak gereksiz bildirim yağmuruna sebep olmak."},
    "Y1": {"puan": 99, "aciklama": "Yetkisini kendi lehine kullanmak."},
    "Y2": {"puan": 1, "aciklama": "Sunucudaki katılımcıyı yanlış yönlendirmek."},
    "Y3": {"puan": 1, "aciklama": "Yanlış işlem yapmak.(Örn: Yanlış uyarı vermek)"},
    "Y4": {"puan": 1, "aciklama": "Sunucuda kendini üstün görmek."},
    "Y5": {"puan": 1, "aciklama": "Kendinen üst kademeli yetkililerin yönlendirmesini dinlememek/takmamak."}
}

YETKILI_ROLLERI = [
    1551241753137254611,  # Senior Staff
    1551241634094645288,  # Staff
    1551241468985737376,  # Trial Staff
    1529546007635824680,  # Kurucu
    1539167256246747186,  # Üst Yönetim
    1534798061845483694,  # Yönetici
    1537934087166369812,  # Yönetim ekibi
    1542249243702726796,  # Mesaj Denetimcisi
    1547526649459777556,  # Ses Kanalı yetkilisi
    1543075759508164659   # Takma Ad Yetkilisi
]

YETKILI_UYARI_1 = 1551287340444549191
YETKILI_UYARI_2 = 1551287502667776130
YETKILI_UYARI_3 = 1551287599983755405

SICIL_LOG_KANAL_ID = 1532828404347437287

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
        
        add_sicil_record(
            user_id=self.hedef_kullanici.id,
            madde="SÖZLÜ",
            aciklama=self.sebep.value,
            yetkili_id=interaction.user.id,
            sonuc="Sözlü uyarı verildi (Rol işlemi yok)."
        )
        
        await interaction.response.send_message(f"✅ Sözlü uyarı {self.hedef_kullanici.mention} kişisine başarıyla verildi.", ephemeral=True)


class ResmiUyariModal(discord.ui.Modal, title="Madde Numarası Girin"):
    madde = discord.ui.TextInput(
        label="Madde Numarası (Örn: M1, M2, D1, Y1)",
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
        
        guild = interaction.guild
        verilecek_rol_id = None
        sonuc_metni = ""
        sicil_isleme = False
        yetki_alma_hatasi = False
        
        hedef_yetkili_mi = any(r in YETKILI_ROLLERI for r in roller)
        
        if hedef_yetkili_mi:
            mevcut_seviye = 0
            if YETKILI_UYARI_3 in roller: mevcut_seviye = 3
            elif YETKILI_UYARI_2 in roller: mevcut_seviye = 2
            elif YETKILI_UYARI_1 in roller: mevcut_seviye = 1
            
            yeni_seviye = mevcut_seviye + eklenen_puan
            
            silinecek_uyari_rolleri = [guild.get_role(r) for r in [YETKILI_UYARI_1, YETKILI_UYARI_2, YETKILI_UYARI_3] if guild.get_role(r)]
            uyari_rolleri_sil = [r for r in silinecek_uyari_rolleri if r is not None and r in self.hedef_kullanici.roles]
            if uyari_rolleri_sil:
                try:
                    await self.hedef_kullanici.remove_roles(*uyari_rolleri_sil)
                except discord.Forbidden:
                    pass
            
            if yeni_seviye == 1:
                verilecek_rol_id = YETKILI_UYARI_1
                sonuc_metni = "Yetkili Uyarı 1 rolü verildi."
            elif yeni_seviye == 2:
                verilecek_rol_id = YETKILI_UYARI_2
                sonuc_metni = "Yetkili Uyarı 2 rolü verildi."
            elif yeni_seviye == 3:
                verilecek_rol_id = YETKILI_UYARI_3
                sonuc_metni = "Yetkili Uyarı 3 rolü verildi."
            else:
                silinecek_yetki_rolleri = [guild.get_role(r) for r in YETKILI_ROLLERI if guild.get_role(r)]
                gecerli_silinecekler = [r for r in silinecek_yetki_rolleri if r is not None and r in self.hedef_kullanici.roles]
                
                if gecerli_silinecekler:
                    try:
                        await self.hedef_kullanici.remove_roles(*gecerli_silinecekler, reason="Yetkili Uyarı limitini aştı (Tüm yetkileri alındı).")
                        sonuc_metni = "TÜM YETKİLERİ ALINDI ve normal katılımcı yapıldı."
                    except discord.Forbidden:
                        sonuc_metni = "Yetkiler alınacaktı FAKAT botun rolü bu kişiden daha aşağıda olduğu için yetkileri alınamadı!"
                        yetki_alma_hatasi = True
                else:
                    sonuc_metni = "TÜM YETKİLERİ ALINDI ve normal katılımcı yapıldı."
                    
                verilecek_rol_id = None
                sicil_isleme = not yetki_alma_hatasi
                
        else:
            mevcut_seviye = 0
            if UYARI_3_ROL in roller: mevcut_seviye = 3
            elif UYARI_2_ROL in roller: mevcut_seviye = 2
            elif UYARI_1_ROL in roller: mevcut_seviye = 1
            
            yeni_seviye = mevcut_seviye + eklenen_puan
            
            silinecekler = [guild.get_role(r) for r in [UYARI_1_ROL, UYARI_2_ROL, UYARI_3_ROL] if guild.get_role(r)]
            await self.hedef_kullanici.remove_roles(*[r for r in silinecekler if r is not None])
            
            if yeni_seviye == 1:
                verilecek_rol_id = UYARI_1_ROL
                sonuc_metni = "UYARI 1 rolü verildi."
            elif yeni_seviye == 2:
                verilecek_rol_id = UYARI_2_ROL
                sonuc_metni = "UYARI 2 rolü verildi."
            elif yeni_seviye == 3:
                verilecek_rol_id = UYARI_3_ROL
                sonuc_metni = "UYARI 3 rolü verildi."
            else:
                silinecek_roller = [rol for rol in self.hedef_kullanici.roles if rol.id != guild.id and not rol.is_integration() and not rol.is_premium_subscriber()]
                try:
                    await self.hedef_kullanici.remove_roles(*silinecek_roller, reason="Askıya alındığı için tüm roller temizlendi")
                except discord.Forbidden:
                    pass
                verilecek_rol_id = ASKIYA_ALINAN_ROL
                sonuc_metni = "TÜM ROLLERİ ALINDI ve ASKIYA ALINAN ELEMAN rolü verildi."
                
        if verilecek_rol_id:
            verilecek_rol = guild.get_role(verilecek_rol_id)
            if verilecek_rol:
                try:
                    await self.hedef_kullanici.add_roles(verilecek_rol)
                except discord.Forbidden:
                    pass
                
        # Log Kanalına Gönder (Genel)
        kanal = interaction.guild.get_channel(UYARILAR_KANAL_ID)
        embed = discord.Embed(title="🚨 Resmi Uyarı Verildi!", color=discord.Color.red())
        embed.add_field(name="Uyarı Alan", value=self.hedef_kullanici.mention, inline=True)
        embed.add_field(name="İşlem Yapan", value=interaction.user.mention, inline=True)
        embed.add_field(name="Madde / İhlal", value=f"**{madde_kodu}** - {bilgi['aciklama']}", inline=False)
        embed.add_field(name="Sonuç", value=sonuc_metni, inline=False)
        
        if kanal:
            await kanal.send(content=f"{self.hedef_kullanici.mention}", embed=embed)
            
        # Sicil Logu (Sadece yetkiler alınırsa)
        if sicil_isleme:
            sicil_kanal = interaction.guild.get_channel(SICIL_LOG_KANAL_ID)
            if sicil_kanal:
                sicil_embed = discord.Embed(title="📜 Yetkili Siciline İşlendi - YETKİSİ ALINDI", color=discord.Color.dark_red())
                sicil_embed.add_field(name="Eski Yetkili", value=self.hedef_kullanici.mention, inline=True)
                sicil_embed.add_field(name="İşlem Yapan", value=interaction.user.mention, inline=True)
                sicil_embed.add_field(name="Son İhlal / Madde", value=f"**{madde_kodu}** - {bilgi['aciklama']}", inline=False)
                sicil_embed.add_field(name="Detay", value="Yetkili Uyarı sınırını aştığı için tüm yetki rolleri kalıcı olarak alındı ve normal katılımcıya çevrildi.", inline=False)
                sicil_embed.timestamp = discord.utils.utcnow()
                await sicil_kanal.send(embed=sicil_embed)
                
        # Sicil veri dosyasına kayıt ekle
        add_sicil_record(
            user_id=self.hedef_kullanici.id,
            madde=madde_kodu,
            aciklama=bilgi['aciklama'],
            yetkili_id=interaction.user.id,
            sonuc=sonuc_metni
        )
            
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

    def yonetim_mi(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator:
            return True
        return any(rol.id in [1529546007635824680, 1539167256246747186] for rol in member.roles)

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

    @app_commands.command(name="sicil-gor", description="Bir kullanıcının geçmiş uyarı sicilini gösterir.")
    @app_commands.describe(kisi="Sicili görüntülenecek kişi")
    async def sicil_gor(self, interaction: discord.Interaction, kisi: discord.Member):
        if not self.yonetim_mi(interaction.user):
            return await interaction.response.send_message("❌ Bu komutu sadece Kurucu veya Üst Yönetim kullanabilir.", ephemeral=True)
            
        data = load_sicil()
        uid = str(kisi.id)
        
        if uid not in data or len(data[uid]) == 0:
            return await interaction.response.send_message(f"✅ {kisi.mention} kişisinin sicili tamamen temiz. Hiç uyarısı yok.", ephemeral=True)
            
        kayitlar = data[uid]
        
        embed = discord.Embed(
            title=f"📜 {kisi.display_name} - Sicil Kaydı",
            description=f"Bu kullanıcının toplam **{len(kayitlar)}** adet ihlali bulunuyor.",
            color=discord.Color.dark_theme()
        )
        embed.set_thumbnail(url=kisi.display_avatar.url)
        
        for idx, kayit in enumerate(kayitlar, 1):
            tarih = kayit.get("tarih", "Bilinmeyen Tarih")
            madde = kayit.get("madde", "?")
            aciklama = kayit.get("aciklama", "Belirtilmemiş")
            yetkili_id = kayit.get("yetkili_id", 0)
            sonuc = kayit.get("sonuc", "Bilinmiyor")
            
            detay = (
                f"**Tarih:** {tarih}\n"
                f"**Uyarı Veren:** <@{yetkili_id}>\n"
                f"**Açıklama:** {aciklama}\n"
                f"**Sonuç:** {sonuc}"
            )
            embed.add_field(name=f"{idx}. İhlal (Madde: {madde})", value=detay, inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(UyariSistemi(bot))
