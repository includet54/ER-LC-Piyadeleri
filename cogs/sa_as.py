import discord
from discord.ext import commands
import random

# Toplam 20 tetikleyici (Senin listen + sık kullanılan alternatifler)
TETIKLEYICILER = [
    "sa", "sea", "selamın aleykum", "selamunaleykum", "selam",
    "selamınaleykum", "selamun aleykum", "esselamualeykum",
    "esselamualeyküm", "esselamu aleyküm", "esselamu aleykum",
    "slm", "s.a", "s.a.", "selamlar", "selamın aleyküm",
    "selamun aleyküm", "hayırlı günler", "selam millet", "merhabalar"
]

# Emojilerle zenginleştirilmiş rastgele yanıtlar
YANITLAR = [
    "Aleyküm selam, selamın aynısı sana da kardeş! ✌️😎",
    "Ve aleyküm selam, selamın en güzeli senden geldi. ✨",
    "Aleyküm selam, selamına kurban! 🤎",
    "Ve aleyküm selam, buyur başım gözüm üstüne. 👑",
    "Aleyküm selam, selamınla şereflendik. 🌹",
    "Ve aleyküm selam, selametle kal. 🕊️",
    "Aleyküm selam, selamın ağırlığı kadar bereket üzerine olsun. 🤲💎",
    "Ve aleyküm selam, aldım başımın üstüne yeri var. 🫡",
    "Aleyküm selam, selam hadi; aleyküm de hadi! 😅👋",
    "Ve aleyküm selam, aynen iade ediyorum. 🔄😉",
    "Aleyküm selam, selamına selam kattık. ➕🔥",
    "Ve aleyküm selam, selamın bana ulaştı, karşılığı fazlasıyla sana. 💯",
    "Aleyküm selam, selamın tadı damağımda kaldı. 🍬😋",
    "Ve aleyküm selam, selamının kıymetini bilirim. 🌟",
    "Aleyküm selam, selam olsun sana da güzel insan. 💐"
]

class SaAs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Botun kendi mesajlarına yanıt vermesini engelle
        if message.author.bot:
            return

        # Mesajı küçük harfe çevir ve başındaki/sonundaki boşlukları sil
        icerik = message.content.strip().lower()

        # Eğer yazılan mesaj tam olarak tetikleyicilerden biriyse yanıtla
        if icerik in TETIKLEYICILER:
            secilen_yanit = random.choice(YANITLAR)
            await message.reply(secilen_yanit, mention_author=False)

async def setup(bot):
    await bot.add_cog(SaAs(bot))
