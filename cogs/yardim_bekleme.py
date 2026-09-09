import discord
from discord.ext import commands, tasks
import json
import os
import datetime

# ============================
# KANAL VE ROL ID'LERİ (İsteğine göre ayarlandı)
YARDIM_BEKLEME_VC_ID = 1532829788824404274
YARDIM_VC_ID = 1532829837150916719
ONEMLI_LOG_KANALI = 1532829734742786168
ONLY_MOD_KANALI = 1532828404347437287
YONETIM_EKIBI_ROL = 1537934087166369812

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
        label="Katılımcı Neden Yardım İstedi? Sonuç Ne?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Kullanıcının kayıt sorunu çözüldü, kurallar hatırlatıldı.",
        required=True,
        max_length=1000
    )

    def __init__(self, baslangic_zamani: datetime.datetime, yardim_isteyen_id: int):
        super().__init__()
        self.baslangic_zamani = baslangic_zamani
        self.yardim_isteyen_id = yardim_isteyen_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        bitis_zamani = discord.utils.utcnow()
        fark = bitis_zamani - self.baslangic_zamani
        dakika = int(fark.total_seconds() // 60)
        saniye = int(fark.total_seconds() % 60)
        sure_metni = f"{dakika} dk {saniye} sn"

        update_mod_stat(interaction.user.id, "supports", 1)

        # Only Moderatör Kanalına Log Gönder
        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="✅ Destek Tamamlandı", color=discord.Color.green())
            embed.add_field(name="İlgilenen Yetkili", value=interaction.user.mention, inline=True)
            embed.add_field(name="Katılımcı", value=f"<@{self.yardim_isteyen_id}>", inline=True)
            embed.add_field(name="Destek Süresi", value=sure_metni, inline=True)
            embed.add_field(name="Açıklama / Sonuç", value=self.sonuc.value, inline=False)
            await log_kanal.send(embed=embed)

        # Mesajdaki butonları devre dışı bırak
        await interaction.message.edit(content=f"✅ {interaction.user.mention} desteği anket doldurarak sonlandırdı.", view=None, embed=None)
        await interaction.followup.send("Destek başarıyla sonlandırıldı ve log iletildi.", ephemeral=True)


class DestekAktifView(discord.ui.View):
    def __init__(self, yetkili_id: int, yardim_isteyen_id: int, baslangic_zamani: datetime.datetime):
        super().__init__(timeout=None)
        self.yetkili_id = yetkili_id
        self.yardim_isteyen_id = yardim_isteyen_id
        self.baslangic_zamani = baslangic_zamani

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.yetkili_id:
            await interaction.response.send_message("❌ Sadece desteği devralan yetkili bu işlemi yapabilir!", ephemeral=True)
            return False
        return True

    async def _kick_everyone_from_yardim(self, guild):
        kanal = guild.get_channel(YARDIM_VC_ID)
        if kanal:
            for uye in list(kanal.members):
                try:
                    await uye.move_to(None)
                except Exception:
                    pass

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success)
    async def bitir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Önce herkesi sesten at, sonra anketi göster
        await self._kick_everyone_from_yardim(interaction.guild)
        await interaction.response.send_modal(DestekBitirModal(self.baslangic_zamani, self.yardim_isteyen_id))

    @discord.ui.button(label="Boş", style=discord.ButtonStyle.secondary)
    async def bos_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Herkesi sesten at
        await self._kick_everyone_from_yardim(interaction.guild)
        
        # Log gönder
        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="ℹ️ Destek Boş Çıktı", color=discord.Color.light_grey())
            embed.description = f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısının desteğini **'Boş'** olarak sonuçlandırdı."
            await log_kanal.send(embed=embed)

        await interaction.message.edit(content=f"ℹ️ {interaction.user.mention} desteği boş olarak sonlandırdı.", view=None, embed=None)
        await interaction.followup.send("Kullanıcı boş çıktığı için destek sonlandırıldı.", ephemeral=True)


