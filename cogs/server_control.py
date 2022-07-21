import discord
import sys
import os
import textwrap
import config
import subprocess

from discord.ext import commands
from loguru import logger
from asyncio import sleep
from mcrcon import MCRcon

logger.remove()
logger.add(sys.stdout, format="[{time:HH:mm:ss}] <lvl>{message}</lvl>", level="INFO")

SERVER_IP = getattr(config, "ip", None)
RCON_PORT = getattr(config, "rport", None)
RCON_PASSWD = getattr(config, "rpasswd", None)
SERVER_PATH = getattr(config, "server_path", None)


class MinecraftServer:
    def __init__(self, bot):
        self.bot = bot

    def start(self):
        executable = SERVER_PATH + "/start.sh"
        os.chdir(SERVER_PATH)
        proc = subprocess.Popen(executable, stdout=subprocess.DEVNULL)
        return proc

    def console(self):
        with open(SERVER_PATH + "/logs/latest.log") as logfile:
            logs = logfile.read()
            logfile.close()
        return logs

    async def loop(self):
        # Get server logs
        # console_log = MinecraftServer(self.bot).console()
        console_channel = self.bot.get_channel(984545711364386856)
        last_log = ""
        while True:
            await sleep(0.1)

            try:
                log = MinecraftServer(self.bot).console().split("\n")[-2]
            except IndexError:
                log = MinecraftServer(self.bot).console().split("\n")[-1]

            if log != last_log and len(log) > 1:
                last_log = log
                if not "Thread RCON Client /127.0.0.1" in log:
                    if len(log) > 2000:
                        for part in textwrap.wrap(log, 1999):
                            await console_channel.send(f"`{part}`")
                    else:
                        await console_channel.send(f"`{log}`")


class McControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author == self.bot.user:
            return
        msg = m.content.lower()
        match m.channel.id:
            case 984545711364386856:
                match msg:
                    case "start":
                        logger.warning(
                            f"{m.author.name}#{m.author.discriminator} started server"
                        )
                        await m.channel.send(":white_check_mark: `Запускаю сервер...`")
                        MinecraftServer(self.bot).start()
                        self.bot.loop.create_task(MinecraftServer(self.bot).loop())
                    case _:
                        if msg.startswith("#"):
                            return
                        try:
                            with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
                                output = mcr.command(m.content)
                            logger.warning(
                                f"{m.author.name}#{m.author.discriminator} issued RCON command: {m.content}"
                            )
                            await m.channel.send(f"`{output}`")
                        except ConnectionRefusedError:
                            await m.channel.send(
                                "Сервер не запущен. Напишите `start` для запуска."
                            )
                return


def setup(bot):
    bot.add_cog(McControlCog(bot))
