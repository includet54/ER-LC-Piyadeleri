import re
import os

with open('cogs/yardim_bekleme.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First we need to find the start of our embed declaration
search_start = content.find('embed = discord.Embed(')
if search_start != -1:
    end_idx = content.find('await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)', search_start)
    if end_idx != -1:
        end_idx += len('await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)')
        
        replacement = """embed = discord.Embed(
            description=(
                f"## ✉️ Destek Çağrı Bildirimi\\n"
                f"Kullanıcı destek bekleme ses kanalına yönlendirildi.\\n"
                f"{kisi.mention} | {kisi_rol_adi}\\n"
                f"---\\n"
                f"## 📌Çağrı Bilgisi\\n"
                f"**Çağrı ID:** {destek_id}\\n"
                f"**Kullanıcı:** {kisi.mention} | {kisi_rol_adi}\\n"
                f"**Çağıran Yetkili:** {interaction.user.mention} | {yetkili_rol_adi}\\n"
                f"**Süre:** {tahmini_sure}\\n"
                f"---\\n"
                f"### ✨Yönlendirme\\n"
                f"**Sebep:** {sebep}\\n"
                f"Lütfen [Yardım bekleme](https://discord.com/channels/1529545898294509589/1532829788824404274) ses kanalına geçiniz. Yetkili hazır olduğunda destek odasına alınacaksınız."
            ),
            color=discord.Color.from_rgb(43, 45, 49)
        )
        
        LOGO_URL = "BURAYA_LOGO_LINKINI_YAPISTIR"
        if LOGO_URL.startswith("http"):
            embed.set_thumbnail(url=LOGO_URL)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        target_channel = interaction.client.get_channel(1552041858530672670)
        if target_channel:
            await target_channel.send(content=f"{kisi.mention}", embed=embed)
            await interaction.response.send_message("✅ Bildirim başarıyla gönderildi.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)"""
        
        new_content = content[:search_start] + replacement + content[end_idx:]
        with open('cogs/yardim_bekleme.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Embed updated with correct markdown!')
