from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import discord
import random
import calendar
import asyncio

BaseCog = getattr(commands, "Cog", object)

class Couples(BaseCog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=69696969)

		self.conf.register_global(couples = [], pending_kisses = [])
		self.conf.register_guild(kiss_messages = [], hug_messages = [], propose_messages = [], divorce_messages = [])

	@commands.command()
	@commands.guild_only() # todo: once implemented in DMs, remove this
	async def hug(self, ctx, member: discord.Member = None):
		"""Hugs a server member."""
		if member is None or member == ctx.author:
			await ctx.send("*{0} hugs themself because they're feeling very lonely...*".format(ctx.author.display_name)) # todo: customized hug messages here too?
			return
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("hug_messages") # todo: allow hugging in DMs :8StarcoHug:
		except KeyError:
			messages = ["{0} gives a hug to {1} \u2665"]
		if messages == []:
			messages = ["{0} gives a hug to {1} \u2665"]
		await ctx.send("*{0}*".format(random.choice(messages).format(ctx.author.display_name, member.display_name)))

	@commands.group()
	async def hugmsg(self, ctx):
		"""Gets or sets personalized messages for the `hug` command."""
		pass

	@hugmsg.command(name = "add")
	@checks.has_permissions(manage_guild = True)
	async def hugmsg_add(self, ctx, *, msg: str):
		"""Adds a hug message"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("hug_messages")
		except KeyError:
			messages = []
		for i in messages:
			if messages[i] == msg:
				await ctx.send("This hug message already exists!")
				return
		messages.append(msg)
		await self.conf.guild(ctx.guild).set_raw("hug_messages", value = messages)
		await ctx.message.add_reaction("\u2705")

	@hugmsg.command(name = "del", aliases = ["rem", "remove", "delete"])
	@checks.has_permissions(manage_guild = True)
	async def hugmsg_del(self, ctx, *, msg: str):
		"""Deletes a hug message"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("hug_messages")
		except KeyError:
			await ctx.send("No hug messages exist yet.")
			return
		if messages == []:
			await ctx.send("No hug messages exist yet.")
			return
		for i in messages:
			if messages[i] == msg:
				messages.remove(msg)
				await self.conf.guild(ctx.guild).set_raw("hug_messages", value = messages)
				await ctx.message.add_reaction("\u2705")
				return
		await ctx.send("That hug message was not found.")

	@hugmsg.command(name = "list", aliases = ["get"])
	async def hugmsg_list(self, ctx):
		"""Lists all configured hug messages"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("hug_messages")
		except KeyError:
			await ctx.send("No hug messages exist yet.")
			return
		if messages == []:
			await ctx.send("No hug messages exist yet.")
			return
		await ctx.send("`{0}`".format("`\n`".join(messages)))

	@commands.command()
	@commands.guild_only() # todo: once implemented in DMs, remove this
	async def kiss(self, ctx, user: discord.Member = None):
		"""Offers a kiss to another server member."""
		# Spouse check TODO
		# If spouse found and user is not None, ignore it lol
		if user is None or user == ctx.message.author:
			return
		# Check "pending" status
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		pending = await self.conf.get_raw("pending_kisses")
		for i in pending:
			# Clear kisses "pending" since 30s in case of a bot crash/shutdown during an active kiss, regardless if either party was involved
			que_time = int(i.get("time"))
			if (senttime - que_time) > 30:
				pending.remove(i)
				await self.conf.set_raw("pending_kisses", value = pending)
			if i.get("user1") == ctx.author.id:
				await ctx.send("You already have a pending kiss!")
				return
			elif i.get("user2") == user.id:
				await ctx.send("That user already has a pending kiss!")
				return
		await ctx.send("{0}, you have been offered a kiss from {1}.\nDo you `{2}accept` or `{2}refuse`?".format(user.display_name, ctx.author.display_name, ctx.prefix))
		# Set "pending" status
		pending.append({"user1": ctx.author.id, "user2": user.id, "time": senttime})
		await self.conf.set_raw("pending_kisses", value = pending)
		def check(msg):
			return msg.channel == ctx.channel and (msg.author == ctx.author and msg.content == "{0}cancel".format(ctx.prefix)) or (msg.author == user and (msg.content == "{0}accept".format(ctx.prefix) or msg.content == "{0}refuse".format(ctx.prefix)))
		try:
			message = await ctx.bot.wait_for("message", check=check, timeout=30)
		except asyncio.TimeoutError:
			# Clear pending status. (something Cobalt doesn't do here for some reason)
			for i in pending:
				if i.get("user1") == ctx.author.id:
					pending.remove(i)
					await self.conf.set_raw("pending_kisses", value = pending)
			await ctx.send("{0} didn't respond in time.".format(user.display_name))
			return
		else:
			for i in pending:
					if i.get("user1") == ctx.author.id:
						pending.remove(i)
						await self.conf.set_raw("pending_kisses", value = pending)
			if message.author == ctx.author and message.content == "{0}cancel".format(ctx.prefix):
				await ctx.send("{0} canceled their request.".format(ctx.author.display_name))
				return
			elif message.author == user and message.content == "{0}accept".format(ctx.prefix):
				try:
					messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages") # todo: allow smooch buddies in DMs :8StarcoKiss:
				except KeyError:
					messages = ["{0} and {1} share a kiss \u2665"]
				if messages == []:
					messages = ["{0} and {1} share a kiss \u2665"]
				await ctx.send("*{0}*".format(random.choice(messages).format(ctx.author.display_name, user.display_name)))
				# todo: For couples, adjust "karma" value
				return
			elif message.author == user and message.content == "{0}refuse".format(ctx.prefix):
				await ctx.send("{0} doesn't want a kiss right now.".format(user.display_name))
				return

	@commands.group()
	async def kissmsg(self, ctx):
		"""Gets or sets personalized messages for the `kiss` command."""
		pass

	@kissmsg.command(name = "add")
	@checks.has_permissions(manage_guild = True)
	async def kissmsg_add(self, ctx, *, msg: str):
		"""Adds a kiss message."""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages")
		except KeyError:
			messages = []
		for i in messages:
			if messages[i] == msg:
				await ctx.send("This kiss message already exists!")
				return
		messages.append(msg)
		await self.conf.guild(ctx.guild).set_raw("kiss_messages", value = messages)
		await ctx.message.add_reaction("\u2705")

	@kissmsg.command(name = "del", aliases = ["rem", "remove", "delete"])
	@checks.has_permissions(manage_guild = True)
	async def kissmsg_del(self, ctx, *, msg: str):
		"""Deletes a kiss message"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages")
		except KeyError:
			await ctx.send("No kiss messages exist yet.")
			return
		if messages == []:
			await ctx.send("No kiss messages exist yet.")
			return
		for i in messages:
			if messages[i] == msg:
				messages.remove(msg)
				await self.conf.guild(ctx.guild).set_raw("kiss_messages", value = messages)
				await ctx.message.add_reaction("\u2705")
				return
		await ctx.send("That kiss message was not found.")

	@kissmsg.command(name = "list", aliases = ["get"])
	async def kissmsg_list(self, ctx):
		"""Lists all configured kiss messages"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages")
		except KeyError:
			await ctx.send("No kiss messages exist yet.")
			return
		if messages == []:
			await ctx.send("No kiss messages exist yet.")
			return
		await ctx.send("`{0}`".format("`\n`".join(messages)))
