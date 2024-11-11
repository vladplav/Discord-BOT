from discord import DiscordException,NotFound,Forbidden,HTTPException
import json
from os.path import isfile
import aiofiles
from ButtonClasses import LikeButtons, WorkButtons, AdminButtons, CheckOnline, UserButtons
class Messages_manager:
    def __init__(self, bot):
        self.bot=bot
        self.db_manager=bot.db_manager
        self.load_views()
        self.cached_channels = {}

    def load_views(self):
        self.LikeButtonsView = LikeButtons(self.db_manager)
        self.WorkButtonsView = WorkButtons(self.db_manager)
        self.AdminButtonsView = AdminButtons(self.bot, self.db_manager)
        self.UserInfoView = UserButtons(self.db_manager)


    async def SendLikeMessage(self,ctx):
        return await ctx.send("Поставь лайки на мониторинги!", view=self.LikeButtonsView)

    async def SendWorkMessage(self,ctx):
        return await ctx.send("Пора админить!", view=self.WorkButtonsView)

    async def SendAdminMessage(self,ctx):
        return await ctx.send("Админ панель", view=self.AdminButtonsView)

    async def SendUserMessage(self,ctx):
        return await ctx.send("Ваш профиль", view=self.UserInfoView)

    async def FSendMessage(self,ctx,type):
        if type == 1:
            return await self.SendLikeMessage(ctx)
        elif type == 2:
            return await self.SendWorkMessage(ctx)
        elif type == 3:
            return await self.SendAdminMessage(ctx)
        elif type == 4:
            return await self.SendUserMessage(ctx)
        else:
            print("Неверный Type сообщения: ", type)

    async def EditLikeMessage(self,message):
        return await message.edit(content = "Поставь лайки на мониторинги!", view=self.LikeButtonsView)

    async def EditWorkMessage(self,message):
        return await message.edit(content = "Пора админить!", view=self.WorkButtonsView)

    async def EditAdminMessage(self,message):
        return await message.edit(content = "Админ панель", view=self.AdminButtonsView)

    async def EditUserMessage(self,message):
        return await message.edit(content = "Ваш профиль", view=self.UserInfoView)

    async def FEditMessage(self, message, type):
        if type == 1:
            return await self.EditLikeMessage(message)
        elif type == 2:
            return await self.EditWorkMessage(message)
        elif type == 3:
            return await self.EditAdminMessage(message)
        elif type == 4:
            return await self.EditUserMessage(message)
        else:
            print("Неверный Type сообщения: ", type)

    async def safe_send(self, recipient, content, view=None):
        try:
            if view:
                return await recipient.send(content, view=view)
            else:
                return await recipient.send(content)
        except NotFound:
            print(f'Пользователь/канал с ID {recipient.id} не найден')
        except Forbidden:
            print(f'Нет прав для отправки сообщения пользователю/каналу с ID {recipient.id}')
        except HTTPException as e:
            print(f'Ошибка HTTP при отправке сообщения: {e}')
        except DiscordException as e:
            print(f'Ошибка при отправке сообщения: {e}')

    async def SendLikeMessageToUser(self,user_id):
        user = await self.bot.fetch_user(int(user_id))
        await self.safe_send(user, 'Напоминание: пора поставить лайки на мониторинге!', view=self.LikeButtonsView)

    async def SendCheckOnlineMessageToUser(self,user_id):
        CheckOnlineView = CheckOnline(self.db_manager,user_id)
        user = await self.bot.fetch_user(int(user_id))
        message = await self.safe_send(user, 'Подтвердите, что вы онлайн!', view=CheckOnlineView)
        await CheckOnlineView.setup_message(message)
        try:
            self.bot.db_manager.create_admin_check_session(user_id)
        except Exception as e:
            print(f'Сессия проверки для {user_id} не была создана: {e}')


    async def load_messages_file(self):
        file_path = self.bot.messagesfile
        if not isfile(file_path):
            print(f"{file_path} not found. Creating with default configuration.")
            default_data = {
                "channel_messages": [
                    {
                        "channel_id": "YOUR_CHANNEL_ID_HERE",
                        "message_id": None,
                        "content": "This is a placeholder message that will be updated or created on bot startup."
                    }
                ]
            }
            await self.save_json(file_path, default_data)
            return json.load(default_data)
        async with aiofiles.open(file_path, 'r') as file:
            return json.loads(await file.read())


    async def save_json(self, file_path, data):
        async with aiofiles.open(file_path, 'w') as file:
            await file.write(json.dumps(data, indent=4))

    def get_cached_channel(self, channel_id):
        if channel_id not in self.cached_channels:
            self.cached_channels[channel_id] = self.bot.get_channel(channel_id)
        return self.cached_channels[channel_id]

    async def update_or_create_messages(self):
        data = await self.load_messages_file()
        channel_messages = data['channel_messages']

        for entry in channel_messages:

            channel_id = int(entry['channel_id'])
            message_id = entry['message_id']
            message_type = int(entry['content'])


            channel = self.get_cached_channel(channel_id)

            if channel is None:
                print(f"Канал с ID {channel_id} не найден.")
                continue

            if message_id:
                try:
                    # Попробуем обновить сообщение
                    message = await channel.fetch_message(message_id)
                    await self.FEditMessage(message,message_type)
                    print(f"Обновлено сообщение в канале {channel_id}.")
                except NotFound:
                    print(f"Сообщение с ID {message_id} не найдено. Создаем новое сообщение.")
                    message = await self.FSendMessage(channel,message_type)
                    entry['message_id'] = message.id
            else:
                message = await self.FSendMessage(channel,message_type)
                entry['message_id'] = message.id
        await self.save_json(self.bot.messagesfile, data)

