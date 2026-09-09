import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime

# ============================
MODERATOR_LOG_KANALI = 1532828404347437287
YARDIM_SES_KANALI_ID = 123456789012345678  # <--- BİRİSİ GİRDİĞİNDE PANELİN DÜŞMESİ İÇİN KENDİ SES KANALININ ID'SİNİ BURAYA YAZ
DATA_FILE = "data/mod_stats.json"
GUNLUK_HEDEF_SANIYE = 5 * 60 * 60  # 5 saat
# ============================

def load_stats():
    if not os.path.exists("data"): os.makedirs("data")
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_stats(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def update_mod_stat(mod_id, key, amount=1):
    data = load_stats()
    mod_id = str(mod_id)
    if mod_id not in data: data[mod_id] = {"voice_time": 0, "supports": 0, "tickets": 0}
    data[mod_id][key] += amount
    save_stats(data)

def progress_bar(current, total, length=15):
    progress = min(1.0, current / total)
    filled = int(length * progress)
    return "█" * filled + "░" * (length - filled)


class DestekBitirModal(discord.ui.Modal, title="Desteği Sonlandır"):
    sonuc = discord.ui.TextInput(
        label="Desteği Bitir Anketi Nasıl Sonuçlandı?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Sorunu çözüldü, kurallar anlatıldı.",
        required=True
    )

    def __init__(self, baslangic_zamani: datetime.datetime, yardim_isteyen_id: int, original_message: discord.Message):
        super().__init__()
        self.baslangic_zamani = baslangic_zamani
        self.yardim_isteyen_id = yardim_isteyen_id
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bitis_zamani = discord.utils.utcnow()
        fark = bitis_zamani - self.baslangic_zamani
        dakika = int(fark.total_seconds() // 60)
        saniye = int(fark.total_seconds() % 60)
        sure_metni = f"{dakika} dk {saniye} sn"

        update_mod_stat(interaction.user.id, "supports", 1)

        embed = self.original_message.embeds[0] if self.original_message.embeds else discord.Embed(title="✅ Destek Sonlandırıldı")
        embed.color = discord.Color.green()
        embed.add_field(name="İlgilenen Yetkili", value=interaction.user.mention, inline=True)
        embed.add_field(name="Destek Süresi", value=sure_metni, inline=True)
        embed.add_field(name="Anket Sonucu", value=self.sonuc.value, inline=False)
        
        await self.original_message.edit(embed=embed, view=None)
        await interaction.followup.send("Destek başarıyla sonlandırıldı ve log kanalına iletildi.", ephemeral=True)


class DestekAktifView(discord.ui.View):
    def __init__(self, baslangic_zamani: datetime.datetime, yardim_isteyen_id: int):
        super().__init__(timeout=None)
        self.baslangic_zamani = baslangic_zamani
        self.yardim_isteyen_id = yardim_isteyen_id

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success)
    async def bitir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DestekBitirModal(self.baslangic_zamani, self.yardim_isteyen_id, interaction.message))

    @discord.ui.button(label="Boş", style=discord.ButtonStyle.secondary)
    async def bos_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        yeni_icerik = interaction.message.content + " (Boş Çıktı)"
        await interaction.message.edit(content=yeni_icerik, view=None)
        await interaction.followup.send("Kullanıcı boş çıktığı için destek iptal edildi.", ephemeral=True)


class DevralView(discord.ui.View):
    def __init__(self, yardim_isteyen_id: int):
        super().__init__(timeout=None)
        self.yardim_isteyen_id = yardim_isteyen_id

    @discord.ui.button(label="Devral", style=discord.ButtonStyle.success, emoji="✅")
    async def devral_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        yeni_icerik = f"✅ {interaction.user.mention} tarafından devralındı."
        await interaction.message.edit(
            content=yeni_icerik, 
            view=DestekAktifView(discord.utils.utcnow(), self.yardim_isteyen_id)
        )


class YardimBekleme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_voice_sessions = {}
        self.gunluk_rapor.start()

    def cog_unload(self):
        self.gunluk_rapor.cancel()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return

        # 1. GÜNLÜK SES AKTİFLİĞİ (Tüm ses kanalları için XP / süre sayacı)
        if before.channel is None and after.channel is not None:
            self.active_voice_sessions[member.id] = discord.utils.utcnow()
        elif before.channel is not None and after.channel is None:
            if member.id in self.active_voice_sessions:
                join_time = self.active_voice_sessions.pop(member.id)
                fark = (discord.utils.utcnow() - join_time).total_seconds()
                update_mod_stat(member.id, "voice_time", fark)

        # 2. YARDIM BEKLEME BİLDİRİM PANELİ (Resimdeki gibi otomatik düşme)
        if after.channel and after.channel.id == YARDIM_SES_KANALI_ID and (before.channel is None or before.channel.id != YARDIM_SES_KANALI_ID):
            kanal = self.bot.get_channel(MODERATOR_LOG_KANALI)
            if not kanal: return
            
            embed = discord.Embed(title="🆘 Yardım Bekleme", color=discord.Color.dark_theme())
            embed.description = f"{member.mention} **Yardım Bekleme** kanalına girdi."
            embed.timestamp = discord.utils.utcnow()
            
            ping_msg = "<@&1529546007635824680> <@&1539167256246747186> <@&1534798061845483694>"
            await kanal.send(content=ping_msg, embed=embed, view=DevralView(member.id))

    # Türkiye saatiyle gece 00:00 (UTC 21:00) 
    @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=datetime.timezone.utc))
    async def gunluk_rapor(self):
        await self.bot.wait_until_ready()
        kanal = self.bot.get_channel(MODERATOR_LOG_KANALI)
        if not kanal: return

        data = load_stats()
        if not data:
            return await kanal.send("📊 **Günün Özeti:** Bugün hiçbir veri kaydedilmedi.")

        embed = discord.Embed(title="📊 Günlük Yetkili İstatistikleri", description="Günün analizi ve sıralama tablosu. Veriler sıfırlanıyor...", color=discord.Color.blue())
        
        for mod_id, stat in sorted(data.items(), key=lambda x: x[1]["voice_time"], reverse=True):
            user = self.bot.get_user(int(mod_id))
            if not user: continue
            
            toplam_saniye = stat["voice_time"]
            saat = int(toplam_saniye // 3600)
            dak = int((toplam_saniye % 3600) // 60)
            bar = progress_bar(toplam_saniye, GUNLUK_HEDEF_SANIYE)
            hedef_durum = "✅ Tamamlandı" if toplam_saniye >= GUNLUK_HEDEF_SANIYE else "❌ Eksik"

            aciklama = (
                f"**Ses Süresi:** {saat}s {dak}dk\n"
                f"**İlerleme:** `{bar}` ({hedef_durum})\n"
                f"**Baktığı Destek:** {stat['supports']}\n"
                f"**Baktığı Bilet:** {stat['tickets']}"
            )
            embed.add_field(name=f"👤 {user.display_name}", value=aciklama, inline=False)
            
        await kanal.send(embed=embed)
        save_stats({})
        self.active_voice_sessions.clear()


async def setup(bot):
    await bot.add_cog(YardimBekleme(bot))
