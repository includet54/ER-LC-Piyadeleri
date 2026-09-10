import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class MusicControlView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    async def update_panel(self, interaction: discord.Interaction):
        state = self.cog.get_state(self.guild_id)
        embed = discord.Embed(title="🎶 Müzik Kuyruğu", color=discord.Color.blue())
        if not state["queue"]:
            embed.description = "Sıra boş."
        else:
            liste_metni = ""
            for i, sarki in enumerate(state["queue"]):
                prefix = "▶️ " if i == state["index"] else "▫️ "
                liste_metni += f"{prefix} **{i+1}.** {sarki.filename}\n"
            embed.description = liste_metni
        
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="btn_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        state = self.cog.get_state(self.guild_id)
        if vc and state["index"] > 0:
            state["index"] -= 2  # play_next fonksiyonu çağrıldığında 1 ekleyeceği için 2 eksiltiyoruz
            vc.stop()  # Mevcut şarkıyı durdurduğumuz an after eventi tetiklenir ve play_next çalışır
            await asyncio.sleep(0.5) # Bekleme ekleyerek play_next'in indexi güncellemesine izin veriyoruz
            await self.update_panel(interaction)
        else:
            await interaction.response.send_message("❌ Önceki şarkı yok.", ephemeral=True)

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="btn_pause_resume")
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            if vc.is_paused():
                vc.resume()
                await interaction.response.send_message("▶️ Müzik devam ettiriliyor.", ephemeral=True)
            elif vc.is_playing():
                vc.pause()
                await interaction.response.send_message("⏸️ Müzik duraklatıldı.", ephemeral=True)
            # update_panel yerine direkt bildirim gönderilebilir veya panel güncellenebilir
        else:
            await interaction.response.send_message("❌ Çalan bir şey yok.", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="btn_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        state = self.cog.get_state(self.guild_id)
        if vc and state["index"] < len(state["queue"]) - 1:
            vc.stop()  # Mevcut şarkıyı durdurduğumuz an sonrakine geçer
            await asyncio.sleep(0.5) # Bekleme ekleyerek play_next'in indexi güncellemesine izin veriyoruz
            await self.update_panel(interaction)
        else:
            await interaction.response.send_message("❌ Sırada başka şarkı yok.", ephemeral=True)
            
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="btn_stop")
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            self.cog.states[self.guild_id] = {"queue": [], "index": -1}
            await vc.disconnect()
            await self.update_panel(interaction)
        else:
            await interaction.response.send_message("❌ Zaten seste değilim.", ephemeral=True)


class SesOynatici(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}

    def get_state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = {"queue": [], "index": -1}
        return self.states[guild_id]

    def play_next(self, guild_id):
        state = self.get_state(guild_id)
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        vc = guild.voice_client
        if not vc or not vc.is_connected():
            return
            
        state["index"] += 1
        if state["index"] >= len(state["queue"]):
            state["index"] = len(state["queue"]) - 1
            return
            
        attachment = state["queue"][state["index"]]
        
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        # FFmpeg kurulu olduğundan dolayı default executable 'ffmpeg' olarak kalabilir, garanti olsun diye ekliyoruz
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=attachment.url, **FFMPEG_OPTIONS)
        vc.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next, guild_id))

    @app_commands.command(name="play-file", description="Ses kanalında mp3 dosyası oynatır")
    @app_commands.describe(dosya="Oynatılacak ses dosyası (mp3, wav vb.)")
    async def play_file(self, interaction: discord.Interaction, dosya: discord.Attachment):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Önce bir ses kanalına girmelisiniz!", ephemeral=True)
            
        if not dosya.content_type or not dosya.content_type.startswith(('audio/', 'video/')):
            return await interaction.response.send_message("❌ Lütfen geçerli bir ses dosyası (örneğin .mp3) yükleyin.", ephemeral=True)

        await interaction.response.defer() # İşlem biraz sürebilir, timeout olmasın diye bekletiyoruz

        vc = interaction.guild.voice_client
        if not vc:
            try:
                vc = await interaction.user.voice.channel.connect()
            except Exception as e:
                return await interaction.followup.send(f"❌ Ses kanalına bağlanılamadı: {e}", ephemeral=True)
        elif vc.channel != interaction.user.voice.channel:
            await vc.move_to(interaction.user.voice.channel)

        state = self.get_state(interaction.guild_id)
        state["queue"].append(dosya)

        if not vc.is_playing() and not vc.is_paused():
            state["index"] = len(state["queue"]) - 2 
            await interaction.followup.send(f"🎵 **{dosya.filename}** oynatılıyor!")
            self.play_next(interaction.guild_id)
        else:
            await interaction.followup.send(f"✅ **{dosya.filename}** sıraya eklendi. (Sıra: {len(state['queue'])})")

    @app_commands.command(name="stop", description="Müziği durdurur ve botu sesten çıkarır")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            self.states[interaction.guild_id] = {"queue": [], "index": -1}
            await vc.disconnect()
            await interaction.response.send_message("🛑 Müzik durduruldu ve sesten çıkıldı.")
        else:
            await interaction.response.send_message("❌ Bot şu an bir ses kanalında değil.", ephemeral=True)

    @app_commands.command(name="lists", description="Müzik kuyruğunu ve kontrol panelini gösterir")
    async def lists(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if not state["queue"]:
            return await interaction.response.send_message("❌ Sırada hiç şarkı yok.", ephemeral=True)
            
        embed = discord.Embed(title="🎶 Müzik Kuyruğu", color=discord.Color.blue())
        liste_metni = ""
        for i, sarki in enumerate(state["queue"]):
            prefix = "▶️ " if i == state["index"] else "▫️ "
            liste_metni += f"{prefix} **{i+1}.** {sarki.filename}\n"
            
        embed.description = liste_metni
        
        view = MusicControlView(self, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(SesOynatici(bot))

