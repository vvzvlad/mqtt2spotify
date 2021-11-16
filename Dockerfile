FROM python:3.10.0-slim-bullseye
RUN apt-get update -y && apt-get install git curl wget procps -y
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install paho-mqtt spotipy
RUN mkdir /root/mqtt2spotify && mkdir /root/mqtt2spotify/auth &&
RUN git clone https://github.com/vvzvlad/mqtt2spotify.git /root/mqtt2spotify
WORKDIR /root/mqtt2spotify
CMD [ "python", "/root/mqtt2spotify/mqtt2spotify.py" ]
