from discord.ext import commands
import discord
import time
import asyncpg
from difflib import SequenceMatcher
from cogs.menus import TagMenu


class Tags(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def validate_author(self, ctx, name: str):
        query = '''SELECT author_id, id
                   FROM tags
                   WHERE name = $1
                '''
        res = await self.bot.db.fetchrow(query, name)
        if not res:
            embed = discord.Embed(
                color=discord.Colour.red(),
                title=f'The tag with name "{name}" was not found.'
            )
            await ctx.send(embed=embed)
            raise RuntimeError()
        if res['author_id'] != ctx.author.id and \
                not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                color=discord.Colour.red(),
                title=f'To edit a tag, you must own the it or have admin perms.'
            )
            await ctx.send(embed=embed)
            raise RuntimeError()
        return res

    async def send_tag(self, ctx, name: str, *, raw=False):
        query = '''SELECT message, id
                   FROM tags
                   WHERE name = $1
                '''
        res = await self.bot.db.fetchrow(query, name)
        if not res:
            query = '''SELECT name, message
                       FROM tags
                    '''
            res = [row['name'] for row in await self.bot.db.fetch(query)]
            dicted = {entry: SequenceMatcher(None, name, entry).ratio() for entry in res}
            sort = sorted(dicted.items(), key=lambda item: item[1])
            filtered = [f'`{name[0]}`' for name in sort if name[1] > 0.69]
            if not filtered:
                embed = discord.Embed(
                    color=discord.Colour.red(),
                    title=f'Tag "{name}" not found.'
                )
                return await ctx.send(embed=embed)
            else:
                similar = ', '.join(filtered)
                embed = discord.Embed(
                    title=f'Tag "{name}" not found. You might have meant:',
                    description=similar,
                    color=discord.Colour.red()
                )
                return await ctx.send(embed=embed)

        message = res['message']
        message = message if not raw else discord.utils.escape_markdown(message)
        await ctx.send(message)

        if not raw:
            query = '''UPDATE tags
                       SET uses = uses + 1
                       WHERE id = $1
                    '''
            await self.bot.db.execute(query, res['id'])

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, name: str):
        await self.send_tag(ctx, name.lower())

    @tag.command()
    async def raw(self, ctx, *, name: str):
        await self.send_tag(ctx, name, raw=True)

    @tag.command()
    async def add(self, ctx, name: str, *, message: str):
        name, message = name.strip().lower(), message.strip()
        query = '''INSERT INTO tags (name, message, author_id, timestamp, uses)
                   VALUES ($1, $2, $3, $4, $5)
                '''
        try:
            await self.bot.db.execute(
                query,
                name,
                message,
                ctx.author.id,
                int(time.time()),
                0
            )
        except asyncpg.UniqueViolationError:
            embed = discord.Embed(
                color=discord.Colour.red(),
                title=f'Tag "{name}" already exists.'
            )
            return await ctx.send(embed=embed)
        embed = discord.Embed(
            color=discord.Colour.green(),
            title=f'A tag called "{name}" was created by {ctx.author}!'
        )
        await ctx.send(embed=embed)

    @tag.command()
    async def edit(self, ctx, name: str, *, new: str):
        try:
            res = await self.validate_author(ctx, name.lower())
        except RuntimeError:
            return

        query = '''UPDATE tags
                   SET message = $1
                   WHERE id = $2
                '''
        await self.bot.db.execute(query, new, res['id'])
        embed = discord.Embed(
            color=discord.Colour.green(),
            title=f'Tag "{name}" was updated by {ctx.author}!'
        )
        await ctx.send(embed=embed)

    @tag.command()
    async def delete(self, ctx, *, name):
        try:
            res = await self.validate_author(ctx, name.lower())
        except RuntimeError:
            return
        query = '''DELETE FROM tags
                   WHERE id = $1
                '''
        await self.bot.db.execute(query, res['id'])
        embed = discord.Embed(
            color=discord.Colour.green(),
            title=f'Tag "{name}" was deleted by {ctx.author}!'
        )
        await ctx.send(embed=embed)

    @tag.command()
    async def all(self, ctx):
        await TagMenu().start(ctx)


def setup(bot):
    bot.add_cog(Tags(bot))
