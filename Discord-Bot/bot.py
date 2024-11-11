import discord
import asyncio
from discord.ext import commands
import Config
from database_manager import DatabaseManager
import Messages
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Функция для загрузки всех Cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded extension {filename}')
            except Exception as e:
                print(f'Failed to load extension {filename}.', e)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    await load_cogs()
    try:
        await bot.messages.update_or_create_messages()
        print("Сообщения созданы или обновлены")
    except Exception as e:
        print(f"Ошибка при создании сообщений: {e}")


async def main():
    bot.db_manager = DatabaseManager()
    bot.allowed_user = Config.ALLOWED_USER_ID
    bot.alladminsfile = Config.ROLE_MEMBERS_FILE
    bot.messagesfile = Config.MESSAGES_FILE
    bot.messages = Messages.Messages_manager(bot)

    with open(Config.TOKEN_FILE, 'r') as file:
        token =  file.read().strip()

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("Bot stopped manually.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted.")
