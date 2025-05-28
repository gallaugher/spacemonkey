# MP3 File Playback with QT Py Audio BFF
# Tested on an Adafruit QT Py ESP32 S2

import os, ssl, socketpool, wifi, time
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import audiocore, board, audiobusio, audiomixer
from audiomp3 import MP3Decoder

# Get Adafruit IO credentials from settings.toml
aio_username = os.getenv('ADAFRUIT_AIO_USERNAME')
aio_key = os.getenv('ADAFRUIT_AIO_KEY')

# Setup feed for dashboard communication
sounds_feed = aio_username + "/feeds/space-monkey-feeds.sounds"

# Audio setup
audio = audiobusio.I2SOut(board.A2, board.A1, board.A0)
filename = "hi.mp3"
path = "/space-monkey-mp3s/"

# Create audio mixer
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
audio.play(mixer)

# Create MP3 decoder
mp3_file = open(path + filename, "rb")
decoder = MP3Decoder(mp3_file)

def play_mp3_voice(filename):
    """Play an MP3 file through the audio mixer"""
    decoder.file = open(path + filename, "rb")
    print(f"Playing {filename}!")
    mixer.voice[0].level = 0.65
    mixer.voice[0].play(decoder)
    while mixer.voice[0].playing:
        pass

def connected(client, userdata, flags, rc):
    """Callback for when MQTT client connects to Adafruit IO"""
    print("Connected to Adafruit IO! Listening for sound commands...")
    client.subscribe(sounds_feed)

def disconnected(client, userdata, rc):
    """Callback for when MQTT client disconnects"""
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    """Handle incoming MQTT messages"""
    print(f"Received: topic: {topic}, message: {message}")
    if topic == sounds_feed and message != "0":
        play_mp3_voice(message)

# Connect to WiFi
print("Connecting to WiFi...")
wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
print("Connected!")

# Create socket pool
pool = socketpool.SocketPool(wifi.radio)

# Setup MQTT client
mqtt_client = MQTT.MQTT(
    broker=os.getenv("BROKER"),
    port=os.getenv("PORT"),
    username=aio_username,
    password=aio_key,
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Setup MQTT callbacks
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
mqtt_client.connect()

# Play startup sound
play_mp3_voice(filename)
print("Space Monkey ready!")

# Main loop
while True:
    try:
        mqtt_client.loop()
    except MQTT.MMQTTException as e:
        print(f"MQTT Error: {e}")
        time.sleep(1)
        try:
            print("Attempting to reconnect...")
            mqtt_client.reconnect()
            print("Reconnected successfully!")
        except Exception as reconnect_error:
            print(f"Reconnection failed: {reconnect_error}")
            time.sleep(5)
    except Exception as general_error:
        print(f"General error: {general_error}")
        time.sleep(1)