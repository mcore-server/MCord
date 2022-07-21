import discord
import config

from mcrcon import MCRcon
from discord.ext import commands
from asyncio import sleep

BOT_TOKEN = getattr(config, "token", None)

SERVER_IP = getattr(config, "ip", None)
RCON_PORT = getattr(config, "rport", None)
RCON_PASSWD = getattr(config, "rpasswd", None)
SERVER_PATH = getattr(config, "server_path", None)


class Statistic:
    def __init__(self, bot):
        self.bot = bot

    async def update_stats(self):
        # Channel that show server online
        online_channel = self.bot.get_channel(984165492224831508)
        # Channel that show server TPS
        tps_channel = self.bot.get_channel(984165542699085855)

        try:
            with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
                tps = mcr.command("papi parse --null %server_tps_1%")[:-1]
                online = mcr.command("papi parse --null %server_online%")[:-1]
            tps_text = f"TPS: {tps}"
            online_text = f"Онлайн: {online}"
        except ConnectionRefusedError:
            tps_text = f"TPS: сервер выключен"
            online_text = f"Онлайн: сервер выключен"

        await tps_channel.edit(name=tps_text)
        await online_channel.edit(name=online_text)

    async def loop(self):
        while True:
            await Statistic(self.bot).update_stats()
            await sleep(300)


class StatisticCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_start(self):
        self.bot.loop.create_task(Statistic(self.bot).loop())


def setup(bot):
    bot.add_cog(StatisticCog(bot))
