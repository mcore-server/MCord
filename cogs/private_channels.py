import discord
import random

from mcrcon import MCRcon
from discord.ext import commands
from asyncio import sleep


class VoiceChannelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, _, after):
        if after.channel is not None:
            if after.channel.id == 981955747577475083:
                # get category; define variables
                ctg = discord.utils.get(member.guild.categories, id=961942312588542022)
                emojis = ["🔥", "⭐️", "⚡️", "✨"]
                username = member.name

                if member.nick is not None:
                    username = member.nick

                # create voice channel, add permissions and move member to this channel
                chn = await member.guild.create_voice_channel(
                    name=f"{random.choice(emojis)} {username}", category=ctg
                )

                await chn.set_permissions(
                    member, connect=True, move_members=True, manage_channels=True
                )
                await member.move_to(chn)

                def check(*args):
                    # is channel empty?
                    return len(chn.members) == 0

                await self.bot.wait_for("voice_state_update", check=check)
                await chn.delete()


def setup(bot):
    bot.add_cog(VoiceChannelsCog(bot))
