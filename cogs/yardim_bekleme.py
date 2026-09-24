import discord
from discord.ext import commands, tasks
from discord import app_commands
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

        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="✅ Destek Sonlandırıldı", color=discord.Color.green())
            embed.description = f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısının desteğini sonlandırdı.\n**Süre:** {sure_metni}\n**Sonuç:** {self.sonuc.value}"
            await log_kanal.send(embed=embed)

        await interaction.message.edit(content=f"✅ {interaction.user.mention} desteği sonlandırdı.", view=None, embed=None)
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

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.success, emoji="✅")
    async def bitir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DestekBitirModal(self.baslangic_zamani, self.yardim_isteyen_id))

    @discord.ui.button(label="Boş Çıktı", style=discord.ButtonStyle.secondary, emoji="🗑️")
    async def bos_cikti_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="❌ Destek Boş Çıktı", color=discord.Color.light_grey())
            embed.description = f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısının desteğini **'Boş'** olarak sonuçlandırdı."
            await log_kanal.send(embed=embed)

        await interaction.message.edit(content=f"❌ {interaction.user.mention} desteği boş olarak sonlandırdı.", view=None, embed=None)
        await interaction.followup.send("Kullanıcı boş çıktığı için destek sonlandırıldı.", ephemeral=True)


class DevralView(discord.ui.View):
    def __init__(self, yardim_isteyen_id: int):
        super().__init__(timeout=None)
        self.yardim_isteyen_id = yardim_isteyen_id

    @discord.ui.button(label="Katılımcıyı Devral", style=discord.ButtonStyle.success, emoji="👋")
    async def devral_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        yardim_isteyen = guild.get_member(self.yardim_isteyen_id)
        yardim_kanal = guild.get_channel(YARDIM_VC_ID)

        if not yardim_isteyen or not yardim_isteyen.voice:
            await interaction.followup.send("❌ Katılımcı şu anda seste değil!", ephemeral=True)
            await interaction.message.edit(content="❌ Katılımcı sesten ayrıldığı için işlem iptal edildi.", view=None, embed=None)
            return

        try:
            await yardim_isteyen.move_to(yardim_kanal)
            await yardim_isteyen.edit(mute=False)
        except Exception as e:
            await interaction.followup.send("❌ Kullanıcı odaya çekilirken hata oluştu. (Belki sesten çıkmıştır)", ephemeral=True)
            return

        baslangic = discord.utils.utcnow()
        await interaction.message.edit(
            content=f"👋 {interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısının desteğini devraldı.\n(Odaya çekildi ve susturması açıldı)",
            view=DestekAktifView(interaction.user.id, self.yardim_isteyen_id, baslangic),
            embed=None
        )
        await interaction.followup.send("Destek başarıyla devralındı.", ephemeral=True)

    @discord.ui.button(label="Beklemeden Çıkar", style=discord.ButtonStyle.danger, emoji="🚪")
    async def at_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        yardim_isteyen = guild.get_member(self.yardim_isteyen_id)

        if yardim_isteyen and yardim_isteyen.voice:
            try:
                await yardim_isteyen.move_to(None)
            except Exception:
                pass

        log_kanal = interaction.guild.get_channel(ONLY_MOD_KANALI)
        if log_kanal:
            embed = discord.Embed(title="🚪 Katılımcı Atıldı", color=discord.Color.red())
            embed.description = f"{interaction.user.mention}, <@{self.yardim_isteyen_id}> kullanıcısını **Yardım Bekleme** kanalından beklemeden çıkardı."
            await log_kanal.send(embed=embed)

        await interaction.message.edit(content=f"🚪 {interaction.user.mention}, katılımcıyı beklemeden çıkardı.", view=None, embed=None)


