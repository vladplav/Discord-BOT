import discord
from discord.ext import commands
from re import compile

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = bot.db_manager  # Сохраняем db_manager в классе для дальнейшего использования
        self.URL_REGEX = compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send(
                "Извините, я не могу обрабатывать команды в личных сообщениях. Пожалуйста, используйте команды на сервере.")
            return

        # Находим все ссылки в сообщении
        urls = self.URL_REGEX.findall(message.content)

        role = discord.utils.get(message.author.guild.roles, name="ADMIN")
        if role in message.author.roles:
            for url in urls:
                if not self.db_manager.is_whitelisted(url):
                    self.db_manager.add_to_whitelist(url)
        else:
            for url in urls:
                if not self.db_manager.is_whitelisted(url):
                    try:
                        await message.delete()
                        print(f"Удалено сообщение с недопустимой ссылкой: {url}, от пользователя {message.author}")
                        return
                    except discord.Forbidden:
                        print(f"Не могу удалить сообщение в канале {message.channel.id}")
                    except discord.HTTPException as e:
                        print(f"Ошибка при удалении сообщения: {e}")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))  # Передаем db_manager в CommandsCog
