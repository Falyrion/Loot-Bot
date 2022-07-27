from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import discord
import random
import json
from datetime import datetime, timedelta


def get_html_data() -> BeautifulSoup:
    """ Fetch html data from prime gaming website

    :return: BeautifulSoup
    """

    # Create browser options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # no UI interface
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Start browser
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # Get html from website
    driver.get("https://gaming.amazon.com/home")
    time.sleep(3)
    source = driver.page_source

    # Close browser
    driver.close()

    # Create soup
    soup = BeautifulSoup(source, 'html.parser')
    return soup


def extract_data_from_html(soup: BeautifulSoup) -> list:
    """ Extract wanted data from BeautifulSoup-Object

    :param soup: BeautifulSoup; The fetched html data
    :return: list; List of tuples where each tuple contains game-name, image-link and weblink
    """

    data = []

    for item_card in soup.find_all("div", attrs={"class": "item-card__action"}):
        # Get item name
        name = item_card.find(
            "a",
            attrs={"class": "tw-interactive tw-block tw-full-width tw-interactable tw-interactable--alpha"})["aria-label"]

        # Get link to item image
        image_link = item_card.find("img", attrs={"class": "tw-image"})["src"]

        # Get weblink
        href = item_card.find(
            "a",
            attrs={"class": "tw-interactive tw-block tw-full-width tw-interactable tw-interactable--alpha"})["href"]
        weblink = "https://gaming.amazon.com" + href

        # TODO: Make sure we got an entry for each list. If not add some empty value.

        data.append((name, image_link, weblink))

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
    with open("ressources/latest_fetch_twitch.json", "w", encoding="utf-8") as file:
        json.dump(data_dict, file)


def load_data_from_json() -> dict:
    """ Load data from saved JSON file

    :return: dict
    """
    # Read JSON file to dictionary
    with open("ressources/latest_fetch_twitch.json", encoding="utf-8") as file:
        data_dict = json.load(file)

    return data_dict


def fetch_data() -> dict:
    """ A wrapper for the functions to fetch, extract and save ressources from the website

    :return: dict
    """
    # Get HTML ressources
    soup = get_html_data()

    # Extract from html
    data = extract_data_from_html(soup=soup)

    # Save new ressources
    save_data_to_json(data=data)

    # Create and return dict
    data_json = {
        "timestamp": str(datetime.now()),
        "data": data
    }

    return data_json


async def send_message_multiple(message, data, games):
    """ Send each free game loot as an individual message to the chat

    :param message: message
    :param data: list; List of tuples where each tuple contains game-name, image-link and weblink
    :param games: list; List of possible games that are wanted to display
    :return: None
    """
    for entry in data:
        current_title = entry[0]

        # Extract game title and check if it is a wanted game
        current_game_title = current_title[:current_title.find(":")]

        if current_game_title in games:
            current_image = entry[1]
            current_link = entry[2]

            # Create embed
            embed_class = discord.Embed(
                title=current_title,
                url=current_link
                # color=0x00ff00
            )

            # Set thumbnail
            embed_class.set_thumbnail(
                url="https://d2u4zldaqlyj2w.cloudfront.net/ba8810e8-f985-43bc-a889-8ba2b0dfea48/favicon.ico"
            )

            # Add inline field with weblink
            embed_class.add_field(name="**Open in browser**", value=current_link, inline=False)
            # Add image to footer
            embed_class.set_image(url=current_image)
            # Footer
            # embed_class.set_footer(text="via Twitch Prime Loot Discord Bot")

            # Send message
            await message.channel.send(embed=embed_class)

    return


async def send_message_single(message, data, games):
    """ Send all free game loot inside a single message to the chat

    :param message: message
    :param data: list; List of tuples where each tuple contains game-name, image-link and weblink
    :param games: list; List of possible games that are wanted to display
    :return: None
    """
    # Create embed
    embed_class = discord.Embed(
        title="Now free on prime gaming",
        url="https://gaming.amazon.com/home"
        # color=0x00f1f1
    )

    # Set thumbnail
    embed_class.set_thumbnail(
        url="https://d2u4zldaqlyj2w.cloudfront.net/ba8810e8-f985-43bc-a889-8ba2b0dfea48/favicon.ico"
    )

    images = []

    # Add each game as a field to the embed
    for entry in data:
        current_title = entry[0]

        # Extract game title and check if it is a wanted game
        current_game_title = current_title[:current_title.find(":")]

        if current_game_title in games:
            current_image = entry[1]
            images.append(current_image)
            current_link = entry[2]

            # Inline filed
            embed_class.add_field(name=f"**{current_title}**", value=current_link, inline=False)

    # Set a random image of all possible images into the footer
    if len(images) > 0:
        random_img = random.randrange(0, len(images) - 1)
        embed_class.set_image(url=images[random_img])
        # embed_class.set_footer(text="via Twitch Prime Loot Discord Bot")

        # Send message
        await message.channel.send(embed=embed_class)

    return


async def handle_cmd(message: discord.Message, games: list, message_type: int, fetch: bool):
    """ Main function to handle loading of ressources and sending it to the discord chat

    :param message: discord.Message; The original message with the command
    :param games: list; List of games to include
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

    print("Loading prime gaming data")

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
        await send_message_single(message=message, data=data_json["data"], games=games)
    elif message_type == 1:
        await send_message_multiple(message=message, data=data_json["data"], games=games)

    return
