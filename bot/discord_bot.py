import discord
import yaml

from bot_modules import get_twitch_data


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
        if message.content == CMD_LOOT:
            await get_twitch_data.handle_cmd(message=message, games=ALLOWED_GAMES, message_type=MSG_TYPE, fetch=False)
            return
        elif message.content == CMD_LOOT + " fetch":
            await get_twitch_data.handle_cmd(message=message, games=ALLOWED_GAMES, message_type=MSG_TYPE, fetch=True)
            return


# Load ressources from config
with open("ressources/config.yml", 'r') as file:
    config = yaml.safe_load(file)

TOKEN = config["token"]
CMD_LOOT = config["command_for_content"]
ALLOWED_GAMES = config["games_to_include"]
MSG_TYPE = config["message_type"]

# Run bot
if len(TOKEN) > 1:
    client = TwitchLootBot()
    client.run(TOKEN)
else:
    print("No bot token found. Please set one in the config.yml.")
