import discord
from discord.ext import commands

UYE_ROLU_ID = 1533908873772273715
ONAYLANMIS_BIREY_ROLU_ID = 1534741499726663690
ERKEK_ROLU_ID = 1534736940904218755
KIZ_ROLU_ID = 1534736941600342016

class CinsiyetSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Erkek", description="Erkek rolünü almak için seçin.", emoji="👦"),
            discord.SelectOption(label="Kız", description="Kız rolünü almak için seçin.", emoji="👧")
        ]
        super().__init__(placeholder="Cinsiyetin nedir?", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        
        uye_rol = guild.get_role(UYE_ROLU_ID)
        onay_rol = guild.get_role(ONAYLANMIS_BIREY_ROLU_ID)
        erkek_rol = guild.get_role(ERKEK_ROLU_ID)
        kiz_rol = guild.get_role(KIZ_ROLU_ID)

        roller_verilecek = [uye_rol, onay_rol]

        if self.values[0] == "Erkek":
            roller_verilecek.append(erkek_rol)
            cinsiyet_metin = "Erkek"
        else:
            roller_verilecek.append(kiz_rol)
            cinsiyet_metin = "Kız"

        # None olan rolleri filtrele (Rol bulunamazsa hata vermemesi için)
        roller_verilecek = [r for r in roller_verilecek if r is not None]
        
        await user.add_roles(*roller_verilecek)
        await interaction.response.send_message(f"Kayıt tamamlandı! Rolleriniz verildi. (Seçim: {cinsiyet_metin})", ephemeral=True)

class KayitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CinsiyetSelect())

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kayit_kur")
    @commands.has_permissions(administrator=True)
    async def kayit_kur(self, ctx):
        embed = discord.Embed(
            title="Sunucu Kayıt Anketi",
            description="Sunucuya tam erişim sağlamak ve onaylanmış birey olmak için aşağıdaki menüden cinsiyetinizi seçiniz.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=KayitView())

async def setup(bot):
    await bot.add_cog(Registration(bot))
