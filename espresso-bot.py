# Version 3.0.0
# Shelly API doc: https://shelly-api-docs.shelly.cloud/
# This code is calibrated for a Moccamaster KBG744 AO-B (double brewer with 2 pots).

"""
TODO: Data collection, automatic or semiautomatic calibration
"""
import network
import config
# import os
import urequests
import time
from hue import Hue
from time import sleep
from picozero import pico_led

# Dict representing brewer state
STATE = {"brewing": False, "turnedOff": True, "coffeeDone": False}
MEASURE_INTERVAL = 5 #seconds

WIFI = network.WLAN(network.STA_IF)

def main() -> None:
    connect()
    sensor_url = config.SENSOR_URL
    hue = setupHue()

    while(True):
        power = measure(sensor_url)
        if(power == -1.0):
            # Power is still changing or an exception occured, wait and measure again
            time.sleep(MEASURE_INTERVAL/2)
            continue

        # Heating old coffee
        elif((power > 1.0) and (power <= 300.0) and not STATE["brewing"] and not STATE["coffeeDone"]):
            heatingOldCoffee(hue)

        # Fresh coffee has been made
        elif((power > 1.0) and (power <= 300.0) and STATE["brewing"]):
            freshCoffeeHasBeenMade(hue)

        # Coffee is brewing
        elif(power > 1000.0 and not STATE["brewing"]):
            coffeeIsBrewing(hue)
        
        # Still brewing, make lights blink
        elif(power > 1000.0 and STATE["brewing"]):
            stillBrewing(hue)

        # Coffee maker turned off
        elif(power == 0.0 and not STATE["turnedOff"]):
            coffeeMakerTurnedOff(hue)

        # Idle, don't send messages
        elif(power == 0.0 and STATE["turnedOff"]):
            continue

        time.sleep(MEASURE_INTERVAL)


def measure(sensor_url) -> float:
    tolerance = 40.0
    try:
        response = urequests.get(sensor_url)
    except Exception as e:
        print(e)
        return -1.0
    value1 = float(response.json()['power'])
    if(value1 > 2000.0):
        tolerance = 80
    print(value1,"Watt")
    time.sleep(MEASURE_INTERVAL)
    try:
        response = urequests.get(sensor_url)
    except Exception as e:
        print(e)
        return -1.0
    value2 = float(response.json()['power'])
    print(value2, "Watt")

    if(value1 == 0.0 and value2 == 0.0): return value2
    elif(abs(value1 - value2) <= tolerance and
        abs(value1 - value2) > 1.0): return value2
    else: return -1.0


def connect():
    #Connect to WLAN
    WIFI.active(True)
    WIFI.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    timeout = 0
    while (not WIFI.isconnected() and timeout < 5):
        print('Waiting for WiFi connection...')
        timeout = timeout + 1
        sleep(1)
    if(not WIFI.isconnected()):
        print('Unable to connect')
        machine.reset()
    print('Connected')
    pico_led.on()

def resetState() -> None:
    STATE["brewing"] = False
    STATE["turnedOff"] = True
    STATE["coffeeDone"] = False

def setupHue() -> Hue:
    hue = Hue()
    hue.getLights()
    return hue

def heatingOldCoffee(hue: Hue) -> None:
    print("Någon räddar svalnande kaffe! :ambulance:")

    if(hue.useHue):
        hue.setAllLights(29000) # green

    STATE["coffeeDone"] = True
    STATE["turnedOff"] = False

def coffeeIsBrewing(hue: Hue) -> None:
    print("Nu bryggs det kaffe! :building_construction:")

    if(hue.useHue):
        hue.setAllLights(10000) # yellow

    STATE["brewing"] = True
    STATE["turnedOff"] = False

def freshCoffeeHasBeenMade(hue: Hue) -> None:
    time.sleep(30) # Wait 30 seconds for coffee to drip down
    print("Det finns kaffe! :coffee: :brown_heart:")

    if(hue.useHue):
        hue.setAllLights(29000) # green

    STATE["coffeeDone"] = True
    STATE["brewing"] = False

def stillBrewing(hue: Hue) -> None:
    if(hue.useHue):
        hue.turnOffAllLights()
        time.sleep(1)
        hue.setAllLights(10000) # yellow

def coffeeMakerTurnedOff(hue: Hue) -> None:
    print("Bryggare avstängd. :broken_heart:")
    resetState()

    if(hue.useHue):
        hue.setAllLights(65000) # red


if(__name__ == "__main__"):
    main()


