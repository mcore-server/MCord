import discord
import json
import requests

from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from asyncio import sleep


class Paper:
    def __init__(self, bot):
        self.bot = bot

    def generate_message(self, build):
        # some variables
        number = build["build"]
        version = build["version"]
        changes = build["changes"]
        commit_url = (
            f"https://github.com/paperMC/paper/commit/{build['changes'][0]['commit']}"
        )
        download_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{number}/downloads/paper-{version}-{number}.jar"

        # generate buttons
        buttons = [
            Button(
                label="Скачать",
                style=discord.ButtonStyle.green,
                url=download_url,
            ),
            Button(label="GitHub", style=discord.ButtonStyle.green, url=commit_url),
        ]  # buttons download and github
        view = View()

        # append buttons to list
        for btn in buttons:
            view.add_item(btn)

        # generate embed
        embed = discord.Embed(
            title="Последнее обновление",
            description=f'`PaperMC {version} | #{number}`\n`{changes[0]["summary"]}`',
        )  # found update
        embed.set_author(
            name="PaperMC",
            icon_url="https://media.discordapp.net/attachments/981094724939153448/994578831996366878/unknown.png",
        )
        embed.timestamp = datetime.now()

        return embed, view

    async def paper_check(self):
        # get list of paper builds
        paper_builds = json.loads(
            requests.get(
                "https://api.papermc.io/v2/projects/paper/version_group/1.19/builds"
            ).text
        )["builds"]
        return paper_builds

    async def paper_update(self, pb):
        update_channel = self.bot.get_channel(982254771534704641)

        last_build = pb[-1]

        embed, view = await Paper(self.bot).generate_message(last_build)

        await update_channel.send(embed=embed, view=view)

    async def loop(self):
        paper_builds = await Paper(self.bot).paper_check()
        while True:
            await sleep(120)

            new_paper_builds = await Paper(self.bot).paper_check()
            if len(paper_builds) == len(new_paper_builds):
                return
            response = await Paper(self.bot).paper_update(new_paper_builds)

            if response:
                paper_builds = new_paper_builds


class PaperUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_start(self):
        self.bot.loop.create_task(Paper(self.bot).loop())

    @commands.Cog.listener()
    async def on_message(self, m):
        msg = m.content.lower()

        if m.author == self.bot.user:
            return

        if msg.startswith("#"):
            if not m.author.guild_permissions.mention_everyone:
                return
            command = msg[1:].split(" ")[0]
            match command:
                case "paper":
                    last_build = await Paper(self.bot).paper_check()
                    last_build = last_build[-1]
                    embed, view = Paper(self.bot).generate_message(last_build)
                    await m.channel.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(PaperUpdateCog(bot))
