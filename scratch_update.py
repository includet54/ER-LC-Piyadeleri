import re

with open('cogs/cete_sistemi.py', 'r', encoding='utf-8') as f:
    content = f.read()

search_str = 'await komut_kanal.send(f"🎉 <@{boss_id}>, **{req[\'name\']}** çeteniz başarıyla onaylandı ve kuruldu! Kanallarınıza göz atabilirsiniz.")'
insert_str = '\n        await update_admin_gang_panel(interaction.client)'

idx = content.find(search_str)
if idx != -1:
    idx += len(search_str)
    new_content = content[:idx] + insert_str + content[idx:]
    with open('cogs/cete_sistemi.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Updated approve_btn!')
else:
    print('Could not find search_str')
