from discord.ext import commands
from config import TOKEN, POSTGRES
import discord
import asyncpg
import re


def avatar(user):
    fmt = 'gif' if user.is_avatar_animtated() else 'png'
    return str(user.avatar_url_as(format=fmt))


STATUS = 'world peace'
QUERIES = (
    '''CREATE TABLE IF NOT EXISTS tags (
       "id" SERIAL PRIMARY KEY,
       "name" VARCHAR(64) UNIQUE,
       "message" TEXT,
       "author_id" BIGINT,
       "timestamp" INTEGER,
       "uses" INTEGER
       )
    ''',
)
COGS = (
    'jishaku',
    'cogs.tags',
    'cogs.music'
)

bot = commands.Bot(
    command_prefix=['hb!', 'Hb!', 'HB!'],
    case_insensitive=True,
    help_command=None,
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=STATUS
    ),
    intents=discord.Intents.all()
)
bot.avatar = avatar
default = re.compile('^http[s]?://cdn[.]discordapp[.]com/embed/avatars/[0-4][.]png')


@bot.command()
async def members(ctx):
    bots = len(list(filter(lambda m: m.bot, ctx.guild.members)))
    humans = ctx.guild.member_count - bots
    online = len(list(filter(lambda m: m.status is not discord.Status.offline, ctx.guild.members)))
    offline = ctx.guild.member_count - online
    defaults = len(list(filter(lambda m: default.match(str(m.avatar_url_as(format='png'))), ctx.guild.members)))

    embed = discord.Embed(
        color=discord.Colour.blurple()
    )
    embed.add_field(name='Total', value=str(ctx.guild.member_count))
    embed.add_field(name='Bots', value=str(bots))
    embed.add_field(name='Humans', value=str(humans))
    embed.add_field(name='Online', value=str(online))
    embed.add_field(name='Offline', value=str(offline))
    embed.add_field(name='Defaults', value=str(defaults))
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        missing = error.missing_perms[0].replace('_', ' ').title()
        embed = discord.Embed(
            color=discord.Colour.red(),
            title=f'You are missing the {missing} perms.'
        )
        return await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            color=discord.Colour.red(),
            title=f'You are missing the <{error.param.name}> argument.'
        )
        return await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        arg = re.findall('"(.+?)"', error.args[0])
        embed = discord.Embed(
            color=discord.Colour.red(),
            title=f'You put an invalid argument: {arg}'
        )
        return await ctx.send(embed=embed)
    else:
        raise error


async def start():
    bot.db = await asyncpg.create_pool(**POSTGRES)
    [await bot.db.execute(query) for query in QUERIES]
    await bot.wait_until_ready()
    [bot.load_extension(cog) for cog in COGS]
    print(discord.utils.oauth_url(bot.user.id))


bot.loop.create_task(start())
bot.run(TOKEN)
