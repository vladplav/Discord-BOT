import json
import discord
from discord.ui import Button, View
from datetime import datetime, timedelta

class LikeButtons(View):
    def __init__(self, db_manager):
        super().__init__(timeout=None)
        self.db_manager = db_manager  # Получаем объект DatabaseManager через конструктор

    @discord.ui.button(label="Лайки поставил!", style=discord.ButtonStyle.success)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            user_id = str(interaction.user.id)
            user_mention = interaction.user.mention
            now = datetime.now()

            last_like_time = self.db_manager.get_last_like_time(user_id)
            if last_like_time:
                last_like_time = datetime.fromisoformat(last_like_time)
                if now - last_like_time < timedelta(hours=24):
                    time_remaining = timedelta(hours=24) - (now - last_like_time)
                    time_remaining = timedelta(seconds=time_remaining.seconds)
                    await interaction.followup.send(
                        f'{user_mention}, вы можете поставить лайки снова через {time_remaining}', ephemeral=True)
                    return

            self.db_manager.update_like_time(user_id)
            await interaction.followup.send(f'{user_mention}, Спасибо, что поставили лайки.', ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой лайка: {e}")

class CheckOnline(View):
    def __init__(self, db_manager,user_id):
        self.user_id=user_id
        self.start_time = datetime.now()
        self.message = None
        super().__init__(timeout=300)
        self.db_manager = db_manager  # Получаем объект DatabaseManager через конструктор

    async def on_timeout(self):
        """Этот метод будет вызван по истечении времени тайм-аута."""
        try:
            self.db_manager.end_admin_check_session(self.user_id)
            self.db_manager.end_admin_session(self.user_id)
            self.db_manager.update_admin_rep_multy(self.user_id, 0.8)
        except Exception as e:
            print(f"Ошибка таймаута: {e}")
        finally:
            # Обновляем кнопки
            for item in self.children:
                item.disabled = True
            if self.message:  # Проверка, что message не равно None
                await self.message.edit(view=self)  # Обновляем сообщение с новым представлением
            self.stop()

    @discord.ui.button(label="Да, я в сети!", style=discord.ButtonStyle.success)
    async def confirm_online(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            user_mention = interaction.user.mention
            await interaction.followup.send(f'{user_mention}, Спасибо, что помогаете серверу', ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой подтверждения работы: {e}")
        finally:
            remaining_time = self.get_remaining_time()
            self.db_manager.update_admin_rep(self.user_id, remaining_time)
            self.db_manager.end_admin_check_session(self.user_id)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            self.stop()


    @discord.ui.button(label="Я отдыхаю", style=discord.ButtonStyle.danger)
    async def button_free(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            user_mention = interaction.user.mention
            await interaction.followup.send(f'{user_mention}, Спасибо, что помогаете серверу', ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой отдыха: {e}")
        finally:
            self.db_manager.end_admin_check_session(self.user_id)
            self.db_manager.end_admin_session(self.user_id)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            self.stop()

    async def setup_message(self, message):
        """Метод для установки атрибута message."""
        self.message = message

    def get_remaining_time(self):
        """Вычисляет оставшееся время до таймаута в секундах."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        remaining_time = max(self.timeout - elapsed_time, 0)  # Вычисляем остаток времени
        return remaining_time


class WorkButtons(View):
    def __init__(self, db_manager):
        super().__init__(timeout=None)
        self.db_manager = db_manager  # Получаем объект DatabaseManager через конструктор

    @discord.ui.button(label="Я работаю", style=discord.ButtonStyle.success)
    async def button_work(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            if self.db_manager.get_current_status(interaction.user.id) == 1:
                await interaction.followup.send("Вы уже админите!", ephemeral=True)
            else:
                await interaction.followup.send("Забань всех читеров и токсиков!", ephemeral=True)
                self.db_manager.add_admin_session(str(interaction.user.id))
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой работы: {e}")

    @discord.ui.button(label="Я отдыхаю", style=discord.ButtonStyle.danger)
    async def button_free(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            if self.db_manager.get_current_status(interaction.user.id) == 1:
                await interaction.followup.send("Спасибо за то что админили на сервере!", ephemeral=True)
                self.db_manager.end_admin_session(str(interaction.user.id))
            else:
                await interaction.followup.send("Вы еще не начинали админить!", ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой отдыха: {e}")


class AdminButtons(View):
    def __init__(self, bot: discord.Client, db_manager):
        super().__init__(timeout=None)
        self.bot = bot
        self.db_manager = db_manager  # Получаем объект DatabaseManager через конструктор

    @discord.ui.button(label="Работающие админы", style=discord.ButtonStyle.primary)
    async def button_admins(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            working_admins = self.db_manager.get_working_admins()
            if working_admins:
                working_admin_mentions = [f"<@{user_id}>" for user_id in working_admins]
                await interaction.followup.send(f'Работающие администраторы: {", ".join(working_admin_mentions)}',
                                                        ephemeral=True)
            else:
                await interaction.followup.send('Нет работающих администраторов.', ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой админов: {e}")

    @discord.ui.button(label="Кто поставил лайки", style=discord.ButtonStyle.primary)
    async def button_likes(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            like_times = self.db_manager.get_all_like_times()
            if not like_times:
                await interaction.followup.send("Никто не поставил лайки", ephemeral=True)
            else:
                like_list = [f'<@{user_id}> - {timestamp}' for user_id, timestamp in like_times.items()]
                await interaction.followup.send('\n'.join(like_list), ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой лайков: {e}")

    @discord.ui.button(label="Обновить список админов", style=discord.ButtonStyle.primary)
    async def button_get_role_members(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            role_name = "ADMIN"
            guild = interaction.guild
            if guild is None:
                return

            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                await interaction.followup.send(f'Роль с именем "{role_name}" не найдена.', ephemeral=True)
                return

            member_ids = [member.id for member in guild.members if role in member.roles]
            if not member_ids:
                await interaction.followup.send(f'Нет пользователей с ролью "{role_name}".', ephemeral=True)
            else:
                # Сохраняем список в файл
                with open(self.bot.alladminsfile, 'w') as file:
                    json.dump(member_ids, file)
                await interaction.followup.send(f'ID пользователей с ролью "{role_name}" сохранены в файл.',ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой обновления списка: {e}")

    @discord.ui.button(label="Пиздануть админов которые не поставили лайки", style=discord.ButtonStyle.primary)
    async def button_pizdanut(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            with open(self.bot.alladminsfile, 'r') as file:
                member_ids = json.load(file)
            for user_id in member_ids:
                if self.db_manager.get_last_like_time(str(user_id)) is None:
                    await self.bot.messages.SendLikeMessageToUser(user_id)

            await interaction.followup.send("Я им написал!", ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой пиздануть админов: {e}")

    @discord.ui.button(label="Пиздануть админов которые типа онлайн", style=discord.ButtonStyle.primary)
    async def button_pizdanut_online(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            working_admins=self.db_manager.get_working_admins()

            for user_id in working_admins:
                await self.bot.messages.SendCheckOnlineMessageToUser(user_id)

            await interaction.followup.send("Я им написал!", ephemeral=True)
        except Exception as e:
            print(f"ошибка взаимодействия с кнопкой пиздануть админов: {e}")

    @discord.ui.button(label="Показать информацию обо всех администраторах таблицей", style=discord.ButtonStyle.primary)
    async def show_all_admins_table(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            all_admins = self.db_manager.get_all_admins()

            if all_admins:
                # Заголовок таблицы
                table_header = (
                    "**Репутация** \t **Количество лайков** \t **Общий онлайн** \t\t\t\t **Упоминание пользователя** \n"
                )

                table_rows = []
                for row in all_admins:
                    user_id = row[1]
                    user_mention = f"<@{user_id}>"

                    total_seconds = row[4]+row[6]
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_duration = f"{hours} часов {minutes} минут"

                    rep_format = int(row[2])

                    # Формируем строку таблицы
                    table_row = (
                        f"{rep_format:10}\t\t\t\t\t\t"
                        f"{row[3]:5}\t\t\t\t\t\t"
                        f"{formatted_duration:20}\t\t\t"
                        f"{user_mention}"
                    )

                    table_rows.append(table_row)

                # Объединяем заголовок и строки таблицы
                table = table_header + "\n".join(table_rows)

                await interaction.followup.send(table, ephemeral=True)
            else:
                await interaction.followup.send("Нет информации о администраторах.", ephemeral=True)

        except Exception as e:
            print(f"Ошибка взаимодействия с кнопкой информации обо всех администраторах: {e}")

    @discord.ui.button(label="Вывод средств", style=discord.ButtonStyle.primary)
    async def admin_cache(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            all_admins = self.db_manager.get_all_admins()

            if all_admins:
                # Заголовок таблицы
                table_header = (
                    "**Готово**\n"
                )

                table_rows = []
                for admin in all_admins:
                    duration=admin[4]
                    self.db_manager.update_admin_old_duration(admin[1],duration)
                    cache=duration//360
                    cache=cache+(admin[3]*10)
                    table_row=f"mm_shop_give_currency {admin[5]} rubles {cache}"
                    table_rows.append(table_row)
                    self.db_manager.clear_admin(admin[1])

                # Объединяем заголовок и строки таблицы
                table = table_header + "\n".join(table_rows)

                await interaction.followup.send(table, ephemeral=True)
            else:
                await interaction.followup.send("Нет информации о администраторах.", ephemeral=True)

        except Exception as e:
            print(f"Ошибка взаимодействия с кнопкой информации обо всех администраторах: {e}")
class UserButtons(View):
    def __init__(self, db_manager):
        super().__init__(timeout=None)
        self.db_manager = db_manager

    @discord.ui.button(label="Статистика", style=discord.ButtonStyle.primary)
    async def show_user_info(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            # Получаем информацию о пользователе
            admin_info = self.db_manager.get_admin_info(interaction.user.id)
            if admin_info:
                user_id, rep, like_count, total_duration, steam_id, old_duration, is_active = admin_info[1:]

                # Форматируем общую продолжительность в дни часы минуты секунды
                duration = total_duration+old_duration
                hours, remainder = divmod(duration, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_duration = f"{hours} часов {minutes} минут {seconds} секунд"
                rep_format= int(rep)
                # Получаем упоминание пользователя
                user_mention = f"<@{interaction.user.id}>"

                # Формируем сообщение с информацией
                info_message = (
                    f"**Упоминание пользователя**: {user_mention}\n"
                    f"**Репутация**: {rep_format}\n"
                    f"**Количество лайков**: {like_count}\n"
                    f"**Общий онлайн**: {formatted_duration}"
                )
            else:
                info_message = "Информация о пользователе не найдена."

            await interaction.followup.send(info_message, ephemeral=True)
        except Exception as e:
            print(f"Ошибка взаимодействия с кнопкой статистики: {e}")