class DevralView(discord.ui.View):
    def __init__(self, yardim_isteyen_id: int):
        super().__init__(timeout=None)
        self.yardim_isteyen_id = yardim_isteyen_id

    @discord.ui.button(label="Katılımcıyı Devral", style=discord.ButtonStyle.success, emoji="✅")
    async def devral_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        yardim_isteyen = guild.get_member(self.yardim_isteyen_id)
        yardim_kanal = guild.get_channel(YARDIM_VC_ID)

        if not yardim_isteyen or not yardim_isteyen.voice:
            await interaction.followup.send("❌ Katılımcı şu anda seste değil!", ephemeral=True)
            await interaction.message.edit(content="❌ Katılımcı sesten ayrıldığı için işlem iptal edildi.", view=None, embed=None)
            return

        # Katılımcıyı YARDIM kanalına çek ve susturmasını kaldır
        try:
            await yardim_isteyen.move_to(yardim_kanal)
            await yardim_isteyen.edit(mute=False)
        except discord.Forbidden:
            await interaction.followup.send("❌ Kullanıcıyı taşımak veya susturmasını açmak için gerekli yetkiye sahip değilim.", ephemeral=True)
            return
        except Exception:
            pass

        # Tuşa basan yetkili eğer bir sesteyse onu da YARDIM kanalına çek
        if interaction.user.voice and interaction.user.voice.channel:
            try:
                await interaction.user.move_to(yardim_kanal)
            except Exception:
                pass

        yeni_icerik = f"✅ {interaction.user.mention}, <@{self.yardim_isteyen_id}> adlı kullanıcının destek talebini devraldı."
        
        # Butonları Desteği Bitir / Boş olarak güncelle
        view = DestekAktifView(interaction.user.id, self.yardim_isteyen_id, discord.utils.utcnow())
        await interaction.message.edit(content=yeni_icerik, view=view, embed=None)

    @discord.ui.button(label="Katılımcıyı Beklemeden Çıkar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cikar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        yardim_isteyen = guild.get_member(self.yardim_isteyen_id)

        # Eğer adam hâlâ yardım bekleme odasındaysa odadan at
        if yardim_isteyen and yardim_isteyen.voice and yardim_isteyen.voice.channel and yardim_isteyen.voice.channel.id == YARDIM_BEKLEME_VC_ID:
            try:
                await yardim_isteyen.move_to(None)
            except Exception:
                pass

        # Log gönder
        log_kanal = guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="👢 Katılımcı Atıldı", color=discord.Color.red())
            embed.description = f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısını **Yardım Bekleme** kanalından beklemeden çıkardı."
            await log_kanal.send(embed=embed)

        await interaction.message.edit(content=f"✖️ {interaction.user.mention}, katılımcıyı beklemeden çıkardı.", view=None, embed=None)


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

        # 1. GÜNLÜK SES AKTİFLİĞİ SİSTEMİ
        if before.channel is None and after.channel is not None:
            self.active_voice_sessions[member.id] = discord.utils.utcnow()
        elif before.channel is not None and after.channel is None:
            if member.id in self.active_voice_sessions:
                join_time = self.active_voice_sessions.pop(member.id)
                fark = (discord.utils.utcnow() - join_time).total_seconds()
                update_mod_stat(member.id, "voice_time", fark)

        # 2. YARDIM BEKLEME SİSTEMİ
        # Eğer kullanıcı "Yardım Bekleme" kanalına giriş yaparsa:
        if after.channel and after.channel.id == YARDIM_BEKLEME_VC_ID and (before.channel is None or before.channel.id != YARDIM_BEKLEME_VC_ID):
            
            # Giriş yaptığında sustur
            try:
                await member.edit(mute=True)
            except Exception:
                pass
            
            # Önemli Log Bildirim kanalına log düş ve Yönetim Ekibini etiketle
            kanal = self.bot.get_channel(ONEMLI_LOG_KANALI)
            if kanal:
                embed = discord.Embed(
                    title="🆘 Yardım Bekleyen Var!", 
                    description=f"{member.mention} **Yardım Bekleme** kanalına giriş yaptı ve destek bekliyor.", 
                    color=discord.Color.orange()
                )
                embed.timestamp = discord.utils.utcnow()
                
                ping_msg = f"<@&{YONETIM_EKIBI_ROL}>"
                await kanal.send(content=ping_msg, embed=embed, view=DevralView(member.id))

        # Eğer kullanıcı "Yardım Bekleme" kanalından çıkarsa (veya devralınıp başka kanala çekilirse)
        elif before.channel and before.channel.id == YARDIM_BEKLEME_VC_ID:
            # Kullanıcı eğer bağlantıyı tamamen kesmediyse (başka odaya geçmişse) susturmasını kaldır
            if after.channel is not None and after.channel.id != YARDIM_BEKLEME_VC_ID:
                try:
                    await member.edit(mute=False)
                except Exception:
                    pass

    # Türkiye saatiyle gece 00:00 (UTC 21:00) 
    @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=datetime.timezone.utc))
    async def gunluk_rapor(self):
        await self.bot.wait_until_ready()
        kanal = self.bot.get_channel(ONLY_MOD_KANALI)
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
