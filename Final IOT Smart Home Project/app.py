from flask import Flask, request, render_template, Response
import Adafruit_DHT
import requests
import RPi.GPIO as GPIO
import time
import threading
import json
from flask import redirect, url_for

app = Flask(__name__)

raspberry_ip = '172.20.10.2'  # Địa chỉ IP của Raspberry Pi

# Khai báo GPIO cảm biến SR505
SR505_pin = 19

# Khai báo GPIO cảm biến DHT11
DHT11_pin = 17

# Khai báo các GPIO cho khóa tự động
lock_pin = 18
password = "1234"  # Mật khẩu cần nhập

# Khai báo các GPIO cho đèn
kitchen_light_pin = 23
bedroom_light_pin = 24
bathroom_light_pin = 25
living_room_light_pin = 26

# Khai báo GPIO cho thiết bị
quat_pin = 12
tv_pin = 13

# Khai báo GPIO cho cảm biến hồng ngoại
led_pin = 20
lm393_pin = 27
led_pin_1 = 21

# Thiết lập chế độ chân GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(led_pin_1, GPIO.OUT)
GPIO.setup(lm393_pin, GPIO.IN)

# Thiết lập GPIO cho khóa tự động
GPIO.setup(lock_pin, GPIO.OUT)

# Thiết lập GPIO cho đèn
GPIO.setup(kitchen_light_pin, GPIO.OUT)
GPIO.setup(bedroom_light_pin, GPIO.OUT)
GPIO.setup(bathroom_light_pin, GPIO.OUT)
GPIO.setup(living_room_light_pin, GPIO.OUT)

# Thiết lập GPIO cho thiết bị
GPIO.setup(quat_pin, GPIO.OUT)
GPIO.setup(tv_pin, GPIO.OUT)

# Thiết lập GPIO cho cảm biến
GPIO.setup(SR505_pin, GPIO.IN)

# Thiết lập GPIO cho cảm biến DHT11
DHT11_sensor = Adafruit_DHT.DHT11

def unlock_door():
    GPIO.output(lock_pin, GPIO.HIGH)
    print("Cửa đã mở")


def lock_door():
    GPIO.output(lock_pin, GPIO.LOW)
    print("Cửa đã khóa")


def control_light(pin, state):
    GPIO.output(pin, GPIO.HIGH if state == 'on' else GPIO.LOW)

def control_quat(pin, state):
    GPIO.output(pin, GPIO.HIGH if state == 'on' else GPIO.LOW)

def control_tv(pin, state):
    GPIO.output(pin, GPIO.HIGH if state == 'on' else GPIO.LOW)

def control_led():
    GPIO.output(led_pin, GPIO.HIGH if GPIO.input(lm393_pin) == GPIO.LOW else GPIO.LOW)

def sensor_thread():
    lm393_data = []
    while True:
        control_led()
        lm393_value = GPIO.input(lm393_pin)
        lm393_data.append(lm393_value)
        time.sleep(0.1)

sensor_thread = threading.Thread(target=sensor_thread)
sensor_thread.daemon = True
sensor_thread.start()

def sensor_thread1():
    SR505_data = []
    while True:
        SR505_value = GPIO.input(SR505_pin)
        SR505_data.append(SR505_value)
        time.sleep(0.1)

sensor_thread1 = threading.Thread(target=sensor_thread1)
sensor_thread1.daemon = True
sensor_thread1.start()

def sensor_thread2():
    DHT11_data = []
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT11_sensor, DHT11_pin)
        if humidity is not None and temperature is not None:
            data = {'humidity': humidity, 'temperature': temperature}
            DHT11_data.append(data)
        time.sleep(2)

sensor_thread2 = threading.Thread(target=sensor_thread2)
sensor_thread2.daemon = True
sensor_thread2.start()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/unlock', methods=['POST', 'GET'])
def unlock():
    if request.method == 'POST':
        entered_password = request.form['password']
        if entered_password == password:
            unlock_door()
            requests.get(f'http://{raspberry_ip}/unlock')
            return "MỞ CỬA"
        else:
            return "Mật khẩu không chính xác"
    return render_template('unlock.html')


@app.route('/lock')
def lock():
    lock_door()
    requests.get(f'http://{raspberry_ip}/lock')
    return "KHÓA CỬA"


@app.route('/light', methods=['POST'])
def control_light_route():
    room = request.form['room']
    state = request.form['state']
    pin = None

    if room == 'kitchen':
        pin = kitchen_light_pin
    elif room == 'bedroom':
        pin = bedroom_light_pin
    elif room == 'bathroom':
        pin = bathroom_light_pin
    elif room == 'living_room':
        pin = living_room_light_pin
    elif room == 'car':
        pin = led_pin_1

    if pin is not None:
        control_light(pin, state)

    return 'Đã điều khiển đèn'


@app.route('/all_lights_on')
def all_lights_on():
    control_light(kitchen_light_pin, 'on')
    control_light(bedroom_light_pin, 'on')
    control_light(bathroom_light_pin, 'on')
    control_light(living_room_light_pin, 'on')
    control_light(led_pin_1, 'on')
    return 'Đã bật tất cả đèn'


@app.route('/all_lights_off')
def all_lights_off():
    control_light(kitchen_light_pin, 'off')
    control_light(bedroom_light_pin, 'off')
    control_light(bathroom_light_pin, 'off')
    control_light(living_room_light_pin, 'off')
    control_light(led_pin_1, 'off')
    return 'Đã tắt tất cả đèn'

@app.route('/fan', methods=['POST'])
def control_fan_route():
    state = request.form['state']
    control_quat(quat_pin, state)
    return 'Đã điều khiển quạt'


@app.route('/tv', methods=['POST'])
def control_tv_route():
    state = request.form['state']
    control_quat(tv_pin, state)
    return 'Đã điều khiển tv'

@app.route('/sensor_data')
def sensor_data():
    def generate():
        while True:
            lm393_value = GPIO.input(lm393_pin)
            data = {'label': str(time.time()), 'value': lm393_value}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/sr505_data')
def sr505_data():
    def generate1():
        while True:
            SR505_value = GPIO.input(SR505_pin)
            data1 = {'label': str(time.time()), 'value': SR505_value}
            yield f"data: {json.dumps(data1)}\n\n"
            time.sleep(0.1)

    return Response(generate1(), mimetype='text/event-stream')

@app.route('/dht11_data')
def dht11_data():
    def generate2():
        while True:
            humidity, temperature = Adafruit_DHT.read_retry(DHT11_sensor, DHT11_pin)
            if humidity is not None and temperature is not None:
                data2 = {'label': str(time.time()), 'humidity': humidity, 'temperature': temperature}
                yield f"data: {json.dumps(data2)}\n\n"
            time.sleep(2)

    return Response(generate2(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='172.20.10.2', port=8000)
