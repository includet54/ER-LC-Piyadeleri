import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\cete_sistemi.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\cete_sistemi.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update GangInviteView handle_response
        old_gang = '''        # Butonlar devre dY brak
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"{interaction.message.content}\\n**Yantnz:** {'o  Kabul Edildi' if accepted else '?O Reddedildi'}", view=self)'''
        
        old_gang = old_gang.encode('utf-8').decode('utf-8') # Just to bypass weird encoding
        
        # It's better to use regex to replace it
        pattern_gang = r"        # Butonları devre dışı bırak\s+for child in self\.children:\s+child\.disabled = True\s+await interaction\.response\.edit_message\(.*?view=self\)"
        new_gang = """        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message(f"Yanıtınız kaydedildi: {'✅ Kabul Edildi' if accepted else '❌ Reddedildi'}", ephemeral=True)"""
        
        content = re.sub(pattern_gang, new_gang, content)
        
        
        # Update MemberInviteView handle_response
        pattern_member1 = r"        for child in self\.children:\s+child\.disabled = True\s+komut_kanal = interaction\.client\.get_channel\(CETE_BILDIRIM_CHANNEL_ID\)\s+if not accepted:\s+await interaction\.response\.edit_message\(.*?view=self\)"
        new_member1 = """        komut_kanal = interaction.client.get_channel(CETE_BILDIRIM_CHANNEL_ID)
        
        if not accepted:
            try:
                await interaction.message.delete()
            except:
                pass
            await interaction.response.send_message("Daveti reddettiniz.", ephemeral=True)"""
        content = re.sub(pattern_member1, new_member1, content)
        
        pattern_member2 = r"        if is_user_in_any_gang\(self\.invited_user_id\):\s+await interaction\.response\.edit_message\(.*?view=self\)"
        new_member2 = """        if is_user_in_any_gang(self.invited_user_id):
            try:
                await interaction.message.delete()
            except:
                pass
            await interaction.response.send_message("Zaten bir çetedesiniz, davet iptal edildi.", ephemeral=True)"""
        content = re.sub(pattern_member2, new_member2, content)
        
        pattern_member3 = r"        guild = interaction\.guild\s+role = guild\.get_role\(int\(self\.cete_id\)\)\s+member = guild\.get_member\(int\(self\.invited_user_id\)\)\s+if role and member:\s+await member\.add_roles\(role\)\s+await interaction\.response\.edit_message\(.*?view=self\)"
        new_member3 = """        guild = interaction.guild
        role = guild.get_role(int(self.cete_id))
        member = guild.get_member(int(self.invited_user_id))
        if role and member:
            await member.add_roles(role)
        
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message("✅ Çeteye başarıyla katıldınız!", ephemeral=True)"""
        content = re.sub(pattern_member3, new_member3, content)
        
        
        # Update AdminApprovalView success message to delete_after
        pattern_admin = r"await komut_kanal\.send\(f\"🎉 <@\{boss_id\}>, \*\*\{req\['name'\]\}\*\* çeteniz başarıyla onaylandı ve kuruldu! Kanallarınıza göz atabilirsiniz\.\"\)"
        new_admin = r"await komut_kanal.send(f\"🎉 <@{boss_id}>, **{req['name']}** çeteniz başarıyla onaylandı ve kuruldu! Kanallarınıza göz atabilirsiniz.\", delete_after=15)"
        content = re.sub(pattern_admin, new_admin, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated messages logic in {file_path}")
    except Exception as e:
        print(f"Error {file_path}: {e}")
