import discord
import yaml

from bot_modules import get_twitch_data, get_epic_games_data


class TwitchLootBot(discord.Client):
    # On ready
    async def on_ready(self):
        print('Bot logged in as {0.user}'.format(client))
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="Type !twitch", state=discord.Status.online
            )
        )
        print("Bot changed online presence")

    # On command
    async def on_message(self, message):
        if message.author == client.user:
            return

        # Handle prime games content command
        if message.content == CMD_TWITCH:
            await get_twitch_data.handle_cmd(message=message, games=ALLOWED_GAMES, message_type=MSG_TYPE_TWITCH,
                                             fetch=False)
            return
        elif message.content == CMD_TWITCH + " fetch":
            await get_twitch_data.handle_cmd(message=message, games=ALLOWED_GAMES, message_type=MSG_TYPE_TWITCH,
                                             fetch=True)
            return

        # Handle epic games content command
        elif message.content == CMD_EPIC:
            await get_epic_games_data.handle_cmd(message=message, message_type=MSG_TYPE_EPIC, fetch=False)
            return
        elif message.content == CMD_EPIC + " fetch":
            await get_epic_games_data.handle_cmd(message=message, message_type=MSG_TYPE_EPIC, fetch=True)
            return


# Load ressources from config
with open("ressources/config.yml", 'r') as file:
    config = yaml.safe_load(file)

TOKEN = config["token"]
CMD_TWITCH = config["twitch"]["command"]
CMD_EPIC = config["epic"]["command"]
ALLOWED_GAMES = config["twitch"]["games_to_include"]
MSG_TYPE_TWITCH = config["twitch"]["message_type"]
MSG_TYPE_EPIC = config["epic"]["message_type"]

# Run bot
if TOKEN != "0":
    client = TwitchLootBot()
    client.run(TOKEN)
else:
    print("No bot token found. Please set one in the config.yml.")
