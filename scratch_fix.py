with open('cogs/yonetim_paneli.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix double messages in trial
import re
pattern = r'mesaj = f"✅\s*\{hedef_uye\.mention\} başarıyla \*\*Trial Staff\*\*, \*\*Whitelist Yetkilisi\*\*, \*\*Ticket Yetkilisi\*\* ve \*\*Kapışma Talep Yetkilisi\*\* yapıldı\.".*?yapıldı\."'
content = re.sub(pattern, 'mesaj = f"✅  {hedef_uye.mention} başarıyla **Trial Staff**, **Whitelist Yetkilisi**, **Ticket Yetkilisi** ve **Kapışma Talep Yetkilisi** yapıldı."', content)

# Check Staff
pattern2 = r'mesaj = f"✅\s*\{hedef_uye\.mention\} başarıyla \*\*Staff\*\* ve \*\*Destek Bekleme Yetkilisi\*\* yapıldı \(Trial Staff alındı\)\.".*?\."'
content = re.sub(pattern2, 'mesaj = f"✅  {hedef_uye.mention} başarıyla **Staff** ve **Destek Bekleme Yetkilisi** yapıldı (Trial Staff alındı)."', content)

# Also fix the weird markdown stars escaping
content = content.replace(r'\*\*Trial Staff:\*\*', '**Trial Staff:**')
content = content.replace(r'\*\*Staff:\*\*', '**Staff:**')

with open('cogs/yonetim_paneli.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed!")
