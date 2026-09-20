import discord
from discord.ext import commands
from discord import app_commands
import os

KURUCU_ROL_ID = 1529546007635824680
ILLEGAL_ROL_ID = 1539249508314259567
LEGAL_ROL_ID = 1539318613498929193

CIVILIAN_VEHICLES = [
    "Falcon Prime Eques 2003",
    "Chevlon Camion GMT 800 LTS 2002",
    "Chevlon Camion GMT 800 LT 2002",
    "Chevlon Camion GMT 800 S 2002",
    "Falcon Advance 350 Royal Ranch 2020",
    "Falcon Advance 350 2020",
    "Bullhorn Pueblo V6 2022",
    "Falcon Scavenger 2013",
    "Falcon Scavenger Royal Ranch 2024",
    "Celestial Type-6 2024",
    "Bullhorn Prancer S 2011",
    "Falcon Rampage Prairie 2021",
    "Bullhorn Prancer C-T 2020"
]

OFFICIAL_VEHICLES = [
    "Falcon Traveller PPV 2022",
    "Falcon Advance XET 2022",
    "Falcon Global 350 2013",
    "Chevlon Camion PPV 2021",
    "Chevlon Amigo LZR 2011",
    "Falcon Interceptor Sedan 2017"
]

def check_civilian_permissions(member: discord.Member) -> bool:
    if member.guild_permissions.administrator: return True
    return any(r.id in [KURUCU_ROL_ID, ILLEGAL_ROL_ID, LEGAL_ROL_ID] for r in member.roles)

def check_official_permissions(member: discord.Member) -> bool:
    if member.guild_permissions.administrator: return True
    return any(r.id in [KURUCU_ROL_ID, LEGAL_ROL_ID] for r in member.roles)

def find_asset_image(base_name: str, is_official: bool = False):
    variations = []
    
    # Format variations
    name_underscored = base_name.replace(" ", "_")
    prefix_under = "(LEO)_" if is_official else ""
    prefix_space = "(LEO) " if is_official else ""
    
    # 1. Exact match
    variations.append(f"{base_name}")
    # 2. Exact match + _Original
    variations.append(f"{base_name}_Original")
    # 3. Underscored
    variations.append(f"{name_underscored}")
    # 4. Underscored + _Original (Matches most civilian vehicles)
    variations.append(f"{name_underscored}_Original")
    
    if is_official:
        variations.append(f"{prefix_space}{base_name}")
        variations.append(f"{prefix_space}{base_name}_Original")
        variations.append(f"{prefix_under}{name_underscored}")
        variations.append(f"{prefix_under}{name_underscored}_Original") # Matches most official vehicles

    for var in variations:
        for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
            path = os.path.join("assets", f"{var}{ext}")
            if os.path.exists(path):
                return path
    return None

class MapView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def send_map(self, interaction: discord.Interaction, map_name: str, fallback_file: str = None):
        img_path = find_asset_image(map_name)
        if not img_path and fallback_file:
            img_path = find_asset_image(fallback_file)
            
        embed = discord.Embed(title=f"🗺️ {map_name}", color=discord.Color.blue())
        if img_path:
            dosya = discord.File(img_path, filename="map.png")
            embed.set_image(url="attachment://map.png")
            await interaction.response.send_message(embed=embed, file=dosya, ephemeral=True)
        else:
            embed.description = "*(Resim bulunamadı)*"
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Harita 2025", style=discord.ButtonStyle.primary, custom_id="map_2025")
    async def btn_2025(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_map(interaction, "Harita 2025", fallback_file="In-Game Map December 23 2025")

    @discord.ui.button(label="Harita 2026", style=discord.ButtonStyle.primary, custom_id="map_2026")
    async def btn_2026(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_map(interaction, "Harita 2026", fallback_file="Street Map v3 March 22 2026")

class AssetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="civilian-vehicles", description="Sivil araçların listesini ve detaylarını gösterir.")
    @app_commands.describe(arac="Görmek istediğiniz araç")
    async def civilian_vehicles(self, interaction: discord.Interaction, arac: str):
        if not check_civilian_permissions(interaction.user):
            return await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok. (Legal/İllegal rolleri gerektirir)", ephemeral=True)
            
        if arac not in CIVILIAN_VEHICLES:
            return await interaction.response.send_message("❌ Belirtilen sivil araç bulunamadı. Lütfen listeden geçerli bir araç seçin.", ephemeral=True)

        img_path = find_asset_image(arac, is_official=False)
        embed = discord.Embed(title=f"🚗 {arac}", description="Bu sivil araçla ilgili özellikler:\n*(Buraya araç özellikleri eklenebilir)*", color=discord.Color.green())
        
        if img_path:
            dosya = discord.File(img_path, filename="vehicle.png")
            embed.set_thumbnail(url="attachment://vehicle.png")
            await interaction.response.send_message(embed=embed, file=dosya)
        else:
            embed.description += "\n\n*(Resim bulunamadı)*"
            await interaction.response.send_message(embed=embed)

    @civilian_vehicles.autocomplete("arac")
    async def civilian_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=car, value=car)
            for car in CIVILIAN_VEHICLES if current.lower() in car.lower()
        ][:25]

    @app_commands.command(name="official-vehicles", description="Resmi (Polis/LEO) araçların listesini ve detaylarını gösterir.")
    @app_commands.describe(arac="Görmek istediğiniz araç")
    async def official_vehicles(self, interaction: discord.Interaction, arac: str):
        if not check_official_permissions(interaction.user):
            return await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok. (Sadece Legal rolü gerektirir)", ephemeral=True)
            
        if arac not in OFFICIAL_VEHICLES:
            return await interaction.response.send_message("❌ Belirtilen resmi araç bulunamadı. Lütfen listeden geçerli bir araç seçin.", ephemeral=True)

        img_path = find_asset_image(arac, is_official=True)
        embed = discord.Embed(title=f"🚓 {arac}", description="Bu resmi araçla ilgili özellikler:\n*(Buraya polis aracı özellikleri eklenebilir)*", color=discord.Color.blue())
        
        if img_path:
            dosya = discord.File(img_path, filename="vehicle.png")
            embed.set_thumbnail(url="attachment://vehicle.png")
            await interaction.response.send_message(embed=embed, file=dosya)
        else:
            embed.description += "\n\n*(Resim bulunamadı)*"
            await interaction.response.send_message(embed=embed)

    @official_vehicles.autocomplete("arac")
    async def official_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=car, value=car)
            for car in OFFICIAL_VEHICLES if current.lower() in car.lower()
        ][:25]

    @app_commands.command(name="maps", description="Sunucu haritalarını gösterir.")
    async def maps(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🗺️ Harita Seçimi", description="Lütfen görmek istediğiniz haritayı seçin:", color=discord.Color.dark_theme())
        await interaction.response.send_message(embed=embed, view=MapView())

async def setup(bot):
    await bot.add_cog(AssetsCog(bot))
