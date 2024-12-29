import network
import time
import urequests

from machine import Pin, Timer

runtime_error = False

HELD_MS = 1000
SPAM_MS = 5000

SSID = ''
SSID_PASSWORD = ''

JELLYFIN_LXC = 112
JELLYFIN_LED_GPIO = 14
JELLYFIN_BTN_GPIO = 15

PROXMOX_URL = ""
PROXMOX_AUTH = ""

LXC_ID_TO_LED = {
        JELLYFIN_LXC: JELLYFIN_LED_GPIO
    }

def connect_wireless():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    #Remove Sleep wireless shutdown (bad 4 power)
    wlan.config(pm = 0xa11140)
    wlan.connect(SSID, SSID_PASSWORD)

def spam_protection_pass(start_milliseconds):
    if (start_milliseconds == None or time.ticks_diff(time.ticks_ms(), start_milliseconds) > SPAM_MS):
        return True
    return False

def held_pass(held_milliseconds):
    if (held_milliseconds == None or time.ticks_diff(time.ticks_ms(), held_milliseconds) < HELD_MS):
        return False
    return True

def listen_for_button(gpio_port, press_func, hold_func):
    btn = Pin(gpio_port, Pin.IN, Pin.PULL_DOWN)
    
    start_milliseconds = None
    held_milliseconds = None
    btn_pressed = False
    while not runtime_error:
        #Button Released
        if(btn_pressed == True and btn.value() == 0):
            btn_pressed = False       
            if(held_pass(held_milliseconds)):
                hold_func()
            else:
                press_func()
        # Button Pressed
        elif(btn.value() == 1):
            if(spam_protection_pass(start_milliseconds)):
                start_milliseconds = time.ticks_ms()
                held_milliseconds = time.ticks_ms()
                btn_pressed = True

def proxmox_lxc_start(lxc_id):
    r = urequests.post(f"https://{PROXMOX_URL}:8006/api2/json/nodes/proxmox/lxc/{lxc_id}/status/start/", headers = { "Authorization": PROXMOX_AUTH })
    print(r.status_code)
    r.close()  
    
def proxmox_lxc_stop(lxc_id):
    r = urequests.post(f"https://{PROXMOX_URL}:8006/api2/json/nodes/proxmox/lxc/{lxc_id}/status/stop/", headers = { "Authorization": PROXMOX_AUTH })
    print(r.status_code)
    r.close()

def proxmox_all_lxc_status():
    print(f"https://{PROXMOX_URL}:8006/api2/json/nodes/proxmox/lxc/")
    r = urequests.get(f"https://{PROXMOX_URL}:8006/api2/json/nodes/proxmox/lxc/", headers = { "Authorization": PROXMOX_AUTH })
    print(r.status_code)
    return r.json()

def monitor_lxc_status():
    
    for lxc_id in LXC_ID_TO_LED.keys():
        led = Pin(LXC_ID_TO_LED[lxc_id], Pin.OUT)
        led.off()

    def tick(timer):
        print("REFRESH")
        all_status = proxmox_all_lxc_status()["data"]
        
        LXC_ID_TO_LED_KEYS = LXC_ID_TO_LED.keys()
        for lxc_status in all_status:
            if(lxc_status["vmid"] in LXC_ID_TO_LED_KEYS):
                led = Pin(LXC_ID_TO_LED[lxc_status["vmid"]], Pin.OUT)
                lxc_id = lxc_status["vmid"]
                if(lxc_status["status"] == "running"):
                    if(led.value() != 1):
                        led.on()
                else:
                    if(led.value() != 0):
                        led.off()
    tim = Timer()
    tick(tim)
    tim.init(period=30000, mode=Timer.PERIODIC, callback=tick)
    
def blink_led(GPIO):
    led = Pin("LED", Pin.OUT)
    def tick(timer):
        led.toggle()
    tim = Timer()
    tim.init(freq=2, mode=Timer.PERIODIC, callback=tick)

def light_led(GPIO):
    led = Pin(GPIO, Pin.OUT)
    led.on()
    print("ON")

def dim_led(GPIO):
    led = Pin(GPIO, Pin.OUT)
    led.off()
    print("OFF")

def jellyfin_start():
    print("jellyfin_start")
    if(True):
        proxmox_lxc_start(JELLYFIN_LXC)
    light_led(JELLYFIN_LED_GPIO)
    
def jellyfin_shutdown():
    print("jellyfin_shutdown")
    if(True):
        proxmox_lxc_stop(JELLYFIN_LXC)
    dim_led(JELLYFIN_LED_GPIO)

gpio_to_func = {
    JELLYFIN_BTN_GPIO: {
        "press_func": jellyfin_start,
        "hold_func": jellyfin_shutdown,
        "light": JELLYFIN_LED_GPIO
    }
}

blink_led("LED")
dim_led(JELLYFIN_LED_GPIO)

connect_wireless()
print("START")
#TODO Threads
monitor_lxc_status()
listen_for_button(JELLYFIN_BTN_GPIO, gpio_to_func[JELLYFIN_BTN_GPIO]["press_func"], gpio_to_func[JELLYFIN_BTN_GPIO]["hold_func"])