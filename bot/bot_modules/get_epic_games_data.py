import discord
import random
import json
import requests
from datetime import datetime, timedelta


def fetch_data_epic() -> list:
    """ Extract wanted data from Epic Games Store

    :param soup: BeautifulSoup; The fetched html data
    :return: list; List of tuples where each tuple contains game-name, end date and image-link
    """

    # Source https://github.com/AuroPick/epic-free-games/blob/main/src/index.ts
    # Data from https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?country=DE

    data = []

    # Fetch data
    r = requests.get("https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?country=DE")

    print("Response " + str(r.status_code))
    if r.status_code == 400:
        return data

    raw_data = r.json()

    # Extract games
    games = raw_data["data"]["Catalog"]["searchStore"]["elements"]

    for game in games:
        if (game["price"]["totalPrice"]["discountPrice"] == 0) and (game["price"]["totalPrice"]["originalPrice"] != 0):

            # Get title
            title = game["title"]

            # Get end date
            end_date_raw = game["price"]["lineOffers"][0]["appliedRules"][0]["endDate"]
            end_date_year = end_date_raw[:4]
            end_date_month = end_date_raw[5:7]
            end_date_day = end_date_raw[8:10]
            end_date = f"{end_date_day}.{end_date_month}.{end_date_year}"

            # Get image
            for images in game["keyImages"]:
                if images["type"] == "OfferImageWide":
                    image = images["url"]
                    break

            data.append([title, end_date, image])

    return data


def save_data_to_json(data: list):
    """ Save loaded data to JSON file

    :param data: List; Data from the twitch website
    :return: None
    """
    # Get timestamp
    timestamp = str(datetime.now())

    # Create dictionary
    data_dict = {
        "timestamp": timestamp,
        "data": data
    }

    # Write dictonary to JSON file
    with open("ressources/latest_fetch_epic_games.json", "w", encoding="utf-8") as file:
        json.dump(data_dict, file)


def load_data_from_json() -> dict:
    """ Load data from saved JSON file

    :return: dict
    """
    # Read JSON file to dictionary
    with open("ressources/latest_fetch_epic_games.json", encoding="utf-8") as file:
        data_dict = json.load(file)

    return data_dict


def fetch_data() -> dict:
    """ A wrapper for the functions to fetch, extract and save ressources from the website

    :return: dict
    """
    data = fetch_data_epic()

    if len(data) > 0:
        # Save
        save_data_to_json(data=data)

    # Create and return dict
    data_json = {
        "timestamp": str(datetime.now()),
        "data": data
    }

    return data_json


async def send_message_multiple(message, data):
    """ Send each free game loot as an individual message to the chat

    :param message: message
    :param data: list; List of tuples where each tuple contains game-name, image-link and weblink
    :return: None
    """
    for entry in data:
        current_title = entry[0]
        current_end_date = entry[1]
        current_image = entry[2]

        # Create embed
        embed_class = discord.Embed(
            title="Now free on Epic Games",
            url="https://store.epicgames.com/free-games"
            # color=0x00ff00
        )

        # Set thumbnail
        embed_class.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Epic_Games_logo.png/527px-Epic_Games_logo.png?20180404191303"
        )

        # Inline filed
        embed_class.add_field(name=current_title, value=f"Free until {current_end_date}", inline=False)

        # Add image to footer
        embed_class.set_image(url=current_image)

        # Footer
        # embed_class.set_footer(text="via Twitch Prime Loot Discord Bot")

        # Send message
        await message.channel.send(embed=embed_class)

    return


async def send_message_single(message, data):
    """ Send all free game loot inside a single message to the chat

    :param message: message
    :param data: list; List of tuples where each tuple contains game-name, image-link and weblink
    :return: None
    """
    # Create embed
    embed_class = discord.Embed(
        title="Now free on Epic Games",
        url="https://store.epicgames.com/free-games"
        # color=0x00f1f1
    )

    # Set thumbnail
    embed_class.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Epic_Games_logo.png/527px-Epic_Games_logo.png?20180404191303"
    )

    images = []

    # Add each game as a field to the embed
    for entry in data:
        current_title = entry[0]
        current_end_date = entry[1]
        current_image = entry[2]
        images.append(current_image)

        # Inline filed
        embed_class.add_field(name=f"**{current_title}**", value=f"Free until {current_end_date}", inline=False)

    # Set a random image of all possible images into the footer
    if len(images) > 0:
        random_img = random.randrange(0, len(images) - 1)
        embed_class.set_image(url=images[random_img])
        # embed_class.set_footer(text="via Twitch Prime Loot Discord Bot")

        # Send message
        await message.channel.send(embed=embed_class)

    return


async def handle_cmd(message: discord.Message, message_type: int, fetch: bool):
    """ Main function to handle loading of ressources and sending it to the discord chat

    :param message: discord.Message; The original message with the command
    :param message_type: int; Defines what kind of response message to send
    :param fetch: bool; If true, try to fetch ressources from website. If false use the cached CSV file.
    :return: None
    """

    # Check if fetch true:
    # -> Fetch ressources
    # Else
    # -> Load previously fetched data from JSON file
    # -> Check if json empty OR timestamp to old
    #    -> Fetch ressources
    #    -> Save ressources
    #
    # Check if loaded ressources is empty
    # -> Send sorry message
    # else
    # -> Send messages

    print("Loading epic games store data")

    # Check if fetch. If true fetch
    if fetch:
        msg = await message.channel.send("Let me check what's new. This might take a few seconds.")
        data_json = fetch_data()
        await msg.delete()

    else:
        # Load ressources from JSON
        data_json = load_data_from_json()

        if len(data_json["data"]) == 0:
            msg = await message.channel.send("Let me check what's new. This might take a few seconds.")
            data_json = fetch_data()
            await msg.delete()

        else:
            # Get timestamps
            timestamp_now = datetime.now()
            timestamp_last_str = data_json["timestamp"]
            timestamp_last = datetime.strptime(timestamp_last_str, '%Y-%m-%d %H:%M:%S.%f')

            if (timestamp_now - timestamp_last) >= timedelta(days=1):
                msg = await message.channel.send("Let me check what's new. This might take a few seconds.")
                data_json = fetch_data()
                await msg.delete()

    # Check if ressources empty
    if len(data_json["data"]) == 0:
        print("No data found")
        await message.channel.send("Could not find any content. Please try again later")
        return

    # Send message
    print("Data found. Sending message to discord.")
    if message_type == 0:
        await send_message_single(message=message, data=data_json["data"])
    elif message_type == 1:
        await send_message_multiple(message=message, data=data_json["data"])

    return
