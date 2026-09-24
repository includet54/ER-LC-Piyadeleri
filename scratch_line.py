with open('cogs/yardim_bekleme.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('f"---\\n\\n"', 'f"***\\n\\n"')

with open('cogs/yardim_bekleme.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced --- with ***')
