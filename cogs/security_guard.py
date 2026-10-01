import discord
from discord.ext import commands
import asyncio
from datetime import timedelta, datetime
import collections
import os
import json

# ================= KORUMA AYARLARI =================
SPAM_MESSAGE_LIMIT = 5
SPAM_TIME_SECONDS = 5
SPAM_TIMEOUT_DURATION = 5  # Dakika

RAID_JOIN_LIMIT = 5
RAID_TIME_SECONDS = 15

NUKE_ACTION_LIMIT = 3
NUKE_TIME_SECONDS = 30

# Kurucu rolü veya üst düzey yetkililer (Bu rollere sahip olanlar cezalardan muaf olur)
WHITELISTED_ROLES = [1529546007635824680, 1539167256246747186]

# Log kanalı (Buraya ID yazın veya bot açıldığında ilk bulduğu uygun kanala atar)
SECURITY_LOG_CHANNEL_ID = 1554830631408504842 # Çete log kanalı veya yeni bir log kanalı atanabilir. 
# Geçici olarak burayı boş bırakıp dinamik bulmasını da sağlayabiliriz, ama direkt yazmak güvenlidir.

class SecurityGuard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Anti-Spam (Kullanıcı ID -> Zaman Damgaları)
        self.user_messages = collections.defaultdict(list)
        
        # Anti-Raid (Zaman Damgaları)
        self.recent_joins = []
        self.raid_mode = False
        
        # Anti-Nuke (Yetkili ID -> Eylem Zaman Damgaları)
        self.admin_actions = collections.defaultdict(list)
        
        self.log_channel = None

    async def get_log_channel(self, guild):
        if self.log_channel:
            return self.log_channel
            
        kanal = guild.get_channel(SECURITY_LOG_CHANNEL_ID)
        if kanal:
            self.log_channel = kanal
            return kanal
            
        # Eğer belirtilen ID yoksa, içinde 'log' veya 'guvenlik' geçen bir kanal bul
        for channel in guild.text_channels:
            if "güvenlik" in channel.name.lower() or "security" in channel.name.lower():
                self.log_channel = channel
                return channel
                
        return None

    def is_whitelisted(self, member):
        if member.id == member.guild.owner_id:
            return True
        for role in member.roles:
            if role.id in WHITELISTED_ROLES:
                return True
            if role.permissions.administrator:
                # Normalde adminler anti-nuke ile denetlenir ama anti-spam'dan muaf olabilir. 
                # Nuke koruması adminleri de kapsar! (Hesap çalınmasına karşı)
                pass
        return False

    async def alert(self, guild, title, description, color=discord.Color.red()):
        kanal = await self.get_log_channel(guild)
        if kanal:
            embed = discord.Embed(title=f"🛡️ {title}", description=description, color=color)
            embed.timestamp = discord.utils.utcnow()
            try:
                await kanal.send(content="@here 🚨 **GÜVENLİK UYARISI**", embed=embed)
            except:
                pass

    # ================= ANTI-SPAM =================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if self.is_whitelisted(message.author):
            return

        uid = message.author.id
        now = datetime.now()
        
        self.user_messages[uid].append((now, message))
        
        # Sadece son SPAM_TIME_SECONDS saniye içindeki mesajları tut
        self.user_messages[uid] = [(t, msg) for t, msg in self.user_messages[uid] if (now - t).total_seconds() <= SPAM_TIME_SECONDS]
        
        if len(self.user_messages[uid]) > SPAM_MESSAGE_LIMIT:
            # Spam tespit edildi!
            messages_to_delete = [msg for _, msg in self.user_messages[uid]]
            self.user_messages[uid].clear()
            
            try:
                await message.channel.delete_messages(messages_to_delete)
            except:
                pass
                
            try:
                await message.author.timeout(timedelta(minutes=SPAM_TIMEOUT_DURATION), reason="Anti-Spam: Hızlı mesaj gönderme.")
                await message.channel.send(f"⚠️ {message.author.mention}, spam yaptığınız için {SPAM_TIMEOUT_DURATION} dakika susturuldunuz!", delete_after=10)
                await self.alert(message.guild, "Anti-Spam Tetiklendi", f"👤 **Kullanıcı:** {message.author.mention}\n📍 **Kanal:** {message.channel.mention}\n⚡ **Sebep:** Kısa sürede çok fazla mesaj.")
            except discord.Forbidden:
                pass

    # ================= ANTI-RAID (Spawn Koruması) =================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        now = datetime.now()
        self.recent_joins.append(now)
        
        # Son RAID_TIME_SECONDS içindeki girişleri say
        self.recent_joins = [t for t in self.recent_joins if (now - t).total_seconds() <= RAID_TIME_SECONDS]
        
        if len(self.recent_joins) > RAID_JOIN_LIMIT:
            if not self.raid_mode:
                self.raid_mode = True
                await self.alert(member.guild, "Anti-Raid / Spawn Koruması Aktif!", f"🚨 Sunucuya kısa sürede {RAID_JOIN_LIMIT}'den fazla giriş oldu!\nBot saldırısı (Raid) şüphesiyle yeni katılanlar otomatik olarak atılacak. Tehlike geçene kadar bu durum devam edecek.", discord.Color.dark_red())
            
        if self.raid_mode:
            try:
                await member.send("Sunucumuzda şu an yoğun bir giriş tespit edildiği için (Raid Modu) güvenlik amacıyla atıldınız. Lütfen bir süre sonra tekrar katılmayı deneyin.")
            except:
                pass
            try:
                await member.kick(reason="Anti-Raid Sistemi: Sunucu saldırı altında.")
            except:
                pass

            # 30 saniye yeni giriş olmazsa raid modunu kapat
            await asyncio.sleep(30)
            now_check = datetime.now()
            if not any((now_check - t).total_seconds() <= 30 for t in self.recent_joins):
                if self.raid_mode:
                    self.raid_mode = False
                    await self.alert(member.guild, "Anti-Raid Modu Kapatıldı", "✅ Tehlike geçti, sunucu girişleri tekrar normale döndü.", discord.Color.green())


    # ================= ANTI-NUKE =================
    async def check_nuke(self, guild, action_type, reason):
        await asyncio.sleep(2) # Discord logunun düşmesi için ufak bir bekleme
        
        try:
            async for entry in guild.audit_logs(limit=1, action=action_type):
                user = entry.user
                if user.bot or user.id == guild.owner_id:
                    continue
                
                # Kurucu rolü varsa dokunma (Ama hesabının çalınma ihtimaline karşı sadece Owner_id'yi muaf tutmak daha güvenlidir)
                if user.id in [1529546007635824680]:
                    pass # İstisnaya izin vermek istersen burayı ayarlayabilirsin, ama güvenlik için herkesi denetlemek iyidir.
                
                now = datetime.now()
                self.admin_actions[user.id].append(now)
                
                self.admin_actions[user.id] = [t for t in self.admin_actions[user.id] if (now - t).total_seconds() <= NUKE_TIME_SECONDS]
                
                if len(self.admin_actions[user.id]) >= NUKE_ACTION_LIMIT:
                    self.admin_actions[user.id].clear()
                    
                    # Nuke Tespit Edildi! Yöneticiyi cezalandır!
                    await self.alert(guild, "ANTI-NUKE TETİKLENDİ!", f"🚨 **Tespiti Yapılan Yetkili:** {user.mention} ({user.id})\n❌ **Eylem:** Çok kısa sürede çok fazla sunucu yapısına zarar verdi ({reason}).\n⚠️ **Otomatik İşlem:** Kullanıcının tüm yetkileri elinden alındı ve sunucudan uzaklaştırıldı!", discord.Color.dark_red())
                    
                    try:
                        # Yetkilerini Al & At
                        await user.ban(reason="Anti-Nuke: Sunucuya Zarar Verme Girişimi")
                    except Exception as e:
                        print(f"Anti-nuke ban hatası: {e}")
                        try:
                            # Ban yetkisi yoksa rolleri sil
                            silinecek = [r for r in user.roles if r.name != "@everyone"]
                            await user.remove_roles(*silinecek, reason="Anti-Nuke Koruması")
                        except:
                            pass
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.check_nuke(channel.guild, discord.AuditLogAction.channel_delete, "Kanal Silme")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.check_nuke(role.guild, discord.AuditLogAction.role_delete, "Rol Silme")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.check_nuke(guild, discord.AuditLogAction.ban, "Kullanıcı Banlama")

async def setup(bot):
    await bot.add_cog(SecurityGuard(bot))
