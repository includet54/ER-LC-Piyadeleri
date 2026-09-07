import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, UserSelect

# ==================== AYARLAR ====================
VS_TALEP_KANAL_ID = 1537136926287593503          # [vs talep] kanalı
VS_SONUC_KANAL_ID = 1537142672953708685          # [vs sonuç] kanalı

KURUCU_ROLE = 1529546007635824680
UST_YONETIM_ROLE = 1539167256246747186
YONETICI_ROLE = 1534798061845483694

PVP_MANAGER_ROLE = 1539169640326893589
DRIVE_MANAGER_ROLE = 1539169263124746350

YONETIM_ROLLER = [KURUCU_ROLE, UST_YONETIM_ROLE, YONETICI_ROLE]

# Kademe rolleri, en düşükten en yükseğe sıralı.
# Kazanan üye bu listede en yüksek sahip olduğu kademeden bir üst kademeye terfi eder.
TEMEL_KADEME = 1541213765410754640
KADEME_1 = 1541214087155810384
KADEME_2 = 1541215423301681252
KADEME_3 = 1541215599026372688
KADEME_4 = 1541216066532016310
KADEME_5 = 1541216359541645312
KADEME_6 = 1541216610751221851
KADEME_7 = 1541216852905041980

TIER_ORDER = [TEMEL_KADEME, KADEME_1, KADEME_2, KADEME_3, KADEME_4, KADEME_5, KADEME_6, KADEME_7]
# =================================================


def build_channel_topic(requester_id: int, victim_id: int, vs_type: str) -> str:
    """Kanal 'topic' alanına talep bilgisini gömer, bot yeniden başlasa bile tuşlar doğru çalışsın diye."""
    return f"vs|{requester_id}|{victim_id}|{vs_type}"


def parse_channel_topic(channel: discord.TextChannel):
    topic = channel.topic or ""
    try:
        prefix, rid, vid, vtype = topic.split("|")
        if prefix != "vs":
            return None, None, None
        return int(rid), int(vid), vtype
    except Exception:
        return None, None, None


async def promote_winner(guild: discord.Guild, winner: discord.Member):
    """Kazanan üyeyi bir üst kademeye terfi ettirir. Hiçbir kademe rolü yoksa hiçbir şey yapmaz."""
    if winner is None:
        return
    winner_role_ids = {r.id for r in winner.roles}
    # En yüksek kademeden başlayarak kontrol et, sadece bir terfi uygula.
    for i in range(len(TIER_ORDER) - 2, -1, -1):
        current_id = TIER_ORDER[i]
        next_id = TIER_ORDER[i + 1]
        if current_id in winner_role_ids:
            current_role = guild.get_role(current_id)
            next_role = guild.get_role(next_id)
            try:
                if current_role:
                    await winner.remove_roles(current_role, reason="VS kazandı - kademe terfisi")
                if next_role:
                    await winner.add_roles(next_role, reason="VS kazandı - kademe terfisi")
            except discord.Forbidden:
                pass
            return


async def swap_manager_role(guild: discord.Guild, winner: discord.Member, loser: discord.Member, vs_type: str):
    """
    Kaybeden üyede ilgili Manager rolü varsa, o rol kaybedenden alınıp kazanana verilir.
    Not: İstekte sadece PVP MANAGER için belirtilmişti, ama DRIVE için de aynı mantığın
    geçerli olması muhtemel görünüyor, o yüzden ikisi için de simetrik uyguladım.
    Sadece PVP için çalışmasını istersen 'manager_role_id' satırını PVP_MANAGER_ROLE
    olarak sabitlemen yeterli.
    """
    if winner is None or loser is None:
        return
    manager_role_id = PVP_MANAGER_ROLE if vs_type == "PVP" else DRIVE_MANAGER_ROLE
    if any(r.id == manager_role_id for r in loser.roles):
        role = guild.get_role(manager_role_id)
        if role:
            try:
                await loser.remove_roles(role, reason="VS kaybetti - manager rolü alındı")
                await winner.add_roles(role, reason="VS kazandı - manager rolü devralındı")
            except discord.Forbidden:
                pass


class VSTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="PVP", value="PVP", description="PVP kapışması", emoji="⚔️"),
            discord.SelectOption(label="DRIVE", value="DRIVE", description="Drive kapışması", emoji="🚗"),
        ]
        super().__init__(
            placeholder="Hangi türde kapışmak istiyorsun?",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="vs_type_select"
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_type = self.values[0]
        await interaction.response.defer()


class VSUserSelect(UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="Kiminle kapışmak istiyorsun? (Mağdur)",
            min_values=1,
            max_values=1,
            custom_id="vs_user_select"
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_user = self.values[0]
        await interaction.response.defer()


class VSRequestView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_user = None
        self.selected_type = None
        self.add_item(VSUserSelect())
        self.add_item(VSTypeSelect())

    @discord.ui.button(label="Talebi Gönder", style=discord.ButtonStyle.danger, emoji="⚔️", custom_id="vs_submit")
    async def submit(self, interaction: discord.Interaction, button: Button):
        if self.selected_user is None or self.selected_type is None:
            await interaction.response.send_message(
                "❌ Lütfen **hem kişiyi** hem de **türü** seçmelisin!",
                ephemeral=True
            )
            return

        if self.selected_user.id == interaction.user.id:
            await interaction.response.send_message("❌ Kendinle kapışamazsın!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        requester = interaction.user
        victim = self.selected_user
        vs_type = self.selected_type

        # Kanal ismi
        channel_name = f"vs-{requester.display_name[:10]}-vs-{victim.display_name[:10]}".lower().replace(" ", "-")

        # Overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            requester: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            victim: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        # Yönetim rolleri
        for role_id in YONETIM_ROLLER:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # Manager rolü
        manager_role_id = PVP_MANAGER_ROLE if vs_type == "PVP" else DRIVE_MANAGER_ROLE
        manager_role = guild.get_role(manager_role_id)
        if manager_role:
            overwrites[manager_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # Kanal oluştur — talep bilgisi 'topic' içine gömülür (bot restart olsa bile tuşlar çalışsın diye)
        category = interaction.channel.category
        new_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            topic=build_channel_topic(requester.id, victim.id, vs_type),
            reason=f"VS Talebi: {requester} vs {victim} ({vs_type})"
        )

        # Sabit mesaj + butonlar
        embed = discord.Embed(
            title="⚔️ VS Talebi Açıldı",
            description=(
                f"**Açan:** {requester.mention}\n"
                f"**Mağdur:** {victim.mention}\n"
                f"**Tür:** `{vs_type}`\n\n"
                f"Yönetim ekibi aşağıdan sonucu belirlesin."
            ),
            color=0xE74C3C
        )

        view = VSChannelView(
            requester_label=f"{requester.display_name} Kazandı",
            victim_label=f"{victim.display_name} Kazandı",
        )
        msg = await new_channel.send(
            content=f"{requester.mention} {victim.mention} "
                    f"{' '.join([f'<@&{r}>' for r in YONETIM_ROLLER])} "
                    f"<@&{manager_role_id}>",
            embed=embed,
            view=view
        )
        await msg.pin()

        await interaction.followup.send(
            f"✅ VS talebin oluşturuldu → {new_channel.mention}",
            ephemeral=True
        )


class VSChannelView(View):
    """
    Bu View artık talep bilgisini kendi içinde tutmuyor (requester_id/victim_id gibi) —
    her tuşa basıldığında bilgiyi kanalın 'topic' alanından okuyor. Bu sayede:
      1) main.py içinde tek, argümansız bir 'VSChannelView()' ile kalıcı (persistent)
         olarak eklenebiliyor (önceki hata buradan kaynaklanıyordu).
      2) Bot yeniden başlasa bile tuşlar doğru kişilere doğru işlemi uyguluyor.
    """
    def __init__(self, requester_label: str = "Talebi Açan Kazandı", victim_label: str = "Mağdur Kazandı"):
        super().__init__(timeout=None)
        for child in self.children:
            if getattr(child, "custom_id", None) == "vs_requester_win":
                child.label = requester_label
            elif getattr(child, "custom_id", None) == "vs_victim_win":
                child.label = victim_label

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Sadece yönetim basabilir
        user_roles = [r.id for r in interaction.user.roles]
        if not any(r in user_roles for r in YONETIM_ROLLER):
            await interaction.response.send_message("❌ Bu butonlara sadece Yönetim ekibi basabilir!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Talebi Açan Kazandı", style=discord.ButtonStyle.success, custom_id="vs_requester_win")
    async def requester_win(self, interaction: discord.Interaction, button: Button):
        requester_id, victim_id, vs_type = parse_channel_topic(interaction.channel)
        if requester_id is None:
            await interaction.response.send_message("❌ Bu kanalın VS bilgisi okunamadı.", ephemeral=True)
            return
        await self._finish(interaction, winner_id=requester_id, loser_id=victim_id, vs_type=vs_type)

    @discord.ui.button(label="Mağdur Kazandı", style=discord.ButtonStyle.primary, custom_id="vs_victim_win")
    async def victim_win(self, interaction: discord.Interaction, button: Button):
        requester_id, victim_id, vs_type = parse_channel_topic(interaction.channel)
        if requester_id is None:
            await interaction.response.send_message("❌ Bu kanalın VS bilgisi okunamadı.", ephemeral=True)
            return
        await self._finish(interaction, winner_id=victim_id, loser_id=requester_id, vs_type=vs_type)

    @discord.ui.button(label="Talep İptal Edildi", style=discord.ButtonStyle.danger, custom_id="vs_cancel")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        channel = interaction.channel
        if channel:
            await channel.delete(reason="VS Talebi iptal edildi")

    async def _finish(self, interaction: discord.Interaction, winner_id: int, loser_id: int, vs_type: str):
        await interaction.response.defer()

        guild = interaction.guild
        winner = guild.get_member(winner_id)
        loser = guild.get_member(loser_id)

        sonuc_kanal = guild.get_channel(VS_SONUC_KANAL_ID)
        if sonuc_kanal:
            embed = discord.Embed(
                title="🏆 VS Sonucu",
                description=(
                    f"**Kazanan:** {winner.mention if winner else f'<@{winner_id}>'}\n"
                    f"**Kaybeden:** {loser.mention if loser else f'<@{loser_id}>'}\n"
                    f"**Tür:** `{vs_type}`"
                ),
                color=0x2ECC71
            )
            await sonuc_kanal.send(embed=embed)

        # Kademe terfisi (sadece kazanan tarafta kademe rolü varsa çalışır)
        await promote_winner(guild, winner)

        # Manager rolü devri (sadece kaybeden tarafta ilgili manager rolü varsa çalışır)
        await swap_manager_role(guild, winner, loser, vs_type)

        channel = interaction.channel
        if channel:
            await channel.delete(reason="VS sonucu belirlendi")


class VSSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="VS Talep Oluştur", style=discord.ButtonStyle.danger, emoji="⚔️", custom_id="vs_open_request")
    async def open_request(self, interaction: discord.Interaction, button: Button):
        view = VSRequestView()
        await interaction.response.send_message(
            "Aşağıdan **kimi** ve **hangi türde** kapışmak istediğini seç, sonra **Talebi Gönder** butonuna bas:",
            view=view,
            ephemeral=True
        )


async def setup_vs_talep(bot: commands.Bot):
    """Bot başladığında sabit mesajı atar (yoksa)."""
    channel = bot.get_channel(VS_TALEP_KANAL_ID)
    if not channel:
        return

    # Daha önce atılmış mı kontrol et
    async for msg in channel.history(limit=20):
        if msg.author == bot.user and msg.components:
            return  # Zaten var

    embed = discord.Embed(
        title="⚔️ VS TALEP",
        description=(
            "Aşağıdaki butona basarak yeni bir VS talebi açabilirsin.\n\n"
            "Kiminle ve hangi türde (PVP / DRIVE) kapışmak istediğini seçmen gerekiyor."
        ),
        color=0x9B59B6
    )

    view = VSSetupView()
    await channel.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    # Kalıcı görünümler artık main.py içinde tek seferden ekleniyor.
    # Bot hazır olunca sabit mesajı kontrol et
    @bot.listen()
    async def on_ready():
        await setup_vs_talep(bot)