class YardimBekleme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_voice_sessions = {}
        self.gunluk_rapor.start()

    @app_commands.command(name="destek-bildir", description="Belirtilen kullanıcıyı destek bekleme odasına yönlendirir.")
    @app_commands.describe(
        kisi="Çağrılacak kişi",
        sebep="Çağrı sebebi",
        tahmini_sure="Tahmini destek süresi"
    )
    async def destek_bildir(self, interaction: discord.Interaction, kisi: discord.Member, sebep: str, tahmini_sure: str):
        admin_roles = {
            1529546007635824680: "Kurucu",
            1539167256246747186: "Üst Yönetim",
            1534798061845483694: "Yönetici",
            1537934087166369812: "Yönetim Ekibi",
            1551241753137254611: "Senior Staff",
            1551241634094645288: "Staff",
            1551241468985737376: "Trial Staff"
        }
        
        yetkili_rol_adi = "Yetkili"
        for role_id, role_name in admin_roles.items():
            if discord.utils.get(interaction.user.roles, id=role_id):
                yetkili_rol_adi = role_name
                break
                
        user_roles = {
            1539249508314259567: "İllegal",
            1539318613498929193: "Legal"
        }
        
        kisi_rol_adi = "Sivil"
        for role_id, role_name in user_roles.items():
            if discord.utils.get(kisi.roles, id=role_id):
                kisi_rol_adi = role_name
                break
                
        def get_next_destek_id():
            id_file = "data/destek_id.json"
            if not os.path.exists("data"):
                os.makedirs("data")
            if not os.path.exists(id_file):
                last_id = 0
            else:
                try:
                    with open(id_file, "r") as f:
                        data = json.load(f)
                        last_id = data.get("last_id", 0)
                except:
                    last_id = 0
            new_id = last_id + 1
            with open(id_file, "w") as f:
                json.dump({"last_id": new_id}, f)
            return f"PRP-{new_id:05d}"
            
        destek_id = get_next_destek_id()
        
        embed = discord.Embed(
            description=(
                f"## ✉️ Destek Çağrı Bildirimi\n"
                f"Kullanıcı destek bekleme ses kanalına yönlendirildi.\n"
                f"{kisi.mention} | {kisi_rol_adi}\n\n"
                f"***\n\n"
                f"### 📌 Çağrı Bilgisi\n"
                f"• **Çağrı ID:** {destek_id}\n"
                f"• **Kullanıcı:** {kisi.mention} | {kisi_rol_adi}\n"
                f"• **Çağıran Yetkili:** {interaction.user.mention} | {yetkili_rol_adi}\n"
                f"• **Süre:** {tahmini_sure}\n\n"
                f"***\n\n"
                f"### ✨ Yönlendirme\n"
                f"• **Sebep:** {sebep}\n\n"
                f"Lütfen [Yardım bekleme](https://discord.com/channels/1529545898294509589/1532829788824404274) ses kanalına geçiniz. Yetkili hazır olduğunda destek odasına alınacaksınız."
            ),
            color=discord.Color.from_rgb(254, 231, 92) # #FEE75C in RGB
        )
        
        embed.set_footer(text="© 2026 PRP")
        
        LOGO_URL = "https://files.catbox.moe/m3e09z.png"
        if LOGO_URL.startswith("http"):
            embed.set_thumbnail(url=LOGO_URL)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        target_channel = interaction.client.get_channel(1552041858530672670)
        if target_channel:
            await target_channel.send(content=f"{kisi.mention}", embed=embed)
            await interaction.response.send_message("✅ Bildirim başarıyla gönderildi.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)

    def cog_unload(self):
        self.gunluk_rapor.cancel()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return

        if before.channel is None and after.channel is not None:
            self.active_voice_sessions[member.id] = discord.utils.utcnow()
        elif before.channel is not None and after.channel is None:
            if member.id in self.active_voice_sessions:
                join_time = self.active_voice_sessions.pop(member.id)
                fark = (discord.utils.utcnow() - join_time).total_seconds()
                update_mod_stat(member.id, "voice_time", fark)

        if after.channel and after.channel.id == YARDIM_BEKLEME_VC_ID and (before.channel is None or before.channel.id != YARDIM_BEKLEME_VC_ID):
            try:
                await member.edit(mute=True)
            except Exception:
                pass
            
            kanal = self.bot.get_channel(ONEMLI_LOG_KANALI)
            if kanal:
                embed = discord.Embed(
                    title="👀 Yardım Bekleyen Var!", 
                    description=f"{member.mention} **Yardım Bekleme** kanalına giriş yaptı ve destek bekliyor.", 
                    color=discord.Color.orange()
                )
                embed.timestamp = discord.utils.utcnow()
                
                ping_msg = f"<@&{YONETIM_EKIBI_ROL}>"
                await kanal.send(content=ping_msg, embed=embed, view=DevralView(member.id))

        elif before.channel and before.channel.id == YARDIM_BEKLEME_VC_ID:
            if after.channel is not None and after.channel.id != YARDIM_BEKLEME_VC_ID:
                try:
                    await member.edit(mute=False)
                except Exception:
                    pass

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
