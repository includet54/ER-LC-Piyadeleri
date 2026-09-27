import discord
from discord.ext import commands, tasks
import aiohttp
import os
from datetime import datetime

RADAR_KANAL_ID = 1553721461389266974

# Bölge sistemi (Posta kodları vb.) daha sonra buraya entegre edilebilir.

class LiveRadar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.takip_edilen_mesajlar = {}  # {"OyuncuAdı": mesaj_objesi}
        self.radar_loop.start()

    def cog_unload(self):
        self.radar_loop.cancel()

    @tasks.loop(seconds=10)
    async def radar_loop(self):
        if not self.bot.is_ready():
            return
            
        api_key = os.getenv("ERLC_API_KEY")
        if not api_key:
            print("[RADAR HATA] ERLC_API_KEY bulunamadı! Railway Variables kısmını kontrol et.", flush=True)
            return

        kanal = self.bot.get_channel(RADAR_KANAL_ID)
        if not kanal:
            print(f"[RADAR HATA] Kanal bulunamadı! ID: {RADAR_KANAL_ID}. Botun kanalı görme yetkisi var mı?", flush=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Server-Key': api_key}
                async with session.get('https://api.erlc.gg/v2/server', headers=headers, timeout=5) as resp:
                    if resp.status != 200:
                        print(f"[RADAR HATA] API'ye bağlanılamadı. HTTP Kodu: {resp.status}", flush=True)
                        return
                    data = await resp.json()
                    players = data.get("Players", [])
                    print(f"[RADAR BİLGİ] API'den {len(players)} oyuncu çekildi.", flush=True)
        except Exception as e:
            print(f"[RADAR HATA] API isteği sırasında bir çökme yaşandı: {e}", flush=True)
            return

        aktif_oyuncular = {}
        for p in players:
            player_str = p.get("Player", "")
            if not player_str:
                continue
            
            isim = player_str.split(':')[0]
            loc = p.get("Location", {})
            x = loc.get("LocationX", 0)
            y = loc.get("LocationY", 0)
            z = loc.get("LocationZ", 0)
            
            aktif_oyuncular[isim] = {"x": x, "y": y, "z": z}

        # 1. Oyuncuların mesajlarını oluştur veya güncelle
        for isim, loc in aktif_oyuncular.items():
            zaman = datetime.now().strftime("%H:%M:%S")
            
            embed = discord.Embed(
                title=f"📡 Radar: {isim}",
                description=(
                    f"**📍 Konum (Koordinatlar):**\n"
                    f"X: `{loc['x']}` | Y: `{loc['y']}` | Z: `{loc['z']}`\n\n"
                    f"🔄 *Son Güncelleme: {zaman}*"
                ),
                color=discord.Color.blue()
            )
            
            if isim in self.takip_edilen_mesajlar:
                try:
                    msg = self.takip_edilen_mesajlar[isim]
                    await msg.edit(embed=embed)
                except discord.NotFound:
                    # Mesaj elle silinmişse yenisini gönder
                    msg = await kanal.send(embed=embed)
                    self.takip_edilen_mesajlar[isim] = msg
                except Exception as e:
                    print(f"[RADAR HATA] Mesaj güncellenirken hata: {e}", flush=True)
            else:
                try:
                    # Yeni bağlanan oyuncu için log mesajı oluştur
                    msg = await kanal.send(embed=embed)
                    self.takip_edilen_mesajlar[isim] = msg
                    print(f"[RADAR BAŞARILI] {isim} için mesaj gönderildi.", flush=True)
                except Exception as e:
                    print(f"[RADAR HATA] Kanala mesaj atılamadı! Yetki hatası olabilir: {e}", flush=True)

        # 2. Sunucudan çıkan oyuncuları temizle ve mesajlarını inaktif (Kırmızı) yap
        cikanlar = [isim for isim in self.takip_edilen_mesajlar if isim not in aktif_oyuncular]
        for isim in cikanlar:
            msg = self.takip_edilen_mesajlar.pop(isim)
            try:
                embed = msg.embeds[0]
                embed.color = discord.Color.red()
                embed.title = f"🔴 Çevrimdışı: {isim}"
                embed.description = "❌ Oyuncu sunucudan ayrıldı. İzleme sonlandırıldı."
                await msg.edit(embed=embed)
            except Exception as e:
                print(f"[RADAR HATA] Çevrimdışı mesajı düzenlenemedi: {e}", flush=True)

async def setup(bot):
    print("[RADAR BİLGİ] live_radar modülü sisteme yükleniyor...", flush=True)
    await bot.add_cog(LiveRadar(bot))
