import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime

# ============================
MODERATOR_LOG_KANALI = 1532828404347437287
DATA_FILE = "data/mod_stats.json"
GUNLUK_HEDEF_SANIYE = 5 * 60 * 60  # 5 saat
# ============================

def load_stats():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_stats(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_mod_stat(mod_id, key, amount=1):
    data = load_stats()
    mod_id = str(mod_id)
    if mod_id not in data:
        data[mod_id] = {"voice_time": 0, "supports": 0, "tickets": 0}
    data[mod_id][key] += amount
    save_stats(data)

def progress_bar(current, total, length=15):
    progress = min(1.0, current / total)
    filled = int(length * progress)
    return "█" * filled + "░" * (length - filled)


# ZAMAN AŞIMINI ÇÖZEN MODAL
class DestekBitirModal(discord.ui.Modal, title="Desteği Sonlandır"):
    sonuc = discord.ui.TextInput(
        label="Desteği Bitir Anketi Nasıl Sonuçlandı?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Sorunu çözüldü, kurallar anlatıldı.",
        required=True
    )
    ekstra = discord.ui.TextInput(
        label="Ekstra notlar (Kime destek verildi?)",
        style=discord.TextStyle.short,
        placeholder="Örn: @Ahmet kişisine destek verdim.",
        required=False
    )

    def __init__(self, baslangic_zamani: datetime.datetime):
        super().__init__()
        self.baslangic_zamani = baslangic_zamani

    async def on_submit(self, interaction: discord.Interaction):
        bitis_zamani = discord.utils.utcnow()
        fark = bitis_zamani - self.baslangic_zamani
        dakika = int(fark.total_seconds() // 60)
        saniye = int(fark.total_seconds() % 60)
        sure_metni = f"{dakika} dk {saniye} sn"

        # Moderatörün destek sayısını artır
        update_mod_stat(interaction.user.id, "supports", 1)

        kanal = interaction.guild.get_channel(MODERATOR_LOG_KANALI)
        if kanal:
            embed = discord.Embed(title="✅ Destek Sonlandırıldı", color=discord.Color.green())
            embed.add_field(name="İlgilenen Yetkili", value=interaction.user.mention, inline=True)
            embed.add_field(name="Destek Süresi", value=sure_metni, inline=True)
            embed.add_field(name="Anket Sonucu", value=self.sonuc.value, inline=False)
            if self.ekstra.value:
                embed.add_field(name="Kime / Ek Notlar", value=self.ekstra.value, inline=False)
            embed.timestamp = bitis_zamani
            await kanal.send(embed=embed)
        
        await interaction.response.send_message("Destek başarıyla sonlandırıldı ve log kanalına iletildi.", ephemeral=True)


class DestekPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Sadece 1 buton var, o da desteği bitir butonu. Desteği alan kişi basar.

    @discord.ui.button(label="Desteği Başlat", style=discord.ButtonStyle.primary, custom_id="destek_baslat_btn")
    async def destek_baslat(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Desteğin ne zaman başladığını tutmak için ephemeral bir mesaj ve bitir butonu yollayalım.
        await interaction.response.send_message("Destek başlatıldı! Desteği bitirdiğinde aşağıdaki butona bas.", view=DestekBitirView(discord.utils.utcnow()), ephemeral=True)

class DestekBitirView(discord.ui.View):
    def __init__(self, baslangic_zamani: datetime.datetime):
        super().__init__(timeout=None)
        self.baslangic_zamani = baslangic_zamani

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.danger, custom_id="destek_bitir_btn_modal")
    async def destek_bitir(self, interaction: discord.Interaction, button: discord.ui.Button):
        # İşte zaman aşımını engelleyen Modal çözümü:
        await interaction.response.send_modal(DestekBitirModal(self.baslangic_zamani))


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

        # Odaya girdi
        if before.channel is None and after.channel is not None:
            self.active_voice_sessions[member.id] = discord.utils.utcnow()
        
        # Odadan çıktı
        elif before.channel is not None and after.channel is None:
            if member.id in self.active_voice_sessions:
                join_time = self.active_voice_sessions.pop(member.id)
                leave_time = discord.utils.utcnow()
                fark = (leave_time - join_time).total_seconds()
                update_mod_stat(member.id, "voice_time", fark)

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
            
            # Zaman hesaplama
            toplam_saniye = stat["voice_time"]
            saat = int(toplam_saniye // 3600)
            dak = int((toplam_saniye % 3600) // 60)
            
            # Progress bar
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
        
        # Verileri sıfırla
        save_stats({})
        self.active_voice_sessions.clear()

    @app_commands.command(name="destek-panel", description="Destek başlatma panelini kurar.")
    @app_commands.default_permissions(administrator=True)
    async def destek_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎧 Destek Bekleme",
            description="Destek odasına geldiyseniz, ilgilenmek için butona basın.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed, view=DestekPanelView())
        await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YardimBekleme(bot))
