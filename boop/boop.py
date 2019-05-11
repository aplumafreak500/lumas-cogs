import discord
from redbot.core import commands
from redbot.core import Config

BaseCog = getattr(commands, "Cog", object)

class Boop(BaseCog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=0xb00b0001)
		self.conf.register_user(boops = 0, booped_by = {})

	@commands.command()
	async def boop(self, ctx, user: discord.Member, *, message: str = None):
		"""Boop a server member"""
		try:
			boops = int(await self.conf.user(ctx.author).get_raw("boops"))
		except KeyError: # We haven't booped anyone yet
			boops = 0
		boops += 1
		await self.conf.user(ctx.author).set_raw("boops", value = boops)
		try:
			booped_by_ = int(await self.conf.user(user).booped_by.get_raw(ctx.author))
		except KeyError:
			booped_by_ = 0
		await self.conf.user(user).booped_by.set_raw(ctx.author, value=booped_by_ + 1)
		sent_msg = "{0} has booped {1}".format(ctx.author.display_name, user.display_name)
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
		try: # TODO: iterate through boop victim list
			boops = await self.conf.user(user).get_raw("booped_by")
			msg = "{0}'s booped victims: \n".format(user.display_name)
			total = 0
			for i in boops:
				times = int(boops.get(i))
				msg += "{0} ({1} times)\n".format(i, times)
				total += times
		except KeyError: # not booped yet
			await ctx.send("This user hasn't been booped yet!")
			return
		await ctx.send("{0}\n\nTotal boops: {1}".format(msg, total))
