from .profile import Profile

def setup(bot):
    bot.add_cog(Profile(bot))
