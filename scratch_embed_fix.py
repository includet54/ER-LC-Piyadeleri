import json
import os

with open('cogs/yardim_bekleme.py', 'r', encoding='utf-8') as f:
    content = f.read()

search_start = content.find('destek_id = get_next_destek_id()')
if search_start != -1:
    real_start = content.find('embed = discord.Embed(', search_start)
    end_idx = content.find('await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)', search_start)
    if real_start != -1 and end_idx != -1:
        end_idx += len('await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)')
        
        replacement = """embed = discord.Embed(
            description=(
                f"# ✉️ Destek Çağrı Bildirimi\\n"
                f"Kullanıcı destek bekleme ses kanalına yönlendirildi.\\n"
                f"{kisi.mention} | {kisi_rol_adi}\\n"
                f"_____________________________________________________________________________________________________________________________\\n"
                f"# 📌Çağrı Bilgisi\\n"
                f"## **Çağrı ID:** {destek_id}\\n"
                f"## **Kullanıcı:** {kisi.mention} | {kisi_rol_adi}\\n"
                f"## **Çağıran Yetkili:** {interaction.user.mention} | {yetkili_rol_adi}\\n"
                f"## **Süre:** {tahmini_sure}\\n"
                f"_____________________________________________________________________________________________________________________________\\n"
                f"# ✨Yönlendirme\\n"
                f"## **Sebep:** {sebep}\\n"
                f"## **Lütfen [Yardım bekleme](https://discord.com/channels/1529545898294509589/1532829788824404274) ses kanalına geçiniz. Yetkili hazır olduğunda destek odasına alınacaksınız.**"
            ),
            color=discord.Color.from_rgb(43, 45, 49)
        )
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        target_channel = interaction.client.get_channel(1552041858530672670)
        if target_channel:
            await target_channel.send(content=f"{kisi.mention}", embed=embed)
            await interaction.response.send_message("✅ Bildirim başarıyla gönderildi.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hedef kanal bulunamadı (1552041858530672670).", ephemeral=True)"""
            
        new_content = content[:real_start] + replacement + content[end_idx:]
        with open('cogs/yardim_bekleme.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Updated embed layout successfully!')
