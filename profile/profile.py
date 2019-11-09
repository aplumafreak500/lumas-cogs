import discord
from redbot.core import commands
from redbot.core import Config
import time
import datetime

BaseCog = getattr(commands, "Cog", object)

class Profile(BaseCog):
	def __init__(self, bot):
		self.bot = bot

		self.debug_log_channel = bot.get_channel(582941546488397829)

	@commands.command()
	@commands.guild_only() # Some attributes don't work over DMs
	async def profile(self, ctx, user: discord.Member = None):
		"""Checks server and global profile details"""

		if user == None:
			user = ctx.author

		sent_msg = "**{0}'s profile info:**\n".format(user.display_name)

		# Discord info
		sent_msg += "*Username:* {0}#{1}\n".format(user.name, user.discriminator)
		sent_msg += "*User ID:* {0}\n".format(user.id)
		sent_msg += "*Joined {0}:* {1}\n".format(ctx.guild.name, user.joined_at.strftime("%B %d, %Y %I:%M:%S %p %Z"))
		sent_msg += "*Joined Discord:* {0}\n".format(user.created_at.strftime("%B %d, %Y %I:%M:%S %p %Z"))
		if user.premium_since == None:
			boost = "N/A"
		else:
			boost = user.premium_since.strftime("%B %d, %Y %I:%M:%S %p %Z")
		sent_msg += "*Boosting Since:* {0}\n".format(boost)
		if user.status == discord.Status.online:
			status = "Online"
		elif user.status == discord.Status.idle:
			status = "Idle"
		elif user.status == discord.Status.dnd:
			status = "Do Not Disturb"
		elif user.status == discord.Status.offline:
			status = "Offline"
		else:
			status = "Unknown"
		sent_msg += "*Status:* {0}\n".format(status)
		if len(user.activities) == 0:
			activity = None
		# HACK: can discord.user.activities contain multiple elements?
		elif user.activities[0].type == discord.ActivityType.playing:
			activity = "playing"
		elif user.activities[0].type == discord.ActivityType.streaming:
			activity = "streaming"
		elif user.activities[0].type == discord.ActivityType.listening:
			activity = "listening to"
		elif user.activities[0].type == discord.ActivityType.watching:
			activity = "watching"
		else:
			activity = None
		if activity != None and (user.activities[0].name == None or user.activities[0].name == ""):
			sent_msg += "*Currently {0}* {1}\n".format(activity, user.activities[0].name)
		# discord.py allows for retrieving mobile/desktop/web status, we don't do that yet
		roles = ""
		if len(user.roles) != 1:
			for i in range(min(5, len(user.roles)-1)):
				roles += user.roles[i+1].name
				if i+1 < min(5, len(user.roles)-1):
					roles += ", "
			sent_msg += "*Top {1} Roles:* {0}\n".format(roles, min(5, len(user.roles)-1))

		# Birthday info
		# bday_cog = self.bot.get_cog("Birthday")
		#if bday_cog != None:
			# Stuff

		# FC info
		#fc_cog = self.bot.get_cog("Friendcodes")

		# Couples
		couples_cog = self.bot.get_cog("Couples")
		if couples_cog != None:
			try:
				data = await couples_cog.profile_get_spouse(user)
				await self.debug_log_channel.send("`profile` DEBUG LOG\n```{}```".format(data))
				if data.get("profile_data") == True and data.get("type") == "couples":
					payload = data.get("data")
					spouse_id = payload.get("spouse")
					if spouse_id != 0 or payload.get("divorced") != 0:
						spouse_user = discord.utils.get(self.bot.get_all_members(), id = spouse_id)
						if spouse_user == None:
							spouse_str = "<{}>".format(spouse_id) # don't explicitly mention if the spouse is present in the data but is not found in Discord's API
						else:
							spouse_str=spouse_user.display_name
						sent_msg += "*Spouse*: {}\n".format(spouse_str)
						sent_msg += "*Couple Karma*: {}\n".format(payload.get("karma"))
						sent_msg += "*Married Since*: {}\n".format(time.strftime("%B %d, %Y %I:%M:%S %p %Z", time.gmtime(payload.get("married_since"))))
			except AttributeError:
				# Different (or old) version of Couples cog is loaded
				pass

		# Boop
		# boop_cog = self.bot.get_cog("Boop")

		await ctx.send(sent_msg)
