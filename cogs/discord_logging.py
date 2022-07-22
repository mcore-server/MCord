import discord
import sqlite3

from discord.ext import commands


class Logging:
    def __init__(self, bot, con):
        self.LOG_CHANNEL_1 = 992871458630013038  # Message logs channel
        self.LOG_CHANNEL_2 = 992871624514740264  # Event logs channel
        self.LOG_CHANNEL_3 = 992871638540505158  # Voice logs channel
        self.LOG_CHANNEL_4 = 992871652918566992  # Bot logs channel
        self.LOG_TYPES = {
            1: self.LOG_CHANNEL_1,
            2: self.LOG_CHANNEL_2,
            3: self.LOG_CHANNEL_3,
            4: self.LOG_CHANNEL_4,
        }
        self.bot = bot
        self.con = con
        self.cur = con.cursor()

    async def write_log(self, log_type, log_content, attachment=None):
        log_channel = self.bot.get_channel(self.LOG_TYPES[log_type])
        all_logs = self.cur.execute("SELECT * FROM log").fetchall()

        log_id = len(all_logs) + 1

        embed = discord.Embed(
            title=f"#{log_id} [{log_type}]", description=log_content, color=0x2F3136
        )

        if attachment:
            embed.set_image(attachment)

        log_message = await log_channel.send(embed=embed)

        self.cur.execute(
            "INSERT INTO log VALUES (?, ?, ?, ?, ?)",
            (
                log_id,
                log_type,
                log_message.id,
                log_content,
                attachment,
            ),
        )
        self.con.commit()


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.con = sqlite3.connect("db/log.db")
        self.cur = self.con.cursor()
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS log (
			id INT,
			type INT,
			message_id INT,
			content TEXT,
			attachment TEXT
		)"""
        )
        self.con.commit()

    @commands.Cog.listener()
    async def on_message(self, m):
        msg = m.content.lower()

        if m.author == self.bot.user:
            return

        # sudo commands
        if msg.startswith("#"):
            if not m.author.guild_permissions.mention_everyone:
                return
            command = msg[1:].split(" ")[0]
            log_content = f"{m.author} отправил боту sudo-команду: {m.content[1:]}\nКанал: <#{m.channel.id}>"
            await Logging(self.bot, self.con).write_log(4, log_content)
            match command:
                case "log":

                    arg = msg.split(" ")[1:]
                    if len(arg) == 1:
                        db_log = self.cur.execute(
                            "SELECT * FROM log WHERE id = ?", (int(arg[0]),)
                        ).fetchone()
                        if db_log is None:
                            await m.channel.send("Лог с таким номером не найден.")
                            return
                        embed = discord.Embed(
                            title=f"#{db_log[0]} [{db_log[1]}]",
                            description=db_log[3],
                            color=0x2F3136,
                        )
                        if db_log[4] is not None:
                            embed.set_image(db_log[4])
                        await m.channel.send(embed=embed)
                    else:
                        await m.channel.send("`#log <id>`")
                        return

        if msg.startswith("!"):
            log_content = f"{m.author} отправил боту команду: {m.content[1:]}\nКанал: <#{m.channel.id}>"
            await Logging(self.bot, self.con).write_log(4, log_content)

    @commands.Cog.listener()
    async def on_message_delete(self, m):
        created_at = m.created_at.strftime("%d-%m-%Y %H:%M:%S")

        log_content = f'{m.author} удалил сообщение.\n[{created_at}] "{m.content}"\nКанал: <#{m.channel.id}>'

        await Logging(self.bot, self.con).write_log(1, log_content)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        created_at = after.created_at.strftime("%d-%m-%Y %H:%M:%S")
        edited_at = after.edited_at.strftime("%d-%m-%Y %H:%M:%S")

        log_content = f'{after.author} отредактировал сообщение.\n[{created_at}] "{before.content}"\n[{edited_at}] "{after.content}"\nКанал: <#{after.channel.id}>'

        await Logging(self.bot, self.con).write_log(1, log_content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        created_at = message.created_at.strftime("%d-%m-%Y %H:%M:%S")

        log_content = f'{payload.member} оставил реакцию {payload.emoji} под сообщением от {message.author}.\n[{created_at}] "{message.content}"\nКанал: <#{message.channel.id}>'

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        created_at = message.created_at.strftime("%d-%m-%Y %H:%M:%S")

        log_content = f'{payload.member} убрал реакцию {payload.emoji} под сообщением от {message.author}.\n[{created_at}] "{message.content}"\nКанал: <#{message.channel.id}>'

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        log_content = f"Реакции были очищены под [сообщением](http://discord.com/channels/{channel.guild.id}/{channel.id}/{message.id}) в канале <#{channel.id}>"

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_content = (
            f"Участник {member.mention} ({member}) присоединился к Discord серверу."
        )

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_content = f"Участник {member.mention} ({member}) покинул Discord сервер."

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_member_ban(self, _, member):
        log_content = f"Участник {member.mention} ({member}) был заблокирован."

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_member_unban(self, _, member):
        log_content = f"Участник {member.mention} ({member}) был разблокирован."

        await Logging(self.bot, self.con).write_log(2, log_content)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        log_content = f"Участник {invite.inviter.mention} ({invite.inviter}) создал приглашение на сервер - {invite.url}."

        await Logging(self.bot, self.con).write_log(2, log_content)


def setup(bot):
    bot.add_cog(LoggingCog(bot))
