import discord
from discord.ext import commands, tasks
import datetime

ONLY_MOD_CHANNEL_ID = 1532828404347437287

# Moderatör istatistiklerini tutacağımız sözlük
# Format: {mod_id: {"aktif_saniye": 0, "destek_sayisi": 0, "bilet_sayisi": 0}}
mod_stats = {}

class DestekBitirModal(discord.ui.Modal, title="Desteği Sonlandır"):
    soru1 = discord.ui.TextInput(
        label="Destek nasıl sonuçlandı?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Kullanıcının sorunu çözüldü...",
        required=True
    )
    soru2 = discord.ui.TextInput(
        label="Eklemek istediğiniz notlar?",
        style=discord.TextStyle.paragraph,
        placeholder="Örn: Kullanıcıya kurallar hatırlatıldı.",
        required=False
    )

    def __init__(self, baslangic_zamani, yetkili):
        super().__init__()
        self.baslangic_zamani = baslangic_zamani
        self.yetkili = yetkili

    async def on_submit(self, interaction: discord.Interaction):
        bitis_zamani = discord.utils.utcnow()
        gecen_sure = bitis_zamani - self.baslangic_zamani
        dakika, saniye = divmod(int(gecen_sure.total_seconds()), 60)

        # İstatistikleri güncelle
        if self.yetkili.id not in mod_stats:
            mod_stats[self.yetkili.id] = {"aktif_saniye": 0, "destek_sayisi": 0, "bilet_sayisi": 0}
        mod_stats[self.yetkili.id]["destek_sayisi"] += 1
        # Aktif saniye sistemi (örnektir, seste kalma takip ediliyorsa oradan da eklenebilir)
        mod_stats[self.yetkili.id]["aktif_saniye"] += int(gecen_sure.total_seconds())

        kanal = interaction.client.get_channel(ONLY_MOD_CHANNEL_ID)
        embed = discord.Embed(title="Destek Sonlandırıldı", color=discord.Color.green())
        embed.add_field(name="İlgilenen Yetkili", value=self.yetkili.mention, inline=True)
        embed.add_field(name="Geçen Süre", value=f"{dakika} dk {saniye} sn", inline=True)
        embed.add_field(name="Soru 1 (Sonuç)", value=self.soru1.value, inline=False)
        if self.soru2.value:
            embed.add_field(name="Soru 2 (Notlar)", value=self.soru2.value, inline=False)
        
        await kanal.send(embed=embed)
        await interaction.response.send_message("Destek başarıyla sonlandırıldı ve loglandı.", ephemeral=True)

class DestekView(discord.ui.View):
    def __init__(self, baslangic_zamani):
        super().__init__(timeout=None)
        self.baslangic_zamani = baslangic_zamani

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.danger, custom_id="destegi_bitir_btn")
    async def bitir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Modal açarak 3 saniye kuralını aşıyoruz (zaman aşımı hatası biter)
        await interaction.response.send_modal(DestekBitirModal(self.baslangic_zamani, interaction.user))

class YardimBekleme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gunluk_istatistik.start()

    # Gece 00:00'da çalışacak görev
    # timezone.utc'ye göre saat 21:00, Türkiye saati ile gece 00:00'a denk gelir.
    @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=datetime.timezone.utc))
    async def gunluk_istatistik(self):
        kanal = self.bot.get_channel(ONLY_MOD_CHANNEL_ID)
        if not kanal:
            return

        hedef_saniye = 5 * 3600 # 5 Saat
        embed = discord.Embed(title="Günün Yetkili Analizi ve İstatistikleri", color=discord.Color.blue())
        
        if not mod_stats:
            embed.description = "Bugün hiçbir yetkili verisi kaydedilmedi."
        else:
            for mod_id, veriler in mod_stats.items():
                aktif = veriler["aktif_saniye"]
                oran = min(aktif / hedef_saniye, 1.0)
                dolu_blok = int(oran * 10)
                bos_blok = 10 - dolu_blok
                xp_bar = "🟩" * dolu_blok + "⬛" * bos_blok
                
                aktif_saat, kalan = divmod(aktif, 3600)
                aktif_dk, _ = divmod(kalan, 60)
                
                embed.add_field(
                    name=f"<@{mod_id}>", 
                    value=f"**Süre:** {aktif_saat}s {aktif_dk}d\n**İlerleme:** {xp_bar}\n**Destek Sayısı:** {veriler['destek_sayisi']}\n**Bilet Sayısı:** {veriler['bilet_sayisi']}", 
                    inline=False
                )
        
        await kanal.send(embed=embed)
        # Gün sonunda istatistikleri sıfırla
        mod_stats.clear()

    @commands.command(name="yardim_baslat")
    @commands.has_permissions(manage_messages=True)
    async def yardim_baslat(self, ctx):
        baslangic = discord.utils.utcnow()
        await ctx.send("Destek talebi başladı. Bitirmek için butona tıklayın.", view=DestekView(baslangic))

async def setup(bot):
    await bot.add_cog(YardimBekleme(bot))
