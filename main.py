#!/usr/bin/env python3.10
import discord
import random
import os
import sqlite3
import sys
import mcaptcha
import asyncio

from datetime import datetime
from discord.ext import commands
from asyncio import sleep
from loguru import logger  # for logging
from shutil import copyfile  # for copying files


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

logger.remove()
logger.add(sys.stdout, format="[{time:HH:mm:ss}] <lvl>{message}</lvl>", level="INFO")
con = sqlite3.connect("db/bot.db")
cur = con.cursor()

try:
    import config
except ModuleNotFoundError:
    logger.error("Your configuration file not found!")
    copyfile("examples/config.py", "config.py")
    logger.info("Please edit config.py to run bot")
    exit()

if getattr(config, "token", None) == "TOKEN":
    logger.error("You did not edited the config file! Please edit it (config.py)")
    exit()

BOT_TOKEN = getattr(config, "token", None)

SERVER_IP = getattr(config, "ip", None)
RCON_PORT = getattr(config, "rport", None)
RCON_PASSWD = getattr(config, "rpasswd", None)
SERVER_PATH = getattr(config, "server_path", None)

if SERVER_PATH.endswith("/"):
    SERVER_PATH = SERVER_PATH[:-1]

START_TIME = datetime.now()


@bot.event
async def on_ready():
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INT,
        username INT,
        captcha INT,
        level INT,
        xp INT
    )"""
    )
    con.commit()
    took_time = datetime.now() - START_TIME
    logger.info(f"Done! (took {took_time.seconds}s)")


@bot.event
async def on_message(m):
    msg = m.content.lower()

    if m.author == bot.user:
        return

    match m.channel.id:
        case 961564061441613854:
            if len(m.author.roles) > 1:
                return
            try:
                tempdir = os.listdir("assets/temp")
                for f in tempdir:
                    if f.startswith(str(m.author.id)):
                        return
                await m.author.send(
                    "У вас есть только 3 попытки, чтобы правильно ввести текст с картинки."
                )
                captcha_file = mcaptcha.new(str(m.author.id))

                embed = discord.Embed(title="Регистрация", color=0x2F3136)
                discord_file = discord.File(captcha_file, filename="captcha.png")
                embed.set_image(url="attachment://captcha.png")
                await m.author.send(embed=embed, file=discord_file)
                cur.execute(
                    "INSERT INTO users VALUES (?,?,?,?,?)",
                    (
                        m.author.id,
                        None,
                        3,
                        0,
                        0,
                    ),
                )
                con.commit()

                def check(wmsg):
                    att = cur.execute(
                        "SELECT * FROM users WHERE id=?", (m.author.id,)
                    ).fetchone()[2]
                    tempdir = os.listdir("assets/temp")
                    for f in tempdir:
                        if f.startswith(str(m.author.id)):
                            captcha_text = f.split("_")[1].split(".")[0]
                    if (
                        wmsg.channel.type == discord.ChannelType.private
                        and wmsg.author == m.author
                    ):
                        if wmsg.content.upper() == captcha_text:
                            return True
                        else:
                            if att < 2:
                                return True
                            cur.execute(
                                "UPDATE users SET captcha=captcha-1 WHERE id=?",
                                (m.author.id,),
                            )
                            con.commit()
                            asyncio.create_task(
                                wmsg.channel.send("Неверно! Вы точно ввели правильно?")
                            )

                await bot.wait_for("message", check=check)
                os.remove(captcha_file)
                att = cur.execute(
                    "SELECT * FROM users WHERE id=?", (m.author.id,)
                ).fetchone()[2]
                if att < 2:
                    await m.author.send(
                        "Вы истратили все попытки на ввод капчи. Попробуйте позже."
                    )
                    cur.execute(
                        "UPDATE users SET captcha=? WHERE id=?",
                        (
                            3,
                            m.author.id,
                        ),
                    )
                    con.commit()
                    return

                role = discord.utils.get(m.guild.roles, id=961599861495570482)
                await m.author.add_roles(role)
                await m.author.send(
                    "Вы правильно ввели капчу. Теперь вы можете подавать заявку - <#961941284484939776>"
                )
            except discord.errors.Forbidden:
                temp_msg = await m.channel.send(
                    f"{m.author.mention}, у вас закрыты личные сообщения. Откройте их в настройках Discord"
                )
                await sleep(10)
                await temp_msg.delete()

    # sudo commands
    if msg.startswith("#"):
        if not m.author.guild_permissions.mention_everyone:
            return
        command = msg[1:].split(" ")[0]
        match command:
            case "purge":
                arg = msg.split(" ")[1:]
                if arg[0].isdigit():
                    await m.channel.purge(limit=arg[0])
    match msg:
        case "!ping":
            await m.channel.send("pong")


if __name__ == "__main__":
    logger.info("Starting...")
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            logger.info(f"Loading cog {name}...")
            bot.load_extension(f"cogs.{name}")
    bot.run(BOT_TOKEN)
