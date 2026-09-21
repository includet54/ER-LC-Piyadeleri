import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import random
from datetime import datetime, timedelta

DATA_FILE = "data/cete_data.json"
PENDING_FILE = "data/cete_pending.json"
COLORS_FILE = "data/colors.json"

BOSS_ROLE_ID = 1551552841716334592
UNDERBOSS_ROLE_ID = 1551553107492601876
LOG_CHANNEL_ID = 1551547117024190474
BOT_KOMUT_CHANNEL_ID = 1544809399296589885
GANG_PANEL_CHANNEL_ID = 1551345902868889671

VALID_PARSELLER = ["700","701","702","703","704","705","706","709","504","505","506","1103","1109","1112"]

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hex_to_discord_color(hex_str):
    hex_str = hex_str.strip().lstrip('#')
    return discord.Color(int(hex_str, 16))

def is_user_in_any_gang(user_id):
    cete_data = load_json(DATA_FILE)
    uid = str(user_id)
    for cete_id, cete in cete_data.items():
        if str(cete["boss"]) == uid or uid in cete.get("underbosses", []) or uid in cete.get("members", []):
            return True
    return False

# --- GANG CREATION VIEWS & MODALS ---

class AdminRejectModal(discord.ui.Modal, title="Çete Reddetme Sebebi"):
    sebep = discord.ui.TextInput(
        label="Reddedilme Sebebi",
        style=discord.TextStyle.paragraph,
        placeholder="Neden reddedildiğini yazınız...",
        required=True
    )

    def __init__(self, request_id: str):
        super().__init__()
        self.request_id = request_id

    async def on_submit(self, interaction: discord.Interaction):
        pending = load_json(PENDING_FILE)
        if self.request_id not in pending:
            return await interaction.response.send_message("Talebin süresi dolmuş veya zaten işlem yapılmış.", ephemeral=True)
        
        req = pending[self.request_id]
        boss_id = req["boss"]
        
        # Log mesajını güncelle
        try:
            log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
            msg = await log_channel.fetch_message(req["log_msg_id"])
            embed = msg.embeds[0]
            embed.color = discord.Color.red()
            embed.title = f"❌ REDDEDİLDİ: {req['name']}"
            embed.add_field(name="Reddeden Yetkili", value=interaction.user.mention, inline=False)
            embed.add_field(name="Sebep", value=self.sebep.value, inline=False)
            await msg.edit(embed=embed, view=None)
        except:
            pass

        # Boss'a bildir
        try:
            komut_kanal = interaction.client.get_channel(BOT_KOMUT_CHANNEL_ID)
            await komut_kanal.send(f"❌ <@{boss_id}>, **{req['name']}** adlı çete kurma talebiniz yetkililer tarafından reddedildi.\n**Sebep:** {self.sebep.value}")
        except:
            pass

        del pending[self.request_id]
        save_json(PENDING_FILE, pending)
        await interaction.response.send_message("Talep başarıyla reddedildi.", ephemeral=True)


