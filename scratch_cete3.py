import os
import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\cete_sistemi.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\cete_sistemi.py'
]

replacement = '''    async def on_submit(self, interaction: discord.Interaction):
        try:
            if is_user_in_any_gang(interaction.user.id):
                return await interaction.response.send_message("❌ Zaten bir çetedesiniz veya başka bir çetenin boss'usunuz!", ephemeral=True)
            
            if self.parsel_kodu.value.strip() not in VALID_PARSELLER:
                            return await interaction.response.send_message("❌ Geçersiz parsel kodu! Geçerli kodlar: 700, 701, 702, 703, 1104, 1108, 1101, 601, 602, 600, 805, 807, 809, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 403, 404, 405, 406, 407, 409, 410, 411", ephemeral=True)
            
            colors_data = load_json(COLORS_FILE)
            valid_color = False
            user_input_color = self.cete_rengi.value.strip()
            try:
                normalized_color_id = str(int(user_input_color))
            except ValueError:
                normalized_color_id = user_input_color
                
            for c in colors_data:
                if str(c.get("ID", "")) == normalized_color_id:
                    valid_color = True
                    user_input_color = normalized_color_id 
                    break
                    
            if not valid_color:
                return await interaction.response.send_message("❌ Geçersiz Renk ID girdiniz. Lütfen görseldeki numaralardan birini yazın.", ephemeral=True)

            view = GangMemberSelectView(
                cete_adi=self.cete_adi.value.strip(),
                cete_rengi=user_input_color,
                parsel_kodu=self.parsel_kodu.value.strip(),
                hikaye=self.hikaye.value.strip()
            )
            
            await interaction.response.send_message("Lütfen çetenizin başlangıç üyelerini (En az 3 kişi) aşağıdaki menüden seçiniz:", view=view, ephemeral=True)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print("GANG CREATE MODAL ERROR:", tb)
            try:
                await interaction.response.send_message(f"Sistem Hatası: {str(e)}", ephemeral=True)
            except:
                pass
'''

for file_path in file_paths:
    if not os.path.exists(file_path): continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to replace the on_submit method
    # Let's find the start of on_submit and the end (before class GangPanelView)
    pattern = re.compile(r'    async def on_submit\(self, interaction: discord\.Interaction\):.*?(?=    class GangPanelView|\Z)', re.DOTALL)
    
    # Check if we can find it
    if pattern.search(content):
        # We need to be careful with the indentation of GangPanelView which is a top level class
        # Wait, GangPanelView is top level, so it starts without indent.
        pattern = re.compile(r'    async def on_submit\(self, interaction: discord\.Interaction\):.*?(?=class GangPanelView)', re.DOTALL)
        content = pattern.sub(replacement + '\n', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added try-except to {file_path}")
    else:
        print(f"Could not find on_submit block in {file_path}")
