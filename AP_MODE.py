
import usocket
import uerrno

import network
import utime
from lib.ds3231 import DS3231

from utils import get_config
from controller import handle_request

rtc = DS3231()


def create_access_point():
    config = get_config()
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    # Get the static IP components from config
    ssid = config.get("SSID", "KT-AP")
    password = config.get("PASSWORD", "1234567890")
    kit_no = config.get("KIT_NO", "1")
    static_no = config.get(
        "STATIC_NO", kit_no
    )  # Fallback to KIT_NO if STATIC_NO not found

    # Configure AP with static IP 192.168.4.{static_no}
    ip = f"192.168.4.{static_no}"
    subnet = "255.255.255.0"
    gateway = "192.168.4.1"
    dns = "8.8.8.8"

    ap.ifconfig((ip, subnet, gateway, dns))
    ap.config(essid=ssid, password=password)

    while not ap.active():
        pass

    print("Access Point created")
    print("SSID:", ssid)
    print("Password:", password)
    print("Network config:", ap.ifconfig())


def run_server(port=80):
    create_access_point()

    # Get our IP address from the AP interface
    ap = network.WLAN(network.AP_IF)
    ip = ap.ifconfig()[0]

    addr = usocket.getaddrinfo(ip, port)[0][-1]
    sock = usocket.socket()
    sock.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(5)
    print(f"Server running on http://{ip}:{port}")

    while True:
        try:
            conn, addr = sock.accept()
            print("Client connected from", addr)
            handle_request(conn)
        except OSError as e:
            if e.args[0] == uerrno.ECONNABORTED:
                continue
            raise
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Server error:", e)
            utime.sleep(1)  # Prevent tight loop on errors

    sock.close()


run_server()
