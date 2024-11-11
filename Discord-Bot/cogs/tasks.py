from discord.ext import commands, tasks
from datetime import datetime, timedelta

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remind_likes.start()  # Запускаем задачу напоминания
        self.check_admin_sessions.start()  # Запускаем задачу проверки сессий
        self.admins_update.start()

    @tasks.loop(minutes=10)
    async def remind_likes(self):
        try:

            like_times = self.bot.db_manager.get_all_like_times()
            for user_id, last_like_str in like_times.items():
                last_like = datetime.fromisoformat(last_like_str)
                if datetime.now() - last_like >= timedelta(hours=24):
                    self.bot.db_manager.delete_like_time(user_id)
                    await self.bot.messages.SendLikeMessageToUser(user_id)
        except Exception as e:
            print(f"Error in remind_likes: {e}")

    @tasks.loop(minutes=5)
    async def check_admin_sessions(self):
        try:
            # Получаем список всех работающих админов
            working_admins = self.bot.db_manager.get_working_admins()

            for admin_id in working_admins:

                # Получаем время активной сессии в секундах
                session_time = self.bot.db_manager.get_active_session_time(admin_id)
                # Получаем репутацию администратора
                admin_rep = self.bot.db_manager.get_admin_rep(admin_id)
                if session_time > admin_rep:  # Если время сессии больше, чем репутация (в минутах)
                    # Проверяем последнюю сессию проверки администратора
                    last_check_session = self.bot.db_manager.get_last_check_session(admin_id)
                    if last_check_session is None or (datetime.now() - datetime.fromisoformat(last_check_session['start_time'])) >= timedelta(seconds=(admin_rep-300)):
                        # Если нет сессии проверки или она устарела, отправляем запрос на проверку активности
                        await self.bot.messages.SendCheckOnlineMessageToUser(admin_id)
        except Exception as e:
            print(f"Error in check_admin_sessions: {e}")

    @tasks.loop(minutes=11)
    async def admins_update(self):
        try:
            self.bot.db_manager.remove_duplicates_keep_max_like_count()
            total_durations = self.bot.db_manager.get_total_duration_for_admin_sessions()
            for user_id, duration in total_durations.items():
                self.bot.db_manager.add_admin(user_id)
                self.bot.db_manager.update_total_duration(user_id, duration)
        except Exception as e:
            print(f"Error in admins_update: {e}")

# Функция для загрузки Cog
async def setup(bot):
    await bot.add_cog(TasksCog(bot))
