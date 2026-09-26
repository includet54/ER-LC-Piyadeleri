import re

file_paths = [
    r'C:\Users\pcigd\OneDrive\Belgeler\GitHub\ER-LC-Piyadeleri\cogs\yonetim_paneli.py',
    r'c:\Users\pcigd\Downloads\ER-LC-Piyadeleri-main\ER-LC-Piyadeleri-main\cogs\yonetim_paneli.py'
]

for file_path in file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Add Role IDs at top
        if 'TICKET_YETKILISI_ID' not in content:
            content = content.replace(
                'TAKMA_AD_YETKILISI_ID = 1543075759508164659',
                'TAKMA_AD_YETKILISI_ID = 1543075759508164659\n\nTICKET_YETKILISI_ID = 1553333289798869032\nKAPISMA_TALEP_YETKILISI_ID = 1553427352044707840\nDESTEK_BEKLEME_YETKILISI_ID = 1553473785527537765'
            )

        # 2. Get role objects
        if 'ticket_yetk_rol =' not in content:
            content = content.replace(
                'takma_ad_rol = guild.get_role(TAKMA_AD_YETKILISI_ID)',
                'takma_ad_rol = guild.get_role(TAKMA_AD_YETKILISI_ID)\n        ticket_yetk_rol = guild.get_role(TICKET_YETKILISI_ID)\n        kapisma_yetk_rol = guild.get_role(KAPISMA_TALEP_YETKILISI_ID)\n        destek_bekleme_rol = guild.get_role(DESTEK_BEKLEME_YETKILISI_ID)'
            )

        # 3. Update Trial Staff logic
        trial_pattern = r'if trial_rol: await hedef_uye\.add_roles\(trial_rol\)\s+if wl_rol: await hedef_uye\.add_roles\(wl_rol\)\s+mesaj = f"✅  \{hedef_uye\.mention\} başarıyla \*\*Trial Staff\*\* ve \*\*Whitelist Yetkilisi\*\* yapıldı\."'
        trial_replacement = """if trial_rol: await hedef_uye.add_roles(trial_rol)
                if wl_rol: await hedef_uye.add_roles(wl_rol)
                if ticket_yetk_rol: await hedef_uye.add_roles(ticket_yetk_rol)
                if kapisma_yetk_rol: await hedef_uye.add_roles(kapisma_yetk_rol)
                mesaj = f"✅  {hedef_uye.mention} başarıyla **Trial Staff**, **Whitelist Yetkilisi**, **Ticket Yetkilisi** ve **Kapışma Talep Yetkilisi** yapıldı."""
        
        # fallback with unicode escape sequence or regex with dotall
        trial_pattern = r'if self\.islem_turu == "trial":\s+if trial_rol: await hedef_uye\.add_roles\(trial_rol\)\s+if wl_rol: await hedef_uye\.add_roles\(wl_rol\)\s+mesaj = .*?\"'
        
        trial_replacement = """if self.islem_turu == "trial":
                if trial_rol: await hedef_uye.add_roles(trial_rol)
                if wl_rol: await hedef_uye.add_roles(wl_rol)
                if ticket_yetk_rol: await hedef_uye.add_roles(ticket_yetk_rol)
                if kapisma_yetk_rol: await hedef_uye.add_roles(kapisma_yetk_rol)
                mesaj = f"✅  {hedef_uye.mention} başarıyla **Trial Staff**, **Whitelist Yetkilisi**, **Ticket Yetkilisi** ve **Kapışma Talep Yetkilisi** yapıldı.\""""
        
        content = re.sub(trial_pattern, trial_replacement, content, flags=re.DOTALL)


        # 4. Update Staff logic
        staff_pattern = r'if staff_rol: await hedef_uye\.add_roles\(staff_rol\)\s+if trial_rol: await hedef_uye\.remove_roles\(trial_rol\)\s+mesaj = f".*?Staff\*\* yapıldı \(Trial Staff alındı\)\."'
        staff_replacement = """if staff_rol: await hedef_uye.add_roles(staff_rol)
                if trial_rol: await hedef_uye.remove_roles(trial_rol)
                if destek_bekleme_rol: await hedef_uye.add_roles(destek_bekleme_rol)
                mesaj = f"✅  {hedef_uye.mention} başarıyla **Staff** ve **Destek Bekleme Yetkilisi** yapıldı (Trial Staff alındı).\""""
        
        content = re.sub(staff_pattern, staff_replacement, content, flags=re.DOTALL)


        # 5. Update panel description
        desc_pattern = r'"🔸 \*\*Trial Staff:\*\* Seçilen kişiye Trial Staff ve Registration Manager \(Whitelist Yetkilisi\) verir\.\\n"\s+"🔸 \*\*Staff:\*\* Seçilen kişinin Staff olmasını sağlar\. \*\([^)]*\)\*\.\\n"'
        desc_replacement = r'"🔸 \*\*Trial Staff:\*\* Seçilen kişiye Trial Staff, Registration Manager (Whitelist Yetkilisi), Ticket Yetkilisi ve Kapışma Talep Yetkilisi verir.\\n"\n            "🔸 \*\*Staff:\*\* Seçilen kişinin Staff ve Destek Bekleme Yetkilisi olmasını sağlar. *(Trial Staff zorunludur)*.\\n"'
        
        content = re.sub(desc_pattern, desc_replacement, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")

    except Exception as e:
        print(e)
