import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
from datetime import datetime, timezone, timedelta

RADAR_KANAL_ID = 1553721461389266974
RDM_LOG_KANAL_ID = 1554099605837185044

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BOLGELER_FILE = os.path.join(DATA_DIR, "bolgeler.json")
KILLER_FILE = os.path.join(DATA_DIR, "gunluk_killer.json")

# Dosya okunamasa bile Safezone kontrolünün asla aksamaması için yedek tanımlar
TANIMLI_BOLGELER = {
    "gun_shop": {
        "name": "Gunshop Etkileşimli Bölge (Safezone)",
        "postal_codes": ["227"],
        "bounds": {"min_x": 1095.33, "max_x": 1129.06, "min_z": 3388.36, "max_z": 3411.18}
    },
    "police_department": {
        "name": "Polis Departmanı (Safezone)",
        "postal_codes": ["310", "316", "317"],
        "bounds": {"min_x": 2809.82, "max_x": 2946.46, "min_z": 3473.87, "max_z": 3562.42}
    },
    "fire_department": {
        "name": "Fire Departman (Safezone)",
        "postal_codes": ["228", "229"],
        "bounds": {"min_x": 1207.34, "max_x": 1358.66, "min_z": 3306.45, "max_z": 3459.93}
    },
    "city_spawn": {
        "name": "City Spawn (Safezone)",
        "postal_codes": ["210", "211"],
        "bounds": {"min_x": 1464.1, "max_x": 1616.43, "min_z": 3843.23, "max_z": 3935.5}
    }
}

def yukle_json(yol, varsayilan=None):
    if varsayilan is None:
        varsayilan = {}
    if os.path.exists(yol):
        try:
            with open(yol, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if d else varsayilan
        except Exception:
            return varsayilan
    return varsayilan

def kaydet_json(yol, veri):
    try:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DOSYA HATA] {yol} kaydedilemedi: {e}", flush=True)

def bolge_kontrol(x, z, postal, bolgeler):
    # 1. Koordinat ile kontrol (15 birim esneklik payı ile)
    if isinstance(x, (int, float)) and isinstance(z, (int, float)):
        for b_id, b_info in bolgeler.items():
            bounds = b_info.get("bounds", {})
            min_x = bounds.get("min_x")
            max_x = bounds.get("max_x")
            min_z = bounds.get("min_z")
            max_z = bounds.get("max_z")
            if min_x is not None and max_x is not None and min_z is not None and max_z is not None:
                if (min_x - 15) <= x <= (max_x + 15) and (min_z - 15) <= z <= (max_z + 15):
                    return b_info.get("name", b_id)

    # 2. Posta Kodu ile kontrol (Koordinat sınırın azıcık dışındaysa bile posta kodu eşleşirse yakalar)
    if postal and postal != "-":
        for b_id, b_info in bolgeler.items():
            codes = [str(p) for p in b_info.get("postal_codes", [])]
            if str(postal) in codes:
                return b_info.get("name", b_id)

    return None

