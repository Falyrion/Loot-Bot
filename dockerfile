FROM --platform=linux/amd64 python:3.10

RUN apt-get -y update
RUN apt-get install -y wget

# Install chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb -y

COPY ./bot .

# Install python packages
RUN pip install bs4
RUN pip install selenium
RUN pip install discord
RUN pip install pyyaml
RUN pip install webdriver-manager

USER root

# Run bot
CMD python discord_bot.py
