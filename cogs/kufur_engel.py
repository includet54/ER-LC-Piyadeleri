import discord
from discord.ext import commands
import re

KUFUR_LOG_KANAL_ID = 1551257729530855464

class KufurEngel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Temel kelimelerin kökleri (Bu kelimeleri barındıran tüm kelimeler küfür sayılabilir, 
        # ancak kısa kelimelerde sadece tam eşleşme arayacağız)
        self.kufurler_tam_eslesme = {
            "am", "aq", "amk", "amq", "4q", "4mk", "mal", "aptal", "salak", "gerizekalı",
            "göt", "g0t", "bok", "sıç", "piç", "p1ç", "p!ç", "döl", "sik", "s1k", "s!k", "s*k", "5ik"
        }
        
        # İçinde geçmesi yeterli olan kökler (yanlış alarm verme ihtimali çok düşük olanlar)
        self.kufurler_kapsayan = [
            "amına", "amcık", "amcik", "amc1k", "amını", "amk", "amq",
            "orospu", "or0spu", "0rospu",
            "siktir", "sikey", "siker", "sikiş", "sikik", "siktiğ", "sikim", "sktr", "sokay", "soktuğ",
            "yarrak", "yarak", "yarram", "yarrağ", "y4rrak", "yarr4k", "yarraq",
            "götveren", "götlek", "götten",
            "pezevenk", "pezevenğ",
            "kahpe", "ibne", "gavat",
            "taşşak", "taşak", "yavşak"
        ]
        
        # Kelimenin başında veya tam olarak eşleşmesi gerekenler (Örn: "karını", "ananı" - "makarnanı"yı silmesin diye)
        self.riskli_kokler = [
            "ananı", "ananın", "bacını", "karını", "götün", "manyak"
        ]

    def kufur_mu(self, mesaj_icerigi: str) -> bool:
        mesaj_lower = mesaj_icerigi.lower().replace('İ', 'i').replace('I', 'ı')
        
        if re.search(r'\ba\s*[\.\*]?\s*m\s*[\.\*]?\s*[kq]\b', mesaj_lower): return True
        if re.search(r'\ba\s*[\.\*]?\s*q\b', mesaj_lower): return True
        if re.search(r'\bp\s*[\.\*!\d]?\s*[iı]\s*[\.\*]?\s*ç\b', mesaj_lower): return True
        
        kelimeler = re.findall(r'\b\w+\b', mesaj_lower, flags=re.UNICODE)
        
        for kelime in kelimeler:
            if kelime in self.kufurler_tam_eslesme:
                return True
            for riskli in self.riskli_kokler:
                if kelime.startswith(riskli):
                    return True

        for kufur in self.kufurler_kapsayan:
            if kufur in mesaj_lower:
                return True
                
        return False

    async def log_kufur(self, message: discord.Message, eylem_turu: str):
        log_kanal = self.bot.get_channel(KUFUR_LOG_KANAL_ID)
        if not log_kanal:
            return

        embed = discord.Embed(
            title=f"🚨 Küfür / Hakaret Tespit Edildi ({eylem_turu})",
            color=discord.Color.red()
        )
        embed.add_field(name="Kullanıcı", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
        embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
        embed.add_field(name="Mesaj İçeriği", value=f"```{message.content}```", inline=False)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        try:
            await log_kanal.send(content="<@&1542249243702726796>", embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if self.kufur_mu(message.content):
            await self.log_kufur(message, "Yeni Mesaj")
            try:
                await message.author.send(f"⚠️ **{message.guild.name}** sunucusunda lütfen sözlerine dikkat et! Küfür/Hakaret içeren kelimeler kullanmak yasaktır.")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        if self.kufur_mu(after.content):
            await self.log_kufur(after, "Düzenlenen Mesaj")
            try:
                await after.author.send(f"⚠️ **{after.guild.name}** sunucusunda lütfen sözlerine dikkat et! Küfür/Hakaret içeren kelimeler kullanmak yasaktır.")
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(KufurEngel(bot))
