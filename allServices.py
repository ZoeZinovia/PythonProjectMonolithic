import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import RPi.GPIO as GPIO
import time
import sys
import adafruit_dht
import board

start_total = time.time()

# ------ Variables for all ------ #

MQTT_SERVER = sys.argv[1]
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ------ LED code------ #
start_led = time.time()

MQTT_PATH_LED = "LED"
num_led_messages = 0
PIN_LED = 0  # Will be received in MQTT message

def on_connect(client, userdata, flags, rc):
    print("Connected. Result code: "+ str(rc))
    client.subscribe(MQTT_PATH_LED)


# The on_message function runs once a message is received from the broker
def on_message(client, userdata, msg):
    global num_led_messages
    global start_led
    global PIN_LED
    num_led_messages += 1
    if num_led_messages == 1:
        start_led = time.time()
    received_json = json.loads(msg.payload) #convert the string to json object
    if "Done" in received_json:
        client.loop_stop()
        client.disconnect()
        end_LED = time.time()
        timer = end_LED - start_led
        with open("piResultsPythonMonoLong.txt", "a") as myfile:
            myfile.write("LED subscriber runtime = " + str(timer) + "\n")
        print("LED subscriber runtime = " + str(timer) + "\n");
        GPIO.output(PIN_LED, GPIO.LOW)

    else:
        led_1_status = received_json["LED_1"]
        PIN_LED = received_json["GPIO"]
        GPIO.setup(PIN_LED, GPIO.OUT)
        if led_1_status:
            GPIO.output(PIN_LED, GPIO.HIGH)
        else:
            GPIO.output(PIN_LED, GPIO.LOW)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

# ------ PIR code ------#

start_PIR = time.time()

MQTT_PATH_PIR = "PIR"

# Initial the pir device, with data pin connected to 17:
GPIO.setup(17, GPIO.IN)  # Change setup
presence = False
count = 0
while count < 100000:
    try:
        presence = GPIO.input(17)
        temp_json = {"PIR": presence}
        publish.single(MQTT_PATH_PIR, json.dumps(temp_json), port=1883, hostname=MQTT_SERVER)
    except RuntimeError as error:  # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
    count += 1

publish.single(MQTT_PATH_PIR, json.dumps({"Done": True}), port=1883, hostname=MQTT_SERVER)
end_PIR = time.time()
print("PIR publisher runtime = " + str(end_PIR-start_PIR))
with open("piResultsPythonMonoLong.txt", "a") as myfile:
    myfile.write("PIR publisher runtime = " + str(end_PIR-start_PIR) + "\n")

# ------ Humidity and Temperature code ------#
# Initial the dht device, with data pin connected to:

start_HT = time.time()
dhtDevice = adafruit_dht.DHT11(board.D4)
count = 0
while count < 100000:
    try:
        humidity = dhtDevice.humidity # Get current humidity from dht11
        temperature = dhtDevice.temperature # Get current temperature from dht11
        hum_json = {"Humidity": humidity, "Unit": "%"}
        publish.single("Humidity", json.dumps(hum_json), hostname=MQTT_SERVER)
        temp_json = {"Temp": temperature, "Unit": "C"}
        publish.single("Temperature", json.dumps(temp_json), hostname=MQTT_SERVER)
    except RuntimeError as error:  # Errors happen fairly often, DHT's are hard to read, just keep going
        error.args[0]
    count += 1

publish.single("Humidity", json.dumps({"Done": True}), port=1883, hostname=MQTT_SERVER)
publish.single("Temperature", json.dumps({"Done": True}), port=1883, hostname=MQTT_SERVER)
end_HT = time.time()
print("Humidity and temperature runtime = " + str(end_HT-start_HT))
with open("piResultsPythonMonoLong.txt", "a") as myfile:
    myfile.write("Humidity and temperature publisher runtime = " + str(end_HT-start_HT) + "\n")

end_total = time.time()
with open("piResultsPythonMonoLong.txt", "a") as myfile:
    myfile.write("Overall runtime = " + str(end_total-start_total) + "\n")

client.loop_forever()








