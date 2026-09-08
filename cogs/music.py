import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

# yt-dlp ayarları
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# Panel Butonları (Geçmiş ve Liste İçin)
class MusicPanelView(discord.ui.View):
    def __init__(self, voice_client):
        super().__init__(timeout=None)
        self.vc = voice_client

    @discord.ui.button(label="Oynat/Duraklat", style=discord.ButtonStyle.primary, custom_id="toggle_play")
    async def toggle_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("Şarkı duraklatıldı.", ephemeral=True)
        elif self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("Şarkı devam ediyor.", ephemeral=True)

    @discord.ui.button(label="Geç (Skip)", style=discord.ButtonStyle.secondary, custom_id="skip_track")
    async def skip_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.stop()
            await interaction.response.send_message("Şarkı geçildi.", ephemeral=True)

    @discord.ui.button(label="Durdur (Stop)", style=discord.ButtonStyle.danger, custom_id="stop_track")
    async def stop_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.disconnect()
        await interaction.response.send_message("Müzik durduruldu ve kanaldan çıkıldı.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Veritabanı yerine geçici bellek (Sistemi kapatınca sıfırlanır. Kalıcı olması için SQLite eklenmelidir.)
        self.playlists = {}
        self.history = []

    async def join_channel(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("Bir ses kanalında olmalısınız!")
            return None
        channel = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            vc = await channel.connect()
            return vc
        return interaction.guild.voice_client

    @app_commands.command(name="play", description="YouTube'dan bir link oynatır.")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        vc = await self.join_channel(interaction)
        if not vc:
            return

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        song_url = data['url']
        title = data.get('title', 'Bilinmeyen Şarkı')
        
        self.history.append(title)
        
        vc.play(discord.FFmpegPCMAudio(song_url, **ffmpeg_options))
        await interaction.followup.send(f"🎵 Oynatılıyor: **{title}**")

    @app_commands.command(name="play-file", description="Yüklenen bir ses dosyasını oynatır.")
    async def play_file(self, interaction: discord.Interaction, dosya: discord.Attachment):
        if not dosya.content_type.startswith('audio/'):
            return await interaction.response.send_message("Lütfen geçerli bir ses dosyası yükleyin.", ephemeral=True)
            
        vc = await self.join_channel(interaction)
        if not vc:
            return
            
        self.history.append(dosya.filename)
        vc.play(discord.FFmpegPCMAudio(dosya.url, **ffmpeg_options))
        await interaction.response.send_message(f"🎵 Dosya oynatılıyor: **{dosya.filename}**")

    @app_commands.command(name="stop", description="Şarkıyı durdurur ve kanaldan ayrılır.")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("Müzik durduruldu.")
        else:
            await interaction.response.send_message("Bot zaten bir ses kanalında değil.")

    @app_commands.command(name="creat-list", description="Yeni bir çalma listesi oluşturur.")
    async def creat_list(self, interaction: discord.Interaction, liste_ismi: str):
        if liste_ismi in self.playlists:
            await interaction.response.send_message("Bu isimde bir liste zaten var.", ephemeral=True)
        else:
            self.playlists[liste_ismi] = []
            await interaction.response.send_message(f"📁 **{liste_ismi}** adlı liste oluşturuldu.")

    @app_commands.command(name="add-list", description="Belirtilen listeye YouTube linki ekler.")
    async def add_list(self, interaction: discord.Interaction, liste_ismi: str, url: str):
        if liste_ismi not in self.playlists:
            return await interaction.response.send_message("Böyle bir liste bulunamadı.", ephemeral=True)
        
        self.playlists[liste_ismi].append({'tip': 'url', 'veri': url})
        await interaction.response.send_message(f"✅ Link **{liste_ismi}** listesine eklendi.")

    @app_commands.command(name="add-list-file", description="Belirtilen listeye ses dosyası ekler.")
    async def add_list_file(self, interaction: discord.Interaction, liste_ismi: str, dosya: discord.Attachment):
        if liste_ismi not in self.playlists:
            return await interaction.response.send_message("Böyle bir liste bulunamadı.", ephemeral=True)
        
        self.playlists[liste_ismi].append({'tip': 'dosya', 'veri': dosya.url, 'isim': dosya.filename})
        await interaction.response.send_message(f"✅ **{dosya.filename}** dosyası **{liste_ismi}** listesine eklendi.")

    @app_commands.command(name="lists", description="Liste panelini görüntüler.")
    async def lists(self, interaction: discord.Interaction):
        if not self.playlists:
            return await interaction.response.send_message("Şu anda hiç liste yok.")
            
        listeler = "\n".join([f"• {isim} ({len(icerik)} şarkı)" for isim, icerik in self.playlists.items()])
        embed = discord.Embed(title="Çalma Listeleri", description=listeler, color=discord.Color.blue())
        
        vc = interaction.guild.voice_client
        view = MusicPanelView(vc) if vc else None
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="delete-list", description="Belirtilen listeyi siler.")
    async def delete_list(self, interaction: discord.Interaction, liste_ismi: str):
        if liste_ismi in self.playlists:
            del self.playlists[liste_ismi]
            await interaction.response.send_message(f"🗑️ **{liste_ismi}** adlı liste silindi.")
        else:
            await interaction.response.send_message("Böyle bir liste bulunamadı.", ephemeral=True)

    @app_commands.command(name="history-panel", description="Geçmişte oynatılan şarkıları görüntüler.")
    async def history_panel(self, interaction: discord.Interaction):
        if not self.history:
            return await interaction.response.send_message("Henüz bir şarkı oynatılmadı.")
            
        gecmis = "\n".join([f"• {sarki}" for sarki in self.history[-10:]]) # Son 10 şarkıyı gösterir
        embed = discord.Embed(title="Oynatma Geçmişi", description=gecmis, color=discord.Color.green())
        
        vc = interaction.guild.voice_client
        view = MusicPanelView(vc) if vc else None
        
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Music(bot))
