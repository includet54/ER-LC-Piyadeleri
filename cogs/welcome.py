import discord
from discord.ext import commands
import os

HOSGELDIN_KANAL_ID = 1532829955409449081
CIKIS_KANAL_ID = 1533621981830844538
KATILIMCI_SAYISI_KANAL_ID = 1551308350615199935

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def guncelle_katilimci_sayisi(self, guild: discord.Guild):
        kanal = guild.get_channel(KATILIMCI_SAYISI_KANAL_ID)
        if kanal:
            yeni_isim = f"══▐ {guild.member_count} KATILIMCI▐ ══"
            if kanal.name != yeni_isim:
                try:
                    await kanal.edit(name=yeni_isim)
                except Exception as e:
                    print(f"Katılımcı sayısı güncellenirken hata: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        # Bot başladığında sayıyı kontrol edip günceller
        for guild in self.bot.guilds:
            await self.guncelle_katilimci_sayisi(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.guncelle_katilimci_sayisi(member.guild)
        
        # Kayıtsız rolünü ver
        kayitsiz_rol = member.guild.get_role(1542271426386591894)
        if kayitsiz_rol:
            try:
                await member.add_roles(kayitsiz_rol, reason="Sunucuya katıldı")
            except Exception:
                pass
        
        channel = member.guild.get_channel(HOSGELDIN_KANAL_ID)
        if channel is None:
            return

        member_count = member.guild.member_count

        embed = discord.Embed(
            title="✨ Sunucumuza Hoş Geldin!",
            description=(
                f"Merhaba {member.mention}!\n\n"
                f"**{member.guild.name}** ailesine katıldığın için çok mutluyuz.\n"
                f"Seninle birlikte artık **{member_count}** kişiyiz!\n\n"
                f"📜 Kuralları okumayı unutma\n"
                f"💬 Sohbete katılmaktan çekinme\n"
                f"🎮 İyi eğlenceler dileriz!"
            ),
            color=discord.Color.from_rgb(147, 112, 219)
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        gif_path = "assets/hosgeldin.gif"
        dosya = None
        if os.path.exists(gif_path):
            dosya = discord.File(gif_path, filename="hosgeldin.gif")
            embed.set_image(url="attachment://hosgeldin.gif")

        embed.set_footer(
            text=f"ID: {member.id} • Katılma",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )
        embed.timestamp = discord.utils.utcnow()

        if dosya:
            await channel.send(content=f"Hoş geldin {member.mention} 💜", embed=embed, file=dosya)
        else:
            await channel.send(content=f"Hoş geldin {member.mention} 💜", embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.guncelle_katilimci_sayisi(member.guild)
        
        channel = member.guild.get_channel(CIKIS_KANAL_ID)
        if channel is None:
            return

        embed = discord.Embed(
            title="👋 Bir Üye Ayrıldı",
            description=f"**{member.display_name}** ({member.mention}) aramızdan ayrıldı.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = discord.utils.utcnow()

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))