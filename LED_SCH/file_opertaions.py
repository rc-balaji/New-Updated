import json

import urequests

bin_queue_file = "/bin_queue.json"


MAX_RETRIES = 3  # Maximum number of retries for failed requests


def get_bin_queue():
    print("Called2")
    try:
        with open("/bin_queue.json", "r") as f:
            bin_queue = json.load(f)
            print(bin_queue)
            return bin_queue
    except Exception:
        # If the file does not exist, initialize an empty queue structure
        bin_queue = {index: [] for index in range(4)}
        set_bin_queue(bin_queue)


def set_bin_queue(queue):
    with open("/bin_queue.json", "w") as f:
        json.dump(queue, f)


def read_config():

    try:
        with open("/config.json", "r") as file:
            config = json.load(file)
            return config
    except OSError:
        return {}


def get_data():

    try:
        with open("/data.json", "r") as file:
            config = json.load(file)
            return config
    except OSError:
        return {}


def set_data(new_data):
    with open("/data.json", "w") as file:
        json.dump(new_data, file)
