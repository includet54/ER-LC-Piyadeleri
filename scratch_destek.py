import json
import os
import discord

def get_next_destek_id():
    id_file = "data/destek_id.json"
    if not os.path.exists("data"):
        os.makedirs("data")
        
    if not os.path.exists(id_file):
        last_id = 0
    else:
        try:
            with open(id_file, "r") as f:
                data = json.load(f)
                last_id = data.get("last_id", 0)
        except:
            last_id = 0
            
    new_id = last_id + 1
    with open(id_file, "w") as f:
        json.dump({"last_id": new_id}, f)
        
    return f"PRP-{new_id:05d}"

def generate_destek_bildir_code():
    code = """
    @app_commands.command(name="destek-bildir", description="Belirtilen kullanıcıyı destek bekleme odasına yönlendirir.")
    @app_commands.describe(
        kisi="Çağrılacak kişi",
        sebep="Çağrı sebebi",
        tahmini_sure="Tahmini destek süresi"
    )
    async def destek_bildir(self, interaction: discord.Interaction, kisi: discord.Member, sebep: str, tahmini_sure: str):
        admin_roles = {
            1529546007635824680: "Kurucu",
            1539167256246747186: "Üst Yönetim",
            1534798061845483694: "Yönetici",
            1537934087166369812: "Yönetim Ekibi",
            1551241753137254611: "Senior Staff",
            1551241634094645288: "Staff",
            1551241468985737376: "Trial Staff"
        }
        
        yetkili_rol_adi = "Yetkili"
        for role_id, role_name in admin_roles.items():
            if discord.utils.get(interaction.user.roles, id=role_id):
                yetkili_rol_adi = role_name
                break
                
        user_roles = {
            1539249508314259567: "İllegal",
            1539318613498929193: "Legal"
        }
        
        kisi_rol_adi = "Sivil"
        for role_id, role_name in user_roles.items():
            if discord.utils.get(kisi.roles, id=role_id):
                kisi_rol_adi = role_name
                break
                
        def get_next_destek_id():
            id_file = "data/destek_id.json"
            if not os.path.exists("data"):
                os.makedirs("data")
            if not os.path.exists(id_file):
                last_id = 0
            else:
                try:
                    with open(id_file, "r") as f:
                        data = json.load(f)
                        last_id = data.get("last_id", 0)
                except:
                    last_id = 0
            new_id = last_id + 1
            with open(id_file, "w") as f:
                json.dump({"last_id": new_id}, f)
            return f"PRP-{new_id:05d}"
            
        destek_id = get_next_destek_id()
        
        embed = discord.Embed(
            title="Kullanıcı destek bekleme ses kanalına yönlendirildi.",
            description=f"{kisi.mention} | {kisi_rol_adi}",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        embed.set_author(name="✉️ Destek Çağrı Bildirimi")
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        cagri_bilgisi = (
            f"**Çağrı ID:** {destek_id}\\n"
            f"**Kullanıcı:** {kisi.mention} | {kisi_rol_adi}\\n"
            f"**Çağıran Yetkili:** {interaction.user.mention} | {yetkili_rol_adi}\\n"
            f"**Süre:** {tahmini_sure}"
        )
        embed.add_field(name="📌 Çağrı Bilgisi", value=cagri_bilgisi, inline=False)
        
        yonlendirme = (
            f"**Sebep:** {sebep}\\n\\n"
            f"Lütfen [Yardım bekleme](https://discord.com/channels/1529545898294509589/1532829788824404274) ses kanalına geçiniz. Yetkili hazır olduğunda destek odasına alınacaksınız."
        )
        embed.add_field(name="✨ Yönlendirme", value=yonlendirme, inline=False)
        
        target_channel = interaction.client.get_channel(1552041858530672670)
        if target_channel:
            await target_channel.send(content=f"{kisi.mention}", embed=embed)
            await interaction.response.send_message("✅ Bildirim başarıyla gönderildi.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)
"""
    return code

if __name__ == "__main__":
    with open('cogs/yardim_bekleme.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    code_to_insert = generate_destek_bildir_code()
    
    # insert inside YardimBekleme class, for example right before def cog_unload
    idx = content.find("def cog_unload(self):")
    if idx != -1:
        new_content = content[:idx] + code_to_insert + "\n    " + content[idx:]
        with open('cogs/yardim_bekleme.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully injected destek_bildir into yardim_bekleme.py")
    else:
        print("Failed to find cog_unload")
