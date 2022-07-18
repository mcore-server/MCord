#!/usr/bin/env python3.10
import discord
import requests
import json
import random
import os
import subprocess
import asyncio
import textwrap
import sqlite3
import sys

from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View
from mcrcon import MCRcon
from loguru import logger
from shutil import copyfile

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')

logger.remove()
logger.add(sys.stdout, format="[{time:HH:mm:ss}] <lvl>{message}</lvl>", level='INFO')
con = sqlite3.connect('db/bot.db')
cur = con.cursor()

try:
	import config
except ModuleNotFoundError:
	logger.error('Your configuration file not found!')
	copyfile('examples/config.py', 'config.py')
	logger.info('Please edit config.py to run bot')
	exit()

if getattr(config, "token", None) == 'TOKEN':
	logger.error('You did not edited the config file! Please edit it (config.py)')
	exit()

BOT_TOKEN = getattr(config, "token", None)

SERVER_IP = getattr(config, "ip", None)
RCON_PORT = getattr(config, "rport", None)
RCON_PASSWD = getattr(config, "rpasswd", None)
SERVER_PATH = getattr(config, "server_path", None)

if SERVER_PATH.endswith('/'):
	SERVER_PATH = SERVER_PATH[:-1]

START_TIME = datetime.now()

class MinecraftServer:
	def start():
		executable = SERVER_PATH + '/start.sh'
		os.chdir(SERVER_PATH)
		proc = subprocess.Popen(executable, stdout=subprocess.DEVNULL)
		return proc

	def console():
		logs_file = open(SERVER_PATH + '/logs/latest.log')
		logs = logs_file.read()
		logs_file.close()
		return logs

# Long delay cycle


async def long_delay():
	paper_builds = await paper_update()
	while True:
		# Check paper updates
		await asyncio.sleep(300)

		new_paper_builds = await paper_update()
		response = await paper_update('check', paper_builds, new_paper_builds)

		if response:
			paper_builds = new_paper_builds

		# Update statistics in voice channels
		await update_stats()


async def console_logger():
	# Get server logs
	console_log = MinecraftServer.console()
	while True:
		await asyncio.sleep(1)
		console_channel = bot.get_channel(984545711364386856)

		new_clog = MinecraftServer.console()

		print(new_clog)

		if len(new_clog) != len(console_log):
			console_log = new_clog.replace(console_log, '')
			#if 'Thread RCON Client /127.0.0.1' in console_log:
			#	return

			if len(console_log) > 2000:
				for part in textwrap.wrap(console_log, 1999):
					await console_channel.send(f'`{part}`')
					return

			await console_channel.send(f'`{console_log}`')

###############################

# Check Paper updates

@logger.catch()
async def paper_update(function='get', *args):
	match function:
		case 'get':
			# get list of paper builds
			paper_builds = json.loads(requests.get(
				'https://api.papermc.io/v2/projects/paper/version_group/1.19/builds').text)["builds"]
			return paper_builds	
		case 'check':
			# check updates
			if len(args[0]) < len(args[1]):
				update_channel = bot.get_channel(982254771534704641)

				paper_builds = args[1]

				last_build = paper_builds[-1]

				# some variables
				number = last_build["build"]
				version = last_build["version"]
				changes = last_build["changes"]
				commit_url = f'https://github.com/paperMC/paper/commit/{last_build["changes"][0]["commit"]}'
				download_url = f'https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{number}/downloads/paper-{version}-{number}.jar'

				# generate buttons
				buttons = [Button(label='Скачать', style=discord.ButtonStyle.green, url=download_url), Button(
					label='GitHub', style=discord.ButtonStyle.green, url=commit_url)] # buttons download and github
				view = View()

				# append buttons to list
				for btn in buttons:
					view.add_item(btn)

				# generate embed
				embed = discord.Embed(
					title='Найдено обновление!', description=f'`PaperMC {version} | #{number}`\n`{changes[0]["summary"]}`') # found update
				embed.set_author(
					name='PaperMC', icon_url='https://media.discordapp.net/attachments/981094724939153448/994578831996366878/unknown.png')
				embed.timestamp = datetime.now()

				await update_channel.send(embed=embed, view=view)

				# return true value because there's new paper version
				return True
			else:
				# return false cause there's no new paper version :(
				return False

# Update statistics category


async def update_stats():
	# Channel that show server online
	online_channel = bot.get_channel(984165492224831508)
	# Channel that show server TPS
	tps_channel = bot.get_channel(984165542699085855)

	try:
		with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
			tps = mcr.command("papi parse --null %server_tps_1%")[:-1]
			online = mcr.command("papi parse --null %server_online%")[:-1]
		tps_text = f'TPS: {tps}'
		online_text = f'Онлайн: {online}'
	except ConnectionRefusedError:
		tps_text = f'TPS: сервер выключен'
		online_text = f'Онлайн: сервер выключен'

	await tps_channel.edit(name=tps_text)
	await online_channel.edit(name=online_text)

###############################


@bot.event
async def on_ready():
	#cur.execute('''create table''')
	# con.commit()
	took_time = datetime.now()-START_TIME
	logger.info(f'Done! (took {took_time.seconds}s)')
	bot.loop.create_task(long_delay())


@bot.event
async def on_message(m):
	msg = m.content.lower()

	if m.author == bot.user:
		return

	if m.channel.id == 984545711364386856:
		match msg:
			case 'start':
				logger.warning(
					f'{m.author.name}#{m.author.discriminator} started server')
				await m.channel.send(':white_check_mark: `Запускаю сервер...`')  # ':white_check_mark: `Starting server...`'
				MinecraftServer.start()
				bot.loop.create_task(console_logger())
			case _:
				if msg.startswith('#'):
					return
				try:
					with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
						output = mcr.command(m.content)
					logger.warning(
						f'{m.author.name}#{m.author.discriminator} issued RCON command: {m.content}')
					await m.channel.send(f'`{output}`')
				except ConnectionRefusedError:
					await m.channel.send('Сервер не запущен. Напишите `start` для запуска.')  # 'Server not started. Type `start` for run server.'
		return

	# sudo commands
	if msg.startswith('#'):
		if not m.author.guild_permissions.mention_everyone:
			return
		command = msg[1:]
		match command:
			case 'log':
				arg = command.split(' ')[1:]
				if len(arg) == 1:
					db_log = cur.execute('SELECT * FROM logs WHERE id = ?', (arg[0])).fetchone()
				else:
					await m.channel.send('`#log <id>`')
					return

	match msg:
		case '!ping':
			await m.channel.send('pong')


@bot.event
async def on_voice_state_update(member, _, after):
	if after.channel is not None:
		if after.channel.id == 981955747577475083:
			# get category; define variables
			ctg = discord.utils.get(
				member.guild.categories, id=961942312588542022)
			emojis = ['🔥', '⭐️', '⚡️', '✨']
			username = member.name

			if member.nick is not None:
				username = member.nick

			# create voice channel, add permissions and move member to this channel
			chn = await member.guild.create_voice_channel(name=f"{random.choice(emojis)} {username}", category=ctg)

			await chn.set_permissions(member, connect=True, move_members=True, manage_channels=True)
			await member.move_to(chn)

			def check(*args):
				# is channel empty?
				return len(chn.members) == 0

			await bot.wait_for('voice_state_update', check=check)
			await chn.delete()

if __name__ == '__main__':
	logger.info('Starting...')
	for file in os.listdir("cogs"):
		if file.endswith(".py"):
			name = file[:-3]
			bot.load_extension(f"cogs.{name}")
	bot.run(BOT_TOKEN)
