from flask import Flask, render_template, jsonify, request
import time
import threading
import json
from datetime import datetime
import os
import time as time_module

app = Flask(__name__)


if not os.path.exists("bin_queue.json"):
    with open("bin_queue.json", "w") as f:
        json.dump({str(i): [] for i in range(4)}, f)


class SimulatedBinManager:
    def __init__(self):
        self.buzzer_on = False
        self.relay_on = False
        self.time_queue = {str(i): {"time": 0, "wait_state": False} for i in range(4)}
        self.waiting_time = 600  # 10 minutes in seconds

    def update_state(self):
        while True:
            with open("data.json") as f:
                bins = json.load(f)

            any_on = False
            for i in range(4):
                if self.time_queue[str(i)]["wait_state"]:
                    if self.time_queue[str(i)]["time"] > 0:
                        self.time_queue[str(i)]["time"] -= 1
                        any_on = True
                    else:
                        self.time_queue[str(i)]["wait_state"] = False
                        # Turn off the bin when timer expires
                        bins[i]["clicked"] = True
                        with open("data.json", "w") as f:
                            json.dump(bins, f)

                        # Check if there are pending colors in queue
                        with open("bin_queue.json", "r") as f:
                            queue = json.load(f)

                        if queue[str(i)]:
                            bins[i]["color"] = queue[str(i)].pop(0)
                            bins[i]["clicked"] = False
                            self.time_queue[str(i)] = {
                                "time": self.waiting_time,
                                "wait_state": True,
                            }
                            any_on = True

                            with open("bin_queue.json", "w") as f:
                                json.dump(queue, f)
                            with open("data.json", "w") as f:
                                json.dump(bins, f)

            # Update buzzer and relay status
            self.buzzer_on = any_on
            self.relay_on = any_on

            time_module.sleep(1)

    def check_schedules(self):
        while True:
            current_time = datetime.now().strftime("%H:%M")

            with open("data.json", "r") as f:
                bins = json.load(f)
            with open("bin_queue.json", "r") as f:
                queue = json.load(f)

            updated = False

            for i, bin in enumerate(bins):
                for sched in bin["schedules"]:
                    if sched["enabled"] and sched["time"] == current_time:
                        # If bin is inactive (clicked=True), activate immediately
                        if bin["clicked"]:
                            bins[i]["color"] = sched["color"]
                            bins[i]["clicked"] = False
                            self.time_queue[str(i)] = {
                                "time": self.waiting_time,
                                "wait_state": True,
                            }
                            updated = True
                        else:
                            # Only add to queue if bin is already active (clicked=False)
                            queue[str(i)].append(sched["color"])
                            updated = True

            if updated:
                with open("bin_queue.json", "w") as f:
                    json.dump(queue, f)
                with open("data.json", "w") as f:
                    json.dump(bins, f)

            time_module.sleep(60)  # Check every minute


manager = SimulatedBinManager()
threading.Thread(target=manager.update_state, daemon=True).start()
threading.Thread(target=manager.check_schedules, daemon=True).start()


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/toggle_bin/<int:bin_id>")
def toggle_bin(bin_id):
    with open("data.json", "r") as f:
        bins = json.load(f)

    # Only allow turning off (set clicked to True)
    if not bins[bin_id]["clicked"]:
        bins[bin_id]["clicked"] = True
        # Clear the timer
        manager.time_queue[str(bin_id)] = {"time": 0, "wait_state": False}

        # Check if there are pending colors in queue
        with open("bin_queue.json", "r") as f:
            queue = json.load(f)

        if queue[str(bin_id)]:
            bins[bin_id]["color"] = queue[str(bin_id)].pop(0)
            bins[bin_id]["clicked"] = False
            manager.time_queue[str(bin_id)] = {
                "time": manager.waiting_time,
                "wait_state": True,
            }

            with open("bin_queue.json", "w") as f:
                json.dump(queue, f)

    with open("data.json", "w") as f:
        json.dump(bins, f)

    return jsonify(success=True)


@app.route("/get_status")
def get_status():
    with open("data.json") as f:
        bins = json.load(f)
    with open("bin_queue.json") as f:
        queue = json.load(f)

    # Calculate remaining time for each bin
    remaining_times = {}
    for i in range(4):
        remaining_times[str(i)] = manager.time_queue[str(i)]["time"]

    # Count how many bins are currently on
    active_bins = sum(1 for i in range(4) if not bins[i]["clicked"])

    # Update buzzer and relay status based on active bins
    manager.buzzer_on = active_bins > 0
    manager.relay_on = active_bins > 0

    return jsonify(
        {
            "bins": bins,
            "queue": queue,
            "buzzer": manager.buzzer_on,
            "relay": manager.relay_on,
            "time": datetime.now().strftime("%H:%M:%S"),
            "remaining_times": remaining_times,
        }
    )


@app.route("/update_schedule", methods=["POST"])
def update_schedule():
    data = request.json
    bin_id = data["bin_id"]
    schedule_index = data["schedule_index"]
    enabled = data["enabled"]

    with open("data.json", "r") as f:
        bins = json.load(f)

    bins[bin_id]["schedules"][schedule_index]["enabled"] = enabled

    with open("data.json", "w") as f:
        json.dump(bins, f)

    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)
