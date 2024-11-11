from discord.ext import commands

class CustomPermissionError(commands.CommandError):
    pass

def has_permissions(ctx,allowed_user):
    if ctx.author.id != allowed_user:
        raise commands.MissingPermissions(["У вас нет прав для использования этой команды."])
    return True

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return has_permissions(ctx,self.bot.allowed_user)

    @commands.command(name='buttonAdmins')
    async def buttonAdmins(self, ctx):
        await self.bot.messages.SendAdminMessage(ctx)

    @commands.command(name='buttonWork')
    async def buttonWork(self, ctx):
        await self.bot.messages.SendWorkMessage(ctx)

    @commands.command(name='buttonLike')
    async def buttonLike(self, ctx):
        await self.bot.messages.SendLikeMessage(ctx)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