class LiveRadar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.takip_edilen_mesajlar = {}  # {"OyuncuAdı": mesaj_objesi}
        self.son_konumlar = {}           # {"OyuncuAdı": {"x": ..., "z": ..., "postal": ..., "street": ...}}
        
        # İşlenen kill loglarını benzersiz ID ile takip ediyoruz (Tekrarları ve saat kayması sorunlarını önler)
        kill_data = yukle_json(KILLER_FILE, {"islenen_killer": [], "gunluk_safezone_ihlalleri": {}})
        self.islenen_killer = set(kill_data.get("islenen_killer", []))
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
                # ER:LC API'sinden hem anlık oyuncu konumlarını hem de kill loglarını tek istekte çekiyoruz
                async with session.get('https://api.erlc.gg/v2/server?Players=true&KillLogs=true', headers=headers, timeout=5) as resp:
                    if resp.status != 200:
                        print(f"[RADAR HATA] API'ye bağlanılamadı. HTTP Kodu: {resp.status}", flush=True)
                        return
                    data = await resp.json()
                    players = data.get("Players", [])
                    kill_logs = data.get("KillLogs", [])
                    current_players_count = data.get("CurrentPlayers", "Bilinmiyor")
                    print(f"[RADAR BİLGİ] Sunucuda {current_players_count} kişi var. ({len(players)} detaylı, {len(kill_logs)} kill logu)", flush=True)
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
            y = loc.get("LocationY", loc.get("Y", "-"))
            z = loc.get("LocationZ", 0)
            posta_kodu = loc.get("PostalCode", "-")
            sokak = loc.get("StreetName", "-")
            bina = loc.get("BuildingNumber", "-")
            
            aktif_oyuncular[isim] = {
                "x": round(x, 2) if isinstance(x, (int, float)) else x,
                "y": round(y, 2) if isinstance(y, (int, float)) else y,
                "z": round(z, 2) if isinstance(z, (int, float)) else z,
                "postal": posta_kodu,
                "street": sokak,
                "building": bina
            }

        self.son_konumlar.update(aktif_oyuncular)

        # 1. Oyuncuların mesajlarını oluştur veya güncelle
        tz_tr = timezone(timedelta(hours=3))
        for isim, loc in aktif_oyuncular.items():
            now_tr = datetime.now(tz_tr)
            zaman = now_tr.strftime("%H:%M:%S")
            ts_unix = int(now_tr.timestamp())
            
            embed = discord.Embed(
                title=f"📡 Radar: {isim}",
                description=(
                    f"**📍 Konum (Koordinatlar):**\n"
                    f"X: `{loc['x']}` | Z: `{loc['z']}`" + (f" | Y: `{loc['y']}`" if loc['y'] != "-" else "") + "\n\n"
                    f"📮 **Posta Kodu:** `{loc['postal']}`\n"
                    f"🛣️ **Cadde / Sokak:** `{loc['street']}` (No: `{loc['building']}`)\n\n"
                    f"🔄 *Son Güncelleme: {zaman} (<t:{ts_unix}:R>)*"
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

        # 3. ER:LC Kill Loglarını ve Safezone İhlallerini Kontrol Et
        if kill_logs:
            rdm_kanal = self.bot.get_channel(RDM_LOG_KANAL_ID)
            if not rdm_kanal:
                try:
                    rdm_kanal = await self.bot.fetch_channel(RDM_LOG_KANAL_ID)
                except Exception as e:
                    print(f"[SAFEZONE HATA] {RDM_LOG_KANAL_ID} kanalı bulunamadı: {e}", flush=True)
                    rdm_kanal = None

            bolgeler_data = yukle_json(BOLGELER_FILE, TANIMLI_BOLGELER)
            if not bolgeler_data:
                bolgeler_data = TANIMLI_BOLGELER
            kill_tracker = yukle_json(KILLER_FILE, {"islenen_killer": [], "gunluk_safezone_ihlalleri": {}})
            if not hasattr(self, "islenen_killer"):
                self.islenen_killer = set(kill_tracker.get("islenen_killer", []))

            simdi_unix = int(datetime.now().timestamp())
            bugun = datetime.now(tz_tr).strftime("%Y-%m-%d")

            for k in kill_logs:
                ts = k.get("Timestamp", 0)
                killer_raw = str(k.get("Killer", "Bilinmiyor:0"))
                victim_raw = str(k.get("Killed", "Bilinmiyor:0"))
                kill_id = f"{killer_raw}_{victim_raw}_{ts}"

                # Zaten işlendiyse atla
                if kill_id in self.islenen_killer:
                    continue

                # 15 dakikadan daha eski olan geçmiş cinayetleri atla (bot yeniden başlarsa eski kayıtları spamlamasın)
                if ts < (simdi_unix - 900):
                    self.islenen_killer.add(kill_id)
                    continue

                # Yeni cinayet yakalandı!
                self.islenen_killer.add(kill_id)
                print(f"[KILL LOG YAKALANDI] {killer_raw} -> {victim_raw} (TS: {ts})", flush=True)

                killer_name = killer_raw.split(":")[0] if ":" in killer_raw else killer_raw
                killer_id = killer_raw.split(":")[1] if ":" in killer_raw else "-"

                victim_name = victim_raw.split(":")[0] if ":" in victim_raw else victim_raw
                victim_id = victim_raw.split(":")[1] if ":" in victim_raw else "-"

                # Silah bilgisi
                silah = k.get("Weapon") or k.get("Tool") or k.get("Cause") or "Ateşli Silah / Belirtilmemiş"

                # Konum tespiti (Öncelikle katilin, yoksa kurbanın son radardaki konumu)
                loc = self.son_konumlar.get(killer_name) or self.son_konumlar.get(victim_name)
                x_val = loc.get("x", "-") if loc else "-"
                z_val = loc.get("z", "-") if loc else "-"
                postal = loc.get("postal", "-") if loc else "-"
                street = loc.get("street", "-") if loc else "-"
                bina = loc.get("building", "-") if loc else "-"

                # Safezone kontrolü (Hem X/Z koordinatları hem de Posta Kodu kontrol edilir)
                safezone = bolge_kontrol(x_val, z_val, postal, bolgeler_data) if loc else None
                print(f"[SAFEZONE KONTROL] Katil: {killer_name} | Konum: ({x_val}, {z_val}) | Posta: {postal} | Tespit Edilen Bölge: {safezone}", flush=True)

                if not safezone:
                    print(f"[SAFEZONE DIŞI] Olay güvenli bölge dışında olduğu için log atlanıyor.", flush=True)
                    continue

                # Günlük Safezone ihlal sayacı
                gunluk_sozluk = kill_tracker.setdefault("gunluk_safezone_ihlalleri", {}).setdefault(bugun, {})
                ihlal_sayi = gunluk_sozluk.get(killer_name, 0) + 1
                gunluk_sozluk[killer_name] = ihlal_sayi

                # Safezone İhlal Embed'i
                embed = discord.Embed(
                    title="🚨 SAFEZONE İHLALİ TESPİT EDİLDİ",
                    description=f"**{killer_name}**, korumalı bölge olan **{safezone}** sınırları içerisinde saldırı/cinayet gerçekleştirdi!",
                    color=discord.Color.red(),
                    timestamp=datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(tz_tr)
                )
                embed.add_field(name="👤 İhlal Eden (Saldırgan)", value=f"**{killer_name}** `(ID: {killer_id})`", inline=True)
                embed.add_field(name="🎯 Mağdur (Kurban)", value=f"**{victim_name}** `(ID: {victim_id})`", inline=True)
                embed.add_field(name="🔫 Kullanılan Silah", value=f"`{silah}`", inline=True)

                konum_metni = (
                    f"**🛡️ İhlal Bölgesi:** `{safezone}`\n"
                    f"**📍 Koordinatlar:** X: `{x_val}` | Z: `{z_val}`\n"
                    f"**📮 Posta Kodu:** `{postal}`\n"
                    f"**🛣️ Cadde / Bina:** `{street}` (No: `{bina}`)"
                )
                embed.add_field(name="📍 Olay Yeri Detayları", value=konum_metni, inline=False)
                embed.add_field(name="📊 Günlük Safezone İhlali", value=f"Bugün **{ihlal_sayi}.** kez tekrarladı", inline=True)
                embed.set_footer(text="ER-LC Piyadeleri • Safezone Güvenlik Takip Sistemi")

                if rdm_kanal:
                    try:
                        await rdm_kanal.send(embed=embed)
                        print(f"[SAFEZONE İHLALİ] {killer_name} -> {victim_name} ({safezone}) logu kanala başarıyla gönderildi!", flush=True)
                    except Exception as e:
                        print(f"[SAFEZONE LOG HATA] Kanala mesaj atılamadı! Yetkiyi kontrol et: {e}", flush=True)

            # Son 200 işlenen kill ID'sini sakla
            kill_tracker["islenen_killer"] = list(self.islenen_killer)[-200:]
            kaydet_json(KILLER_FILE, kill_tracker)

async def setup(bot):
    print("[RADAR BİLGİ] live_radar modülü sisteme yükleniyor...", flush=True)
    await bot.add_cog(LiveRadar(bot))
