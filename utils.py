from const import CONFIG_FILE, SCHEDULE_FILE
import json


def sort_schedules_by_time(schedules):
    """Sort schedules by time in ascending order"""
    return sorted(schedules, key=lambda x: x["time"])


def get_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def get_schedule():
    with open(SCHEDULE_FILE, "r") as f:
        schedule = json.load(f)
        # Ensure we have exactly 4 devices
        while len(schedule) < 4:
            schedule.append(
                {
                    "color": [0, 0, 0],
                    "led_pin": 12 + len(schedule),
                    "button_pin": 13 + len(schedule),
                    "schedules": [],
                    "enabled": True,
                    "clicked": False,
                }
            )
        # Sort schedules for each device
        for device in schedule:
            device["schedules"] = sort_schedules_by_time(device["schedules"])
        return schedule


def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f)


def generate_schedule_entries(schedule, device_id):
    entries = []

    for i, item in enumerate(schedule, start=1):
        # Denormalize color from 0–65 to 0–255
        if isinstance(item["color"], list) and len(item["color"]) == 3:
            r, g, b = item["color"]
            r_denorm = round((r / 65) * 255)
            g_denorm = round((g / 65) * 255)
            b_denorm = round((b / 65) * 255)
            hex_color = "#{:02x}{:02x}{:02x}".format(r_denorm, g_denorm, b_denorm)
        else:
            hex_color = "#FFFFFF"  # fallback to white

        status_text = "Enabled" if item["enabled"] else "Disabled"
        status_class = "status-enabled" if item["enabled"] else "status-disabled"
        toggle_text = "Disable" if item["enabled"] else "Enable"

        entries.append(
            f"""
            <tr>
                <td>{i}</td>
                <td>{item['time']}</td>
                <td style='background-color:{hex_color};width:30px;'></td>
                <td class='{status_class}'>{status_text}</td>
                <td>
                    <a href='/toggle-schedule/{device_id}/{i-1}'>{toggle_text}</a>
                    <a href='/delete-schedule/{device_id}/{i-1}'>Delete</a>
                </td>
            </tr>
            """
        )

    entries.append("</table>")

    return "".join(entries)


def parse_query_string(qs):
    params = {}
    if qs:
        pairs = qs.split("&")
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value
    return params


def urldecode(s):
    s = s.replace("+", " ")
    parts = s.split("%")
    res = [parts[0]]
    for item in parts[1:]:
        if len(item) >= 2:
            res.append(chr(int(item[:2], 16)) + item[2:])
        else:
            res.append("%" + item)
    return "".join(res)
