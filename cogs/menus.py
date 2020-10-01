from discord.ext.menus import Menu, button
from discord.ext.commands import Paginator
import discord
import asyncio


class TagMenu(Menu):

    def __init__(self):
        super().__init__(timeout=30, delete_message_after=True)
        self.pages = []
        self.page = 0

    @property
    def embed(self):
        embed = discord.Embed(
            color=discord.Colour.blurple(),
            description=self.pages[self.page]
        )
        embed.set_author(name=f'{self.page + 1} out of {len(self.pages)}')
        return embed

    async def send_initial_message(self, ctx, channel):
        query = '''SELECT name
                   FROM tags
                   ORDER BY name
                '''
        res = await ctx.bot.db.fetch(query)
        if not res:
            await ctx.send('No tags found.')
            self.stop()

        paginator = Paginator(prefix=None, suffix=None, max_size=420)
        i = 1
        for name in [row['name'] for row in res]:
            paginator.add_line(f'**{i}.** {name}')
            i += 1
        self.pages = paginator.pages
        return await ctx.send(embed=self.embed)

    @button('\u23ee')
    async def first(self, payload):
        if self.page != 0:
            self.page = 0
            await self.message.edit(embed=self.embed)

    @button('\u2b05')
    async def previous(self, payload):
        if self.page != 0:
            self.page -= 1
            await self.message.edit(embed=self.embed)

    @button('\u27a1')
    async def next(self, payload):
        if self.page != len(self.pages) - 1:
            self.page += 1
            await self.message.edit(embed=self.embed)

    @button('\u23ed')
    async def last(self, payload):
        index = len(self.pages) - 1
        if self.page != index:
            self.page = index
            await self.message.edit(embed=self.embed)

    @button('\U0001f522')
    async def jump(self, payload):
        m1 = await self.ctx.send("What page would you like to jump to?")

        def check(m):
            return m.channel.id == self.ctx.channel.id and m.author.id == self.ctx.author.id

        try:
            message = await self.bot.wait_for('message', timeout=15, check=check)
        except asyncio.TimeoutError:
            return

        try:
            page = int(message.content)
        except ValueError:
            return await self.ctx.send(
                embed=discord.Embed(
                    title=f'"{message.content}" is not a number.', color=discord.Colour.red()
                )
            )

        if not 1 <= page <= len(self.pages):
            return await self.ctx.send(
                embed=discord.Embed(
                    title=f'Page {page} does not exist.', color=discord.Colour.red()
                )
            )

        if page - 1 != self.page:
            self.page = page - 1
            await self.message.edit(embed=self.embed)

        await self.ctx.channel.delete_messages([m1, message])
