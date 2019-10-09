from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import discord
import random
import calendar
import time
import asyncio

BaseCog = getattr(commands, "Cog", object)

class Couples(BaseCog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=69696969)

		self.conf.register_global(couples = [], pending_kisses = [], pending_proposals = [], pending_divorces = [])
		self.conf.register_guild(kiss_messages = [], hug_messages = [], propose_messages = [], divorce_messages = [])

		# TODO: Per-guild settings (and possibly exchange settings across servers?)
		# TODO: Set spouse in per-user/per-member contexts instead of using a couple list?

		self.debug_log_channel = bot.get_channel(582941546488397829)

	@commands.command()
	@commands.guild_only() # todo: once implemented in DMs, remove this
	async def hug(self, ctx, member: discord.Member = None):
		"""Hugs a server member."""
		if member is None:
			return
		if member.id == ctx.author.id:
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
	@commands.guild_only()
	async def hugmsg(self, ctx):
		"""Gets or sets personalized messages for the `hug` command."""
		pass

	@hugmsg.command(name = "add")
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
	async def hugmsg_add(self, ctx, *, msg: str):
		"""Adds a hug message"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("hug_messages")
		except KeyError:
			messages = []
		for i in messages:
			if i == msg:
				await ctx.send("This hug message already exists!")
				return
		messages.append(msg)
		await self.conf.guild(ctx.guild).set_raw("hug_messages", value = messages)
		await ctx.message.add_reaction("\u2705")

	@hugmsg.command(name = "del", aliases = ["rem", "remove", "delete"])
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
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
			if i == msg:
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
		# Spouse check
		spouse = None
		divorced = 0
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`kiss` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == ctx.author.id:
				divorced = i.get("divorced")
				if divorced == 0:
					spouse = i.get("user2")
				else:
					# sanitize divorced value
					i.update(divorced = 1)
					divorced = 1
					await self.conf.set_raw("couples", value = couples)
			if i.get("user2") == ctx.author.id:
				divorced = i.get("divorced")
				if divorced == 0:
					spouse = i.get("user1")
				else:
					# sanitize divorced value
					i.update(divorced = 1)
					divorced = 1
					await self.conf.set_raw("couples", value = couples)
		if user is not None and spouse is not None and (user.id != spouse and divorced == 0):
			await self.debug_log_channel.send("`kiss` DEBUG LOG\n```user is not None and spouse is not None and (user.id != spouse and divorced == 0)```")
			return
		if spouse is not None and divorced == 0:
			user = discord.utils.get(self.bot.get_all_members(), id = spouse)
		if user is None or user.id == ctx.message.author.id:
			return
		# Check "pending" status
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		pending = await self.conf.get_raw("pending_kisses")
		for i in pending:
			await self.debug_log_channel.send("`kiss` DEBUG LOG\n``` Pending Time: {} User1: {} User2: {}```".format(i.get("time"), i.get("user1"), i.get("user2")))
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
		await ctx.send("{0}, you have been offered a kiss from {1}.\nDo you `{2}accept` or `{2}refuse`?".format(user.mention, ctx.author.display_name, ctx.prefix))
		# Set "pending" status
		pending.append({"user1": ctx.author.id, "user2": user.id, "time": senttime})
		await self.conf.set_raw("pending_kisses", value = pending)
		def check(msg):
			return msg.channel == ctx.channel and (msg.author.id == ctx.author.id and msg.content == "{0}cancel".format(ctx.prefix)) or (msg.author.id == user.id and (msg.content == "{0}accept".format(ctx.prefix) or msg.content == "{0}refuse".format(ctx.prefix)))
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
			if message.author.id == ctx.author.id and message.content == "{0}cancel".format(ctx.prefix):
				await ctx.send("{0} canceled their request.".format(ctx.author.display_name))
				return
			elif message.author.id == user.id and message.content == "{0}accept".format(ctx.prefix):
				try:
					messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages") # todo: allow smooch buddies in DMs :8StarcoKiss:
				except KeyError:
					messages = ["{0} and {1} share a kiss \u2665"]
				if messages == []:
					messages = ["{0} and {1} share a kiss \u2665"]
				sentmsg = random.choice(messages)
				try:
					await ctx.send("*{0}*".format(sentmsg.format(ctx.author.display_name, user.display_name)))
				except IndexError:
					await ctx.send("**__Warning:__ Message `{0}` has an invalid format!**".format(sentmsg))
					await ctx.send("*{0} and {1} share a kiss \u2665*".format(ctx.author.display_name, user.display_name))
				if spouse is not None and divorced == 0:
					for i in couples:
						if (i.get("user1") == spouse and i.get("user2") == ctx.author.id) or (i.get("user1") == ctx.author.id and i.get("user2") == spouse):
							karma = int(i.get("karma")) + 15
							i.update(karma = karma)
							await self.conf.set_raw("couples", value = couples)
							await ctx.send("\U0001f497: +15 ({0})".format(karma))
							return
			elif message.author.id == user.id and message.content == "{0}refuse".format(ctx.prefix):
				await ctx.send("{0} doesn't want a kiss right now.".format(user.display_name))
				return

	@commands.group()
	@commands.guild_only()
	async def kissmsg(self, ctx):
		"""Gets or sets personalized messages for the `kiss` command."""
		pass

	@kissmsg.command(name = "add")
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
	async def kissmsg_add(self, ctx, *, msg: str):
		"""Adds a kiss message."""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("kiss_messages")
		except KeyError:
			messages = []
		for i in messages:
			if i == msg:
				await ctx.send("This kiss message already exists!")
				return
		messages.append(msg)
		await self.conf.guild(ctx.guild).set_raw("kiss_messages", value = messages)
		await ctx.message.add_reaction("\u2705")

	@kissmsg.command(name = "del", aliases = ["rem", "remove", "delete"])
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
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
		print(messages)
		for i in messages:
			print(i)
			if i == msg:
				messages.remove(msg)
				await self.conf.guild(ctx.guild).set_raw("kiss_messages", value = messages)
				await ctx.message.add_reaction("\u2705")
				return
		await ctx.send("That kiss message was not found.")

	@kissmsg.command(name = "list", aliases = ["get"])
	@commands.guild_only()
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

	@commands.command(aliases = ["marry"])
	@commands.guild_only()
	async def propose(self, ctx, user: discord.Member):
		"""Requests a server member's hand in marriage."""
		if user.id == ctx.message.author.id:
			return
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`propose` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == ctx.author.id or i.get("user2") == ctx.author.id:
				if i.get("divorced") == 0:
					await ctx.send("You're already married!")
					return
				else:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
			if i.get("user1") == user.id or i.get("user2") == user.id:
				if i.get("divorced") == 0:
					await ctx.send("That user is already married!")
					return
				else:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
		# Check "pending" status
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		pending = await self.conf.get_raw("pending_proposals")
		for i in pending:
			await self.debug_log_channel.send("`propose` DEBUG LOG\n``` Pending Time: {} User1: {} User2: {}```".format(i.get("time"), i.get("user1"), i.get("user2")))
			# Clear proposals "pending" since 30s in case of a bot crash/shutdown during an active kiss, regardless if either party was involved
			que_time = int(i.get("time"))
			if (senttime - que_time) > 30:
				pending.remove(i)
				await self.conf.set_raw("pending_proposals", value = pending)
			if i.get("user1") == ctx.author.id:
				await ctx.send("You already have a pending proposal!")
				return
			elif i.get("user2") == user.id:
				await ctx.send("That user already has a pending proposal!")
				return
		await ctx.send("{0}, you have been offered {1}'s hand in marriage.\nDo you `{2}accept` or `{2}refuse`?".format(user.display_name, ctx.author.display_name, ctx.prefix))
		# Set "pending" status
		pending.append({"user1": ctx.author.id, "user2": user.id, "time": senttime})
		await self.conf.set_raw("pending_proposals", value = pending)
		def check(msg):
			return msg.channel == ctx.channel and (msg.author.id == ctx.author.id and msg.content == "{0}cancel".format(ctx.prefix)) or (msg.author.id == user.id and (msg.content == "{0}accept".format(ctx.prefix) or msg.content == "{0}refuse".format(ctx.prefix)))
		try:
			message = await ctx.bot.wait_for("message", check=check, timeout=30)
		except asyncio.TimeoutError:
			# Clear pending status
			for i in pending:
				if i.get("user1") == ctx.author.id:
					pending.remove(i)
					await self.conf.set_raw("pending_proposals", value = pending)
			await ctx.send("{0} didn't respond in time.".format(user.display_name))
			return
		else:
			for i in pending:
					if i.get("user1") == ctx.author.id:
						pending.remove(i)
						await self.conf.set_raw("pending_proposals", value = pending)
			if message.author.id == ctx.author.id and message.content == "{0}cancel".format(ctx.prefix):
				await ctx.send("{0} canceled their request.".format(ctx.author.display_name))
				return
			elif message.author.id == user.id and message.content == "{0}accept".format(ctx.prefix):
				try:
					messages = await self.conf.guild(ctx.guild).get_raw("proposal_messages")
				except KeyError:
					messages = ["{0} and {1} are now married. \u2665"]
				if messages == []:
					messages = ["{0} and {1} are now married. \u2665"]
				if couples == []: # edge case for first couple
					couples.append({"user1": ctx.author.id, "user2": user.id, "karma": 0, "divorced": 0, "married_since": 0, "divorced_since": 0, "first_married": 0})
					await self.conf.set_raw("couples", value = couples)
				for i in couples:
					if not ((i.get("user1") == ctx.author.id and i.get("user2") == user.id) or (i.get("user1") == user.id and i.get("user2") == ctx.author.id)):
						couples.append({"user1": ctx.author.id, "user2": user.id, "karma": 0, "divorced": 0, "married_since": 0, "divorced_since": 0, "first_married": 0})
						await self.conf.set_raw("couples", value = couples)
				for i in couples:
					if (i.get("user1") == ctx.author.id and i.get("user2") == user.id) or (i.get("user1") == user.id and i.get("user2") == ctx.author.id):
						if i.get("first_married") == 0:
							i.update(first_married = senttime)
						i.update(married_since = senttime)
						karma = int(i.get("karma")) + 100
						i.update(karma = karma)
						i.update(divorced_since = 0)
						i.update(divorced = 0)
						await self.conf.set_raw("couples", value = couples)
				await self.conf.set_raw("couples", value = couples)
				sentmsg = random.choice(messages)
				try:
					await ctx.send("*{0}*".format(sentmsg.format(ctx.author.display_name, user.display_name)))
				except IndexError:
					await ctx.send("**__Warning:__ Message `{0}` has an invalid format!**".format(sentmsg))
					await ctx.send("*{0} and {1} are now married. \u2665*".format(ctx.author.display_name, user.display_name))
				await ctx.send("\U0001f497: +100 ({0})".format(karma))
				return
			elif message.author.id == user.id and message.content == "{0}refuse".format(ctx.prefix):
				await ctx.send("{0} turned down your proposal.".format(user.display_name))
				return

	@commands.command(aliases = ["adminmarry"])
	@checks.is_owner()
	@commands.guild_only()
	async def adminpropose(self, ctx, user1: discord.Member, user2: discord.Member):
		"""Marries two server members manually."""
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`adminpropose` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == user1.id or i.get("user2") == user1.id:
				if i.get("divorced") == 0:
					await ctx.send("{0} is already married.".format(user1.display_name))
					return
				else:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
			if i.get("user1") == user2.id or i.get("user2") == user2.id:
				if i.get("divorced") == 0:
					await ctx.send("{0} is already married.".format(user2.display_name))
					return
				else:
					# sanitize divorced value
					i.update(dicorced = 1)
					await self.conf.set_raw("couples", value = couples)
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("proposal_messages")
		except KeyError:
			messages = ["{0} and {1} are now married. \u2665"]
		if messages == []:
			messages = ["{0} and {1} are now married. \u2665"]
		if couples == []: # edge case for first couple
			couples.append({"user1": user1.id, "user2": user2.id, "karma": 0, "divorced": 0, "married_since": 0, "divorced_since": 0, "first_married": 0})
			await self.conf.set_raw("couples", value = couples)
		for i in couples:
			if not ((i.get("user1") == user1.id and i.get("user2") == user2.id) or (i.get("user1") == user2.id and i.get("user2") == user1.id)):
				couples.append({"user1": user1.id, "user2": user2.id, "karma": 0, "divorced": 0, "married_since": 0, "divorced_since": 0, "first_married": 0})
				await self.conf.set_raw("couples", value = couples)
		for i in couples:
			if (i.get("user1") == user1.id and i.get("user2") == user2.id) or (i.get("user1") == user2.id and i.get("user2") == user1.id):
				if i.get("first_married") == 0:
					i.update(first_married = senttime)
				i.update(married_since = senttime)
				karma = int(i.get("karma")) + 100
				i.update(karma = karma)
				i.update(divorced_since = 0)
				i.update(divorced = 0)
				await self.conf.set_raw("couples", value = couples)
		await self.conf.set_raw("couples", value = couples)
		sentmsg = random.choice(messages)
		try:
			await ctx.send("*{0}*".format(sentmsg.format(user1.display_name, user2.display_name)))
		except IndexError:
			await ctx.send("**__Warning:__ Message `{0}` has an invalid format!**".format(sentmsg))
			await ctx.send("*{0} and {1} are now married. \u2665*".format(user1.display_name, user2.display_name))
		await ctx.send("\U0001f497: +100 ({0})".format(karma))

	@commands.group()
	@commands.guild_only()
	async def proposemsg(self, ctx):
		"""Gets or sets personalized messages for the `propose` command."""
		pass

	@proposemsg.command(name = "add")
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
	async def proposemsg_add(self, ctx, *, msg: str):
		"""Adds a propose message."""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("propose_messages")
		except KeyError:
			messages = []
		for i in messages:
			if i == msg:
				await ctx.send("This propose message already exists!")
				return
		messages.append(msg)
		await self.conf.guild(ctx.guild).set_raw("propose_messages", value = messages)
		await ctx.message.add_reaction("\u2705")

	@proposemsg.command(name = "del", aliases = ["rem", "remove", "delete"])
	@checks.has_permissions(manage_guild = True)
	@commands.guild_only()
	async def proposemsg_del(self, ctx, *, msg: str):
		"""Deletes a propose message"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("propose_messages")
		except KeyError:
			await ctx.send("No propose messages exist yet.")
			return
		if messages == []:
			await ctx.send("No propose messages exist yet.")
			return
		for i in messages:
			if messages[i] == msg:
				messages.remove(msg)
				await self.conf.guild(ctx.guild).set_raw("propose_messages", value = messages)
				await ctx.message.add_reaction("\u2705")
				return
		await ctx.send("That propose message was not found.")

	@proposemsg.command(name = "list", aliases = ["get"])
	@commands.guild_only()
	async def proposemsg_list(self, ctx):
		"""Lists all configured propose messages"""
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("propose_messages")
		except KeyError:
			await ctx.send("No propose messages exist yet.")
			return
		if messages == []:
			await ctx.send("No propose messages exist yet.")
			return
		await ctx.send("`{0}`".format("`\n`".join(messages)))

	@commands.command()
	@commands.guild_only()
	async def spouse(self, ctx, user: discord.Member = None):
		if user is None:
			user = ctx.message.author
		spouse = None
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`spouse` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == user.id:
				divorced = i.get("divorced")
				if divorced != 0:
					# sanitize divorced value
					divorced = 1
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
				spouse = i.get("user2")
				karma = i.get("karma")
				married_since = i.get("married_since")
				first_married = i.get("first_married")
				divorced_since = i.get("divorced_since")
			if i.get("user2") == user.id:
				divorced = i.get("divorced")
				if divorced != 0:
					# sanitize divorced value
					divorced = 1
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
				spouse = i.get("user1")
				karma = i.get("karma")
				married_since = i.get("married_since")
				first_married = i.get("first_married")
				divorced_since = i.get("divorced_since")
			if spouse is not None and divorced == 0:
				break # we already have our current spouse, prevents prior spouses from overwriting current ones
		if spouse is None:
			await ctx.send("{0} is not married!".format(user.display_name))
			return
		if divorced_since == 0:
			divorced_str = "N/A"
		else:
			divorced_str = time.strftime("%B %d, %Y %I:%M:%S %p %Z", time.gmtime(divorced_since)) #todo: integrate timezone portion of Birthday cog
		if divorced == 0:
			is_or_was = "is"
		else:
			is_or_was = "was"
		await ctx.send("{0}'s spouse {7} {1}\n\n**Karma**: {2}\n**Is Divorced**: {3}\n**Married Since**: {4}\n**Divorced Since**: {5}\n**First Marraige On**: {6}".format(user.display_name, discord.utils.get(self.bot.get_all_members(), id = spouse).display_name, karma, bool(divorced), time.strftime("%B %d, %Y %I:%M:%S %p %Z", time.gmtime(married_since)), divorced_str, time.strftime("%B %d, %Y %I:%M:%S %p %Z", time.gmtime(first_married)), is_or_was))

	# todo: +couples

	@commands.guild_only()
	@commands.command()
	async def divorce(self, ctx):
		"""Requests a divorce from your spouse."""
		spouse = None
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`divorce` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == ctx.author.id:
				spouse = i.get("user2")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
			if i.get("user2") == ctx.author.id:
				spouse = i.get("user1")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
		if spouse is None:
			await ctx.send("You are not married.")
			return
		user = discord.utils.get(self.bot.get_all_members(), id = spouse)
		# Check "pending" status
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		pending = await self.conf.get_raw("pending_divorces")
		for i in pending:
			# Clear proposals "pending" since 30s in case of a bot crash/shutdown during an active kiss, regardless if either party was involved
			que_time = int(i.get("time"))
			if (senttime - que_time) > 30:
				pending.remove(i)
				await self.conf.set_raw("pending_divorces", value = pending)
			if i.get("user1") == ctx.author.id:
				await ctx.send("You already have a pending divorce!")
				return
			elif i.get("user2") == user.id:
				await ctx.send("That user already has a pending divorce!")
				return
		await ctx.send("{0}, {1} would like a divorce.\nDo you `{2}accept` or `{2}refuse`?".format(user.display_name, ctx.author.display_name, ctx.prefix))
		# Set "pending" status
		pending.append({"user1": ctx.author.id, "user2": user.id, "time": senttime})
		await self.conf.set_raw("pending_divorces", value = pending)
		def check(msg):
			return msg.channel == ctx.channel and (msg.author.id == ctx.author.id and msg.content == "{0}cancel".format(ctx.prefix)) or (msg.author.id == user.id and (msg.content == "{0}accept".format(ctx.prefix) or msg.content == "{0}refuse".format(ctx.prefix)))
		try:
			message = await ctx.bot.wait_for("message", check=check, timeout=30)
		except asyncio.TimeoutError:
			# Clear pending status
			for i in pending:
				if i.get("user1") == ctx.author.id:
					pending.remove(i)
					await self.conf.set_raw("pending_divorces", value = pending)
			await ctx.send("{0} didn't respond in time.".format(user.display_name))
			return
		else:
			for i in pending:
					if i.get("user1") == ctx.author.id:
						pending.remove(i)
						await self.conf.set_raw("pending_divorces", value = pending)
			if message.author.id == ctx.author.id and message.content == "{0}cancel".format(ctx.prefix):
				await ctx.send("{0} canceled their request.".format(ctx.author.display_name))
				return
			elif message.author.id == user.id and message.content == "{0}accept".format(ctx.prefix):
				try:
					messages = await self.conf.guild(ctx.guild).get_raw("divorce_messages")
				except KeyError:
					messages = ["{0} and {1} are now divorced. \U0001F494"]
				if messages == []:
					messages = ["{0} and {1} are now divorced. \U0001F494"]
				for i in couples:
					if (i.get("user1") == ctx.author.id and i.get("user2") == user.id) or (i.get("user1") == user.id and i.get("user2") == ctx.author.id):
						i.update(divorced_since = senttime)
						i.update(divorced = 1)
				await self.conf.set_raw("couples", value = couples)
				sentmsg = random.choice(messages)
				try:
					await ctx.send("*{0}*".format(sentmsg.format(ctx.author.display_name, user.display_name)))
				except IndexError:
					await ctx.send("**__Warning:__ Message `{0}` has an invalid format!**".format(sentmsg))
					await ctx.send("*{0} and {1} are now divorced. \U0001F494*".format(user1.display_name, user2.display_name))
				return
			elif message.author.id == user.id and message.content == "{0}refuse".format(ctx.prefix):
				await ctx.send("{0} doesn't want to divorce yet.".format(user.display_name))
				return

	@checks.is_owner()
	@commands.guild_only()
	@commands.command()
	async def admindivorce(self, ctx, user1: discord.Member):
		"""Divorces two server members manually."""
		senttime = calendar.timegm(ctx.message.created_at.utctimetuple())
		spouse = None
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`admindivorce` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == user1.id:
				spouse = i.get("user2")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
			if i.get("user2") == user1.id:
				spouse = i.get("user1")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
		if user1 is None:
			return
		if spouse is None:
			await ctx.send("{0} is not married.".format(user1.display_name))
			return
		pending = await self.conf.get_raw("pending_divorces")
		for i in pending:
			if i.get("user1") == user1.id or i.get("user2") == user1.id:
				pending.remove(i)
				await self.conf.set_raw("pending_divorces", value = pending)
		user2 = discord.utils.get(self.bot.get_all_members(), id = spouse)
		try:
			messages = await self.conf.guild(ctx.guild).get_raw("divorce_messages")
		except KeyError:
			messages = ["{0} and {1} are now divorced. \U0001F494"]
		if messages == []:
			messages = ["{0} and {1} are now divorced. \U0001F494"]
		for i in couples:
			if (i.get("user1") == user1.id and i.get("user2") == user2.id) or (i.get("user1") == user2.id and i.get("user2") == user1.id):
				i.update(divorced_since = senttime)
				i.update(divorced = 1)
		await self.conf.set_raw("couples", value = couples)
		sentmsg = random.choice(messages)
		try:
			await ctx.send("*{0}*".format(sentmsg.format(user1.display_name, user2.display_name)))
		except IndexError:
			await ctx.send("**__Warning:__ Message `{0}` has an invalid format!**".format(sentmsg))
			await ctx.send("*{0} and {1} are now divorced. \U0001F494*".format(user1.display_name, user2.display_name))

	@checks.is_owner()
	@commands.guild_only()
	@commands.command()
	async def harddivorce(self, ctx, user: discord.Member):
		"""Divorces two server members manually and resets their karma."""
		spouse = None
		couples = await self.conf.get_raw("couples")
		for i in couples:
			await self.debug_log_channel.send("`harddivorce` DEBUG LOG\n``` User1: {} User2: {} Divorced: {}```".format(i.get("user1"), i.get("user2"), i.get("divorced")))
			if i.get("user1") == user.id:
				spouse = i.get("user2")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
			if i.get("user2") == user.id:
				spouse = i.get("user1")
				if i.get("divorced") >= 1:
					# sanitize divorced value
					i.update(divorced = 1)
					await self.conf.set_raw("couples", value = couples)
		if user is None:
			return
		if spouse is None:
			await ctx.send("{0} is not married.".format(user.display_name))
			return
		pending = await self.conf.get_raw("pending_divorces")
		for i in pending:
			if i.get("user1") == user.id or i.get("user2") == user.id:
				pending.remove(i)
				await self.conf.set_raw("pending_divorces", value = pending)
		user2 = discord.utils.get(self.bot.get_all_members(), id = spouse)
		for i in couples:
			if (i.get("user1") == user.id and i.get("user2") == user2.id) or (i.get("user1") == user.id and i.get("user2") == user2.id):
				couples.remove(i)
		await self.conf.set_raw("couples", value = couples)
		await ctx.send("*{0} and {1} are now divorced. Their karma and stats are reset. \U0001F494*".format(user.display_name, user2.display_name))
