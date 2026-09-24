import re

with open('cogs/uyari_sistemi.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new dictionary
new_maddeler = """MADDELER = {
    "M1": {"puan": 1, "aciklama": "Sunucumuzda küfür/hakarete başvurmak."},
    "M2": {"puan": 1, "aciklama": "Reklam yapmak, hesap/oyun satışı gibi ticari faaliyetlerde bulunmak (Özel mesajda dahil)."},
    "M3": {"puan": 1, "aciklama": "Bir başkasının görüşüne karşı nefret söylemi, hakaret veya küfür etmek."},
    "M4": {"puan": 1, "aciklama": "Cinsiyet fark etmeksizin taciz içeren davranışlarda bulunmak."},
    "M5": {"puan": 1, "aciklama": "Kanalları amacı dışında kullanmak (Örn: #bot-komut'da sohbet etmek)."},
    "M6": {"puan": 1, "aciklama": "Cinsel içerikli herhangi bir paylaşım (görsel, yazı, link) yapmak."},
    "M7": {"puan": 1, "aciklama": "Yetkiliye, muhattap olmak istemediği halde sunucu içinde hakaret etmek veya kavga ortamı yaratmak."},
    "M8": {"puan": 1, "aciklama": "Zorbalık yapmak, başka bir üyeyi sunucudan soğutacak davranışlarda bulunmak."},
    "M9": {"puan": 1, "aciklama": "<@&1529546007635824680> ve <@&1539167256246747186>'in bilgisi dışında sunucu üyelerini kendi sunucunuza veya grubunuza davet etmek."},
    "M10": {"puan": 1, "aciklama": "+18, cinsel taciz, ırkçılık, cinsiyet/yaş ayrımcılığı içeren içerik paylaşmak."},
    "M11": {"puan": 1, "aciklama": "Irkçılık ve her türlü ayrımcılık yapmak."},
    "M12": {"puan": 99, "aciklama": "1 gün içinde en az 2 uyarı almak."},
    "M13": {"puan": 1, "aciklama": "Sunucuda bulunan kişilerin piskolojisini etkileyecek argo, küçümseme ve dalga geçme gibi faliyetler yapmak."},
    "M14": {"puan": 1, "aciklama": "Sunucumuzda düzenlenen etkinliklerde veya yapılacak olan kapışmalarda karşı taraf rahatsız olduğu halde kendini abartı şekilde övmek."},
    "D1": {"puan": 1, "aciklama": "Önemli kanallara (duyuru vb.) anlamsız, boş mesajlar atmak."},
    "D2": {"puan": 1, "aciklama": "Ses kanallarında ses panelini veya sohbet kanalını gereksiz yere çağırmak (spawnlamak)."},
    "D3": {"puan": 1, "aciklama": "Ses kanallarında sürekli yolculuk yaparak gereksiz bildirim yağmuruna sebep olmak."},
    "Y1": {"puan": 99, "aciklama": "Yetkisini kendi lehine kullanmak."},
    "Y2": {"puan": 1, "aciklama": "Sunucudaki katılımcıyı yanlış yönlendirmek."},
    "Y3": {"puan": 1, "aciklama": "Yanlış işlem yapmak.(Örn: Yanlış uyarı vermek)"},
    "Y4": {"puan": 1, "aciklama": "Sunucuda kendini üstün görmek."},
    "Y5": {"puan": 1, "aciklama": "Kendinen üst kademeli yetkililerin yönlendirmesini dinlememek/takmamak."}
}"""

# Use regex to replace the old MADDELER dictionary
pattern = re.compile(r'MADDELER\s*=\s*\{.*?"Y5"[^\}]+\}', re.DOTALL)
new_content = pattern.sub(new_maddeler, content)

with open('cogs/uyari_sistemi.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated MADDELER successfully")