class AdminApprovalView(discord.ui.View):
    def __init__(self, request_id: str):
        super().__init__(timeout=None)
        self.request_id = request_id

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.green, custom_id="admin_gang_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pending = load_json(PENDING_FILE)
        if self.request_id not in pending:
            return await interaction.response.send_message("Bu talep artık geçerli değil.", ephemeral=True)
        
        req = pending[self.request_id]
        boss_id = int(req["boss"])
        guild = interaction.guild
        
        # Kabul edenleri al
        accepted_members = []
        for uid_str, status in req["invited"].items():
            if status == "accepted":
                accepted_members.append(int(uid_str))
        
        await interaction.response.defer()

        # 1. Rolü Oluştur
        colors_data = load_json(COLORS_FILE)
        hex_color = "#ffffff"
        for c in colors_data:
            if str(c["ID"]) == str(req["color_id"]):
                hex_color = c["Hex (Web RGB)"]
                break
        
        new_role = await guild.create_role(
            name=req["name"],
            color=hex_to_discord_color(hex_color),
            reason="Çete sistemi otomatik kurulum"
        )
        
        boss_role = guild.get_role(BOSS_ROLE_ID)

        # 2. Üyelere Rolleri Ver
        members_to_add = [boss_id] + accepted_members
        for uid in members_to_add:
            member = guild.get_member(uid)
            if member:
                await member.add_roles(new_role)
                if uid == boss_id and boss_role:
                    await member.add_roles(boss_role)
        
        # 3. Kategorileri Bul / Oluştur
        text_category = discord.utils.get(guild.categories, name="Çeteler Sınırsız Ticket")
        if not text_category:
            text_category = await guild.create_category("Çeteler Sınırsız Ticket")
            
        voice_category = discord.utils.get(guild.categories, name="Çete Ses kanalları")
        if not voice_category:
            voice_category = await guild.create_category("Çete Ses kanalları")

        # İzinler
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, connect=False),
            new_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True)
        }

        # 4. Kanalları Oluştur
        text_channel_name = f"{req['name'].replace(' ', '-').lower()}_sınırsız_ticket"
        text_channel = await guild.create_text_channel(text_channel_name, category=text_category, overwrites=overwrites)
        
        freq_code = random.randint(100, 999)
        voice_channel_name = f"{req['name']} 📻{freq_code}"
        voice_channel = await guild.create_voice_channel(voice_channel_name, category=voice_category, overwrites=overwrites)

        # 5. Mesaj Gönder
        info_embed = discord.Embed(title=f"🛡️ {req['name']} Çetesi Kuruldu!", color=new_role.color)
        info_embed.add_field(name="Boss", value=f"<@{boss_id}>", inline=False)
        info_embed.add_field(name="Üyeler", value=" ".join([f"<@{u}>" for u in accepted_members]), inline=False)
        info_embed.add_field(name="Parsel", value=req["parsel"], inline=False)
        info_embed.add_field(name="Hikaye", value=req["story"], inline=False)
        info_embed.set_footer(text="Bu mesaj çeteye yeni üyeler eklendikçe güncellenecektir.")
        info_msg = await text_channel.send(embed=info_embed)

        # 6. JSON'a Kaydet
        cete_data = load_json(DATA_FILE)
        gang_id = str(new_role.id)
        cete_data[gang_id] = {
            "name": req["name"],
            "color_id": req["color_id"],
            "boss": str(boss_id),
            "underbosses": [],
            "members": [str(u) for u in accepted_members],
            "parsel": req["parsel"],
            "text_channel": str(text_channel.id),
            "voice_channel": str(voice_channel.id),
            "role_id": str(new_role.id),
            "info_msg_id": str(info_msg.id)
        }
        save_json(DATA_FILE, cete_data)
        
        # 7. Log Mesajını Güncelle
        try:
            log_channel = guild.get_channel(LOG_CHANNEL_ID)
            msg = await log_channel.fetch_message(req["log_msg_id"])
            embed = msg.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"✅ ONAYLANDI: {req['name']}"
            embed.add_field(name="Onaylayan Yetkili", value=interaction.user.mention, inline=False)
            await msg.edit(embed=embed, view=None)
        except:
            pass

        del pending[self.request_id]
        save_json(PENDING_FILE, pending)

        komut_kanal = guild.get_channel(BOT_KOMUT_CHANNEL_ID)
        await komut_kanal.send(f"🎉 <@{boss_id}>, **{req['name']}** çeteniz başarıyla onaylandı ve kuruldu! Kanallarınıza göz atabilirsiniz.")

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.red, custom_id="admin_gang_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminRejectModal(self.request_id))


