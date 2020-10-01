from discord.ext import commands
from cogs import yt
import discord


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        if not ctx.author.voice:
            embed = discord.Embed(
                color=discord.Colour.red(),
                title=f'You are not in a VC.'
            )
            return await ctx.send(embed=embed)
        channel = channel or ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        embed = discord.Embed(
            color=discord.Colour.green(),
            title=f'I have joined {channel.name}! Do {ctx.prefix}play to play some music.'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def play(self, ctx, *, search):
        async with ctx.typing():
            if not ctx.voice_client:
                if not ctx.author.voice:
                    embed = discord.Embed(
                        color=discord.Colour.red(),
                        title=f'You are not in a VC.'
                    )
                    return await ctx.send(embed=embed)
                channel = ctx.author.voice.channel
                if ctx.voice_client is not None:
                    await ctx.voice_client.move_to(channel)
                else:
                    await channel.connect()

            results = await yt.YoutubeSearch(self.bot.loop, search, max_results=1).to_dict()
            url = f'https://youtube.com/watch?v=' + results[0]['id']
            player = await yt.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player)

        await ctx.send(f'**Now playing `{player.title}`**')

    @commands.command()
    async def volume(self, ctx, volume: int):
        if not ctx.me.voice:
            embed = discord.Embed(
                color=discord.Colour.red(),
                title=f'I am not connected to a VC.'
            )
            return await ctx.send(embed=embed)

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to `{volume}`.")

    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()


def setup(bot):
    bot.add_cog(Music(bot))
