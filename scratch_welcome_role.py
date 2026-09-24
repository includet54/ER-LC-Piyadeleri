import re

with open('cogs/welcome.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"    async def on_member_join\(self, member\):\s+await self\.guncelle_katilimci_sayisi\(member\.guild\)"
new_code = """    async def on_member_join(self, member):
        await self.guncelle_katilimci_sayisi(member.guild)
        
        # Kayıtsız rolünü ver
        kayitsiz_rol = member.guild.get_role(1542271426386591894)
        if kayitsiz_rol:
            try:
                await member.add_roles(kayitsiz_rol, reason="Sunucuya katıldı")
            except Exception:
                pass"""

if "1542271426386591894" not in content:
    content = re.sub(pattern, new_code, content)
    with open('cogs/welcome.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected Kayıtsız role assignment into welcome.py")
else:
    print("Role already injected in welcome.py")