class GangInviteView(discord.ui.View):
    def __init__(self, request_id: str, invited_user_id: str):
        super().__init__(timeout=None)
        self.request_id = request_id
        self.invited_user_id = str(invited_user_id)

    async def handle_response(self, interaction: discord.Interaction, accepted: bool):
        if str(interaction.user.id) != self.invited_user_id:
            return await interaction.response.send_message("Bu davet sizin için değil!", ephemeral=True)
            
        pending = load_json(PENDING_FILE)
        if self.request_id not in pending:
            return await interaction.response.send_message("Bu çete talebi artık geçerli değil (zaman aşımı veya onaylandı).", ephemeral=True)
            
        req = pending[self.request_id]
        if req["invited"].get(self.invited_user_id) != "pending":
            return await interaction.response.send_message("Bu davete zaten yanıt verdiniz.", ephemeral=True)
            
        req["invited"][self.invited_user_id] = "accepted" if accepted else "rejected"
        save_json(PENDING_FILE, pending)
        
        # Butonları devre dışı bırak
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"{interaction.message.content}\n**Yanıtınız:** {'✅ Kabul Edildi' if accepted else '❌ Reddedildi'}", view=self)
        
        await self.update_log_message(interaction, req)

    @discord.ui.button(label="Onaylıyorum", style=discord.ButtonStyle.green, custom_id="invite_accept")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, True)

    @discord.ui.button(label="Onaylamıyorum", style=discord.ButtonStyle.red, custom_id="invite_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, False)

    async def update_log_message(self, interaction, req):
        accepted_count = sum(1 for status in req["invited"].values() if status == "accepted")
        rejected_count = sum(1 for status in req["invited"].values() if status == "rejected")
        total_invited = len(req["invited"])
        
        try:
            log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
            msg = await log_channel.fetch_message(req["log_msg_id"])
            
            embed = discord.Embed(title=f"Çete Başvurusu: {req['name']}", color=discord.Color.yellow())
            if accepted_count >= 3:
                embed.color = discord.Color.default() # Beyaz
            
            embed.add_field(name="Boss", value=f"<@{req['boss']}>", inline=False)
            embed.add_field(name="Çete Rengi (ID)", value=req['color_id'], inline=True)
            embed.add_field(name="Parsel", value=req['parsel'], inline=True)
            embed.add_field(name="Davet Edilen", value=str(total_invited), inline=True)
            embed.add_field(name="Onaylayan", value=str(accepted_count), inline=True)
            embed.add_field(name="Reddeden", value=str(rejected_count), inline=True)
            
            if accepted_count >= 3:
                embed.description = "✅ Yeterli onaya ulaşıldı. Yetkili onayı bekleniyor."
                view = AdminApprovalView(self.request_id)
                await msg.edit(embed=embed, view=view)
            elif (total_invited - rejected_count) < 3:
                # İptal et
                embed.color = discord.Color.red()
                embed.description = "❌ Yeterli kişi onaylamadığı için sistem tarafından otomatik reddedildi."
                await msg.edit(embed=embed, view=None)
                
                pending = load_json(PENDING_FILE)
                del pending[self.request_id]
                save_json(PENDING_FILE, pending)
                
                komut_kanal = interaction.client.get_channel(BOT_KOMUT_CHANNEL_ID)
                await komut_kanal.send(f"❌ <@{req['boss']}>, **{req['name']}** çeteniz için yeterli onay alınamadığından başvuru iptal edildi.")
            else:
                embed.description = "⏳ Üyelerin onayı bekleniyor..."
                await msg.edit(embed=embed)
        except Exception as e:
            print(f"Log message update error: {e}")

class GangCreateModal(discord.ui.Modal, title="Yeni Çete Oluştur"):
    cete_adi = discord.ui.TextInput(label="Çetenizin Adı", max_length=50, required=True)
    cete_rengi = discord.ui.TextInput(label="Çetenizin Rengi (Sayı ID giriniz)", max_length=5, placeholder="Örn: 27", required=True)
    parsel_kodu = discord.ui.TextInput(label="Çetenizin Parsel Kodu", max_length=10, placeholder="Örn: 700", required=True)
    uyeler = discord.ui.TextInput(label="Başlangıç Üyeleri (En az 3 kişi etiketle)", style=discord.TextStyle.paragraph, placeholder="@Polat @Ahmet @Mehmet", required=True)
    hikaye = discord.ui.TextInput(label="Oluşma Hikayesi", style=discord.TextStyle.paragraph, placeholder="Kısa bir hikaye...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Validations
        if is_user_in_any_gang(interaction.user.id):
            return await interaction.response.send_message("❌ Zaten bir çetedesiniz veya başka bir çetenin boss'usunuz!", ephemeral=True)
        
        # Parsel
        if self.parsel_kodu.value.strip() not in VALID_PARSELLER:
            return await interaction.response.send_message(f"❌ Geçersiz parsel kodu! Geçerli kodlar: {', '.join(VALID_PARSELLER)}", ephemeral=True)
        
        # Renk
        colors_data = load_json(COLORS_FILE)
        valid_color = False
        for c in colors_data:
            if str(c["ID"]) == self.cete_rengi.value.strip():
                valid_color = True
                break
        if not valid_color:
            return await interaction.response.send_message("❌ Geçersiz Renk ID girdiniz. Lütfen görseldeki numaralardan birini yazın.", ephemeral=True)

        # Üyeler
        mentions = re.findall(r'<@!?(\d+)>', self.uyeler.value)
        unique_members = list(set(mentions))
        if str(interaction.user.id) in unique_members:
            unique_members.remove(str(interaction.user.id)) # Boss kendini davet edemez
            
        if len(unique_members) < 3:
            return await interaction.response.send_message("❌ Lütfen en az 3 GEÇERLİ kişiyi etiketlediğinizden emin olun (Kendiniz hariç).", ephemeral=True)
            
        for uid in unique_members:
            if is_user_in_any_gang(uid):
                return await interaction.response.send_message(f"❌ Etiketlediğiniz üyelerden biri (<@{uid}>) zaten bir çetede!", ephemeral=True)

        # Save Pending Request
        request_id = str(interaction.id)
        pending_data = load_json(PENDING_FILE)
        
        # Send Log Message
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return await interaction.response.send_message("Log kanalı bulunamadı, yetkililere bildirin.", ephemeral=True)
            
        embed = discord.Embed(title=f"Çete Başvurusu: {self.cete_adi.value}", description="⏳ Üyelerin onayı bekleniyor...", color=discord.Color.yellow())
        embed.add_field(name="Boss", value=interaction.user.mention, inline=False)
        embed.add_field(name="Çete Rengi (ID)", value=self.cete_rengi.value, inline=True)
        embed.add_field(name="Parsel", value=self.parsel_kodu.value, inline=True)
        embed.add_field(name="Davet Edilen", value=str(len(unique_members)), inline=True)
        embed.add_field(name="Onaylayan", value="0", inline=True)
        embed.add_field(name="Reddeden", value="0", inline=True)
        
        log_msg = await log_channel.send(embed=embed)

        pending_data[request_id] = {
            "name": self.cete_adi.value.strip(),
            "color_id": self.cete_rengi.value.strip(),
            "parsel": self.parsel_kodu.value.strip(),
            "boss": str(interaction.user.id),
            "story": self.hikaye.value.strip(),
            "log_msg_id": log_msg.id,
            "invited": {uid: "pending" for uid in unique_members},
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        save_json(PENDING_FILE, pending_data)

        # Davetiyeleri at
        bot_komut = interaction.client.get_channel(BOT_KOMUT_CHANNEL_ID)
        for uid in unique_members:
            view = GangInviteView(request_id, uid)
            await bot_komut.send(content=f"🔔 Merhaba <@{uid}>! **{self.cete_adi.value}** çetesi lideri <@{interaction.user.id}> sizi çetesine davet ediyor. Katılmayı kabul ediyor musunuz?", view=view)

        await interaction.response.send_message("✅ Başvurunuz alındı! Seçtiğiniz üyelere davetiyeler gönderildi. 3 kişinin onaylaması bekleniyor.", ephemeral=True)

class GangPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Çete Oluştur", style=discord.ButtonStyle.primary, custom_id="gang_create_btn")
    async def create_gang(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GangCreateModal())

# --- GANG MEMBER ADD VIEWS ---

class NewMemberInviteView(discord.ui.View):
    def __init__(self, cete_id: str, cete_adi: str, boss_id: str, invited_user_id: str):
        super().__init__(timeout=None)
        self.cete_id = cete_id
        self.cete_adi = cete_adi
        self.boss_id = boss_id
        self.invited_user_id = str(invited_user_id)

    async def handle_response(self, interaction: discord.Interaction, accepted: bool):
        if str(interaction.user.id) != self.invited_user_id:
            return await interaction.response.send_message("Bu davet sizin için değil!", ephemeral=True)

        for child in self.children:
            child.disabled = True
            
        komut_kanal = interaction.client.get_channel(BOT_KOMUT_CHANNEL_ID)
        
        if not accepted:
            await interaction.response.edit_message(content=f"{interaction.message.content}\n**Yanıtınız:** ❌ Reddedildi", view=self)
            await komut_kanal.send(f"❌ <@{self.boss_id}>, <@{self.invited_user_id}> çeteye davetinizi **reddetti**.")
            return

        # Kabul edildi
        cete_data = load_json(DATA_FILE)
        if self.cete_id not in cete_data:
            return await interaction.response.send_message("Çete artık mevcut değil.", ephemeral=True)

        if is_user_in_any_gang(self.invited_user_id):
            await interaction.response.edit_message(content=f"{interaction.message.content}\n**Yanıtınız:** ❌ İptal (Zaten bir çetedesiniz)", view=self)
            return await komut_kanal.send(f"❌ <@{self.boss_id}>, <@{self.invited_user_id}> zaten bir çetede olduğu için eklenemedi.")

        cete = cete_data[self.cete_id]
        cete["members"].append(self.invited_user_id)
        save_json(DATA_FILE, cete_data)

        # Rol ver
        role = interaction.guild.get_role(int(cete["role_id"]))
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.edit_message(content=f"{interaction.message.content}\n**Yanıtınız:** ✅ Kabul Edildi", view=self)
        await komut_kanal.send(f"🎉 <@{self.boss_id}>, <@{self.invited_user_id}> başarıyla **{self.cete_adi}** çetesine katıldı!")

        # Info mesajını güncelle
        try:
            text_channel = interaction.guild.get_channel(int(cete["text_channel"]))
            msg = await text_channel.fetch_message(int(cete["info_msg_id"]))
            embed = msg.embeds[0]
            
            # Üyeler field'ını bul ve güncelle
            for i, field in enumerate(embed.fields):
                if field.name == "Üyeler":
                    embed.set_field_at(i, name="Üyeler", value=" ".join([f"<@{u}>" for u in cete["members"]]), inline=False)
                    break
            await msg.edit(embed=embed)
        except:
            pass

    @discord.ui.button(label="Onaylıyorum", style=discord.ButtonStyle.green, custom_id="new_invite_accept")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, True)

    @discord.ui.button(label="Onaylamıyorum", style=discord.ButtonStyle.red, custom_id="new_invite_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, False)


class CeteSistemi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(DATA_FILE):
            save_json(DATA_FILE, {})
        if not os.path.exists(PENDING_FILE):
            save_json(PENDING_FILE, {})
        
        self.bot.add_view(GangPanelView())

    @app_commands.command(name="cete-panel-kur", description="Çete oluşturma panelini bu kanala kurar.")
    @app_commands.default_permissions(administrator=True)
    async def cete_panel_kur(self, interaction: discord.Interaction):
        await interaction.response.send_message("Panel kuruluyor...", ephemeral=True)
        channel = interaction.channel
        
        embed = discord.Embed(
            title="ER:LC Piyadeleri Çete Sistemi",
            description=(
                "**Gerekçeler:**\n"
                "💠 Çete oluşturmak için en az 3 kişi olmanız gerekmektedir.\n"
                "💠 Çete açıldıktan sonra çete yardımları her ay başı yapılacaktır.\n"
                f"💠 Sadece Çete lideri (<@&{BOSS_ROLE_ID}>), (<@&{UNDERBOSS_ROLE_ID}>) seçebilir.\n"
                "💠 Çetenize ait bir renk seçmeniz gerekmektedir. (Sağ üstteki görsele bakarak numara seçebilirsiniz.)\n"
                "💠 Çetenizin kurulacağı parsel kodunu yazmanız gerekmektedir.\n"
                "💠 Çetenizin oluşma hikayesini kurgulamak zorundasınız.\n\n"
                "Aşağıdaki **Çete Oluştur** butonuna basarak başvuru anketini doldurabilirsiniz."
            ),
            color=discord.Color.dark_theme()
        )
        
        try:
            file1 = discord.File("assets/cete_logo_kucuk.jpg", filename="kucuk.jpg")
            embed.set_thumbnail(url="attachment://kucuk.jpg")
            
            file2 = discord.File("assets/cete_banner.jpg", filename="banner.jpg")
            embed.set_image(url="attachment://banner.jpg")
            
            await channel.send(embed=embed, files=[file1, file2], view=GangPanelView())
        except Exception as e:
            await channel.send(embed=embed, view=GangPanelView())
            await interaction.followup.send(f"Görseller yüklenirken bir hata oluştu: {e}", ephemeral=True)

    @app_commands.command(name="underboss-ekle", description="Çetenize underboss eklersiniz (Sadece Boss kullanabilir).")
    @app_commands.describe(kisi="Underboss yapılacak kişi")
    async def underboss_ekle(self, interaction: discord.Interaction, kisi: discord.Member):
        cete_data = load_json(DATA_FILE)
        boss_uid = str(interaction.user.id)
        
        cete_id = None
        for cid, c in cete_data.items():
            if c["boss"] == boss_uid:
                cete_id = cid
                break
                
        if not cete_id:
            return await interaction.response.send_message("❌ Siz bir çete lideri (Boss) değilsiniz!", ephemeral=True)
            
        cete = cete_data[cete_id]
        if str(kisi.id) not in cete["members"]:
            return await interaction.response.send_message("❌ Seçtiğiniz kişi çetenizde bulunmuyor!", ephemeral=True)
            
        if len(cete.get("underbosses", [])) >= 2:
            return await interaction.response.send_message("❌ Çetenizde en fazla 2 adet Underboss bulunabilir!", ephemeral=True)
            
        if str(kisi.id) in cete.get("underbosses", []):
            return await interaction.response.send_message("❌ Bu kişi zaten Underboss!", ephemeral=True)
            
        # Role verme
        underboss_role = interaction.guild.get_role(UNDERBOSS_ROLE_ID)
        if underboss_role:
            await kisi.add_roles(underboss_role)
            
        cete_data[cete_id]["underbosses"].append(str(kisi.id))
        save_json(DATA_FILE, cete_data)
        
        await interaction.response.send_message(f"✅ Başarıyla {kisi.mention} kullanıcısı çetenizin Underboss'u yapıldı!")

    @app_commands.command(name="uye-ekle", description="Çetenize yeni üye davet edersiniz (Sadece Boss kullanabilir).")
    @app_commands.describe(kisi="Davet edilecek kişi")
    async def uye_ekle(self, interaction: discord.Interaction, kisi: discord.Member):
        cete_data = load_json(DATA_FILE)
        boss_uid = str(interaction.user.id)
        
        cete_id = None
        for cid, c in cete_data.items():
            if c["boss"] == boss_uid:
                cete_id = cid
                break
                
        if not cete_id:
            return await interaction.response.send_message("❌ Siz bir çete lideri (Boss) değilsiniz!", ephemeral=True)
            
        if is_user_in_any_gang(kisi.id):
            return await interaction.response.send_message("❌ Seçtiğiniz kişi zaten bir çetede bulunuyor!", ephemeral=True)
            
        cete = cete_data[cete_id]
        
        view = NewMemberInviteView(cete_id, cete["name"], boss_uid, str(kisi.id))
        bot_komut = interaction.client.get_channel(BOT_KOMUT_CHANNEL_ID)
        await bot_komut.send(content=f"🔔 Merhaba {kisi.mention}! **{cete['name']}** çetesi lideri {interaction.user.mention} sizi çetesine davet ediyor. Katılmayı kabul ediyor musunuz?", view=view)
        
        await interaction.response.send_message(f"✅ {kisi.mention} kişisine davetiye gönderildi! (Kanal: <#{BOT_KOMUT_CHANNEL_ID}>)", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CeteSistemi(bot))
