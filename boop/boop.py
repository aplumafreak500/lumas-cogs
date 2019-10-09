import discord
from redbot.core import commands
from redbot.core import Config

BaseCog = getattr(commands, "Cog", object)

class Boop(BaseCog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=0xb00b0001)
		self.conf.register_user(boops = 0, booped_by = {})

		# TODO: Per guild boop list

	@commands.command()
	@commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
	@commands.guild_only() # it's verified to work via DMs though
	async def boop(self, ctx, user: discord.Member, *, message: str = None):
		"""Boop a server member"""
		try:
			boops = int(await self.conf.user(ctx.author).get_raw("boops"))
		except KeyError: # We haven't booped anyone yet
			boops = 0
		boops += 1
		await self.conf.user(ctx.author).set_raw("boops", value = boops)
		try:
			booped_by_ = int(await self.conf.user(user).booped_by.get_raw(ctx.author.id))
		except KeyError:
			booped_by_ = 0
		# The old method just used ctx.author, support it for now
		try:
			if booped_by_ == 0:
				booped_by_ = int(await self.conf.user(user).booped_by.get_raw(ctx.author))
		except KeyError:
			booped_by_ = 0
		# Delete the old entry if it's present
		try:
			await self.conf.user(user).booped_by.clear_raw(ctx.author)
		except:
			pass
		await self.conf.user(user).booped_by.set_raw(ctx.author.id, value=booped_by_ + 1)
		sent_msg = "{0} has booped {1}".format(ctx.author.display_name, user.mention)
		if message is not None:
			sent_msg += " with the message: {0}!".format(message)
		else:
			sent_msg += "!"
		sent_msg += "\nThat's {0} times now!".format(booped_by_ + 1)
		await ctx.send(sent_msg)

	@commands.command()
	async def listboops(self, ctx, user: discord.User = None):
		"""List boops"""
		if user is None:
			user = ctx.author
		try:
			boops = await self.conf.user(user).get_raw("booped_by")
			msg = "{0}'s booped victims: \n".format(user.display_name)
			total = 0
			for i in boops:
				try:
					boop_user = discord.utils.get(self.bot.get_all_members(), id = int(i))
				except ValueError: # for str -> int errors
					boop_user = None
				if boop_user == None:
					username = i
				else:
					username = boop_user.display_name
				times = int(boops.get(i))
				msg += "{0} ({1} times)\n".format(username, times)
				total += times
		except KeyError: # not booped yet
			await ctx.send("This user hasn't been booped yet!")
			return
		await ctx.send("{0}\n\nTotal boops: {1}".format(msg, total))
