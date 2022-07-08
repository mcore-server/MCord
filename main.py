#!/usr/bin/env python3.10
import discord, requests, time
import json, random, mcrcon
import os, subprocess, asyncio
import textwrap, threading

from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View
from mcrcon import MCRcon

bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
bot.remove_command('help')

try:
	cred_file = open('configuration.secret', 'r')
	configuration = cred_file.read().split('\n')
	cred_file.close()
except FileNotFoundError:
	print('Creating configuration file for you...')
	open('configuration.secret', 'w').write('discord bot token\nminecraft server ip\nminecraft rcon port\nminecraft rcon password\nfull path to your minecraft server')
	print('edit configuration.secret text file and run me!')
	exit()

BOT_TOKEN = configuration[0]

SERVER_IP = configuration[1]
RCON_PORT = int(configuration[2])
RCON_PASSWD = configuration[3]
SERVER_PATH = configuration[4]

if SERVER_PATH.endswith('/'):
	SERVER_PATH = SERVER_PATH[:-1]

START_TIME = datetime.now()

class MinecraftServer:
	def __init__(self, _process=None):
		self.process = _process
	def start(self):
		executable = SERVER_PATH + '/start.sh'
		os.chdir(SERVER_PATH)
		proc = subprocess.Popen(executable, stdout=subprocess.DEVNULL)
		print(proc.pid)
		print(proc)
		print(proc.stdin)
		return proc
	def stop(self):
		print('stop', file=process.stdin)
		time.sleep(5)
		self.process.kill()
	def console(self):
		logs_file = open(SERVER_PATH + '/logs/latest.log')
		logs = logs_file.read()
		logs_file.close()
		return logs
	def command(self, cmd):
		print(cmd, file=self.process.stdin)

async def long_delay():
	# Long delay cycle
	paper_builds = await paper_update()
	while True:
		# Checking paper updates
		await asyncio.sleep(300)

		new_paper_builds = await paper_update()
		response = await paper_update('check', paper_builds, new_paper_builds)

		if response:
			paper_builds = new_paper_builds

		# Updating stats
		await update_stats()

async def console_logger(proc):
	console_log = MinecraftServer(proc).console()
	while True:
		await asyncio.sleep(1)
		console_channel = bot.get_channel(984545711364386856)

		new_clog = MinecraftServer(proc).console()

		if len(new_clog) != len(console_log) and len(new_clog) > 1:
			if 'Thread RCON Client /127.0.0.1' in new_clog: return
			console_log = new_clog.replace(console_log, '')

			if len(console_log) > 2000:
				for part in textwrap.wrap(console_log, 2000):
					await console_channel.send(f'`{part}`')
					return

			await console_channel.send(f'`{console_log}`')

###############################

# Check Paper updates
async def paper_update(function='get', *args):
	match function:
		case 'get':
			# get list of paper builds
			paper_builds = json.loads(requests.get('https://api.papermc.io/v2/projects/paper/version_group/1.19/builds').text)["builds"]
			return paper_builds
		case 'check':
			# checking updates
			if len(args[0]) < len(args[1]):
				update_channel = bot.get_channel(982254771534704641)

				paper_builds = args[1]

				last_build = paper_builds[-1]
		
				# some variables
				number = last_build["build"]; version = last_build["version"]; changes = last_build["changes"]; commit_url = f'https://github.com/paperMC/paper/commit/{last_build["changes"][0]["commit"]}'; download_url = f'https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{number}/downloads/paper-{version}-{number}.jar'

				# generating buttons
				buttons = [Button(label='Скачать', style=discord.ButtonStyle.green, url=download_url),Button(label='GitHub', style=discord.ButtonStyle.green, url=commit_url)]
				view = View()

				# appending buttons to list
				for btn in buttons:
					view.add_item(btn)

				# generating embed
				embed=discord.Embed(title='Найдено обновление!', description=f'`PaperMC {version} | #{number}`\n`{changes[0]["summary"]}`')
				embed.set_author(name='PaperMC', icon_url='https://media.discordapp.net/attachments/981094724939153448/994578831996366878/unknown.png')
				embed.timestamp = datetime.now()

				await update_channel.send(embed=embed, view=view)
				
				# returning true value because there's new paper version
				return True
			else:
				# returning false cause there's no new paper version :(
				return False

# Update statistics category
async def update_stats():
	online_channel = bot.get_channel(984165492224831508) # Channel showing server online
	tps_channel = bot.get_channel(984165542699085855) # Channel showing server TPS

	with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
		tps = mcr.command("papi parse --null %server_tps_1%")[:-1]
		online = mcr.command("papi parse --null %server_online%")[:-1]
	
	await tps_channel.edit(name=f'TPS: {tps}')
	await online_channel.edit(name=f'Онлайн: {online}')

###############################

@bot.event
async def on_ready():
	took_time = datetime.now()-START_TIME
	print(f'[{time.strftime("%H:%M:%S")}] Done! (took {took_time.seconds}s)')
	bot.loop.create_task(long_delay())

@bot.event
async def on_message(m):
	# await bot.process_commands(m)
	#global proc
	msg = m.content.lower()

	if m.author == bot.user: return

	if m.channel.id == 984545711364386856:
		match msg:
			case 'start':
				await m.channel.send(':white_check_mark: `Запускаю сервер...`')
				proc = MinecraftServer().start()
				bot.loop.create_task(console_logger(proc))
			case _:
				try:
					with MCRcon(SERVER_IP, RCON_PASSWD, port=RCON_PORT) as mcr:
						output = mcr.command(m.content)
					await m.channel.send(f'`{output}`')
				except ConnectionRefusedError:
					await m.channel.send('Сервер не запущен. Напишите `start` для запуска.')
		return

	match msg:
		case '!ping':
			await m.channel.send('pong')


@bot.event
async def on_voice_state_update(member,_,after):
	if after.channel is not None:
		if after.channel.id == 981955747577475083:
			# getting category; defining variables
			ctg = discord.utils.get(member.guild.categories, id=961942312588542022)
			emojis = ['🔶', '🔥', '⭐️', '⚡️', '✨', '🟠']
			username = member.name

			if member.nick is not None:
				username = member.nick

			# creating voice channel, adding permissions and moving member to this channel
			chn = await guild.create_voice_channel(name=f"{random.choice(emojis)} {username}",category=ctg)

			await chn.set_permissions(member, connect=True, move_members=True, manage_channels=True)
			await member.move_to(chn)

			def check(*args):
				# is channel empty?
				return len(chn.members) == 0

			await bot.wait_for('voice_state_update',check=check)
			await chn.delete()

if __name__ == '__main__':
	print(f'[{time.strftime("%H:%M:%S")}] Starting...')
	bot.run(BOT_TOKEN)