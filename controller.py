from const import (
    DEFAULT_CONFIG,
    COLOR_OPTIONS,
    MAIN_MENU,
    AP_SETUP_TEMPLATE,
    SCHEDULE_SETUP_TEMPLATE,
    TIME_MANAGEMENT_TEMPLATE,
)


import gc
import utime

from utils import (
    sort_schedules_by_time,
    get_config,
    save_config,
    get_schedule,
    save_schedule,
    generate_schedule_entries,
    parse_query_string,
    urldecode,
)

from lib.ds3231 import DS3231

rtc = DS3231()


def handle_request(conn):
    try:
        # Increase buffer size and add timeout
        conn.settimeout(5.0)
        request = conn.recv(4096)  # Increased buffer size
        if not request:
            conn.close()
            return

        try:
            request = request.decode()
        except UnicodeError:
            conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
            conn.close()
            return

        # Improved request parsing
        headers = request.split("\r\n\r\n", 1)[0] if "\r\n\r\n" in request else request
        first_line = headers.split("\r\n")[0] if "\r\n" in headers else headers

        parts = first_line.split()
        if len(parts) < 2:
            conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
            conn.close()
            return

        method = parts[0]
        path = parts[1]

        # Handle GET requests
        if method == "GET":
            if path == "/":
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(MAIN_MENU)

            elif path == "/setup-ap":
                config = get_config()
                response = AP_SETUP_TEMPLATE.format(
                    ssid=config["SSID"],
                    password=config["PASSWORD"],
                    kit_no=config["KIT_NO"],
                    static_no=config["STATIC_NO"],
                )
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(response)

            elif path.startswith("/setup-schedule"):
                try:
                    device_id = 0
                    if path.startswith("/setup-schedule/"):
                        device_id = int(path.split("/")[2])
                        if device_id < 0 or device_id > 3:
                            device_id = 0

                    schedule_data = get_schedule()
                    device_schedule = schedule_data[device_id]["schedules"]

                    # Check if all schedules are enabled
                    all_enabled = (
                        all(item["enabled"] for item in device_schedule)
                        if device_schedule
                        else False
                    )

                    # Generate color options HTML
                    color_options_html = ""
                    for color in COLOR_OPTIONS:
                        hex_color = "#{:02x}{:02x}{:02x}".format(*color["value"])
                        color_options_html += f"""
                        <div class="color-option" 
                             style="background-color: {hex_color}"
                             onclick="selectColor(this, '{color['value'][0]},{color['value'][1]},{color['value'][2]}')"></div>
                        """

                    # Prepare active class for device buttons
                    active_classes = ["", "", "", ""]
                    active_classes[device_id] = "active"

                    response = SCHEDULE_SETUP_TEMPLATE.format(
                        device_id=device_id,
                        active_0=active_classes[0],
                        active_1=active_classes[1],
                        active_2=active_classes[2],
                        active_3=active_classes[3],
                        schedule_entries=generate_schedule_entries(
                            device_schedule, device_id
                        ),
                        toggle_all_text="Disable All" if all_enabled else "Enable All",
                        color_options=color_options_html,
                    )
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                    conn.send(response)
                except Exception as e:
                    print("Error in schedule setup:", e)
                    conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")

            elif path.startswith("/delete-schedule/"):
                try:
                    parts = path.split("/")
                    if len(parts) >= 4:
                        device_id = int(parts[2])
                        index = int(parts[3])
                        schedule_data = get_schedule()
                        if 0 <= device_id < 4 and 0 <= index < len(
                            schedule_data[device_id]["schedules"]
                        ):
                            schedule_data[device_id]["schedules"].pop(index)
                            save_schedule(schedule_data)
                    conn.send(
                        "HTTP/1.1 303 See Other\r\nLocation: /setup-schedule/{}\r\n\r\n".format(
                            device_id
                        )
                    )
                except Exception as e:
                    print("Error deleting schedule:", e)
                    conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path.startswith("/toggle-schedule/"):
                try:
                    parts = path.split("/")
                    if len(parts) >= 4:
                        device_id = int(parts[2])
                        index = int(parts[3])
                        schedule_data = get_schedule()
                        if 0 <= device_id < 4 and 0 <= index < len(
                            schedule_data[device_id]["schedules"]
                        ):
                            schedule_data[device_id]["schedules"][index]["enabled"] = (
                                not schedule_data[device_id]["schedules"][index][
                                    "enabled"
                                ]
                            )
                            save_schedule(schedule_data)
                    conn.send(
                        "HTTP/1.1 303 See Other\r\nLocation: /setup-schedule/{}\r\n\r\n".format(
                            device_id
                        )
                    )
                except Exception as e:
                    print("Error toggling schedule:", e)
                    conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path.startswith("/enable-all/"):
                try:
                    device_id = int(path.split("/")[2])
                    schedule_data = get_schedule()
                    if 0 <= device_id < 4:
                        for item in schedule_data[device_id]["schedules"]:
                            item["enabled"] = True
                        save_schedule(schedule_data)
                    conn.send(
                        "HTTP/1.1 303 See Other\r\nLocation: /setup-schedule/{}\r\n\r\n".format(
                            device_id
                        )
                    )
                except Exception as e:
                    print("Error enabling all schedules:", e)
                    conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path.startswith("/disable-all/"):
                try:
                    device_id = int(path.split("/")[2])
                    schedule_data = get_schedule()
                    if 0 <= device_id < 4:
                        for item in schedule_data[device_id]["schedules"]:
                            item["enabled"] = False
                        save_schedule(schedule_data)
                    conn.send(
                        "HTTP/1.1 303 See Other\r\nLocation: /setup-schedule/{}\r\n\r\n".format(
                            device_id
                        )
                    )
                except Exception as e:
                    print("Error disabling all schedules:", e)
                    conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
            elif path == "/time-management":
                try:
                    # Get current time from RTC
                    current_time = (
                        rtc.get_formatted_date() + " " + rtc.get_formatted_time()
                    )
                    response = TIME_MANAGEMENT_TEMPLATE.format(
                        current_time=current_time
                    )
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                    conn.send(response)
                except Exception as e:
                    print("Error in time management:", e)
                    conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")

            elif path == "/get-current-time":
                try:
                    current_time = (
                        rtc.get_formatted_date() + " " + rtc.get_formatted_time()
                    )
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
                    conn.send(current_time)
                except Exception as e:
                    print("Error getting current time:", e)
                    conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")

            else:
                conn.send("HTTP/1.1 404 Not Found\r\n\r\n<h1>404 Not Found</h1>")

        # Handle POST requests
        elif method == "POST":
            try:
                content_length = 0
                headers_body = request.split("\r\n\r\n", 1)
                headers = headers_body[0]
                body = headers_body[1] if len(headers_body) > 1 else ""

                for line in headers.split("\r\n"):
                    if line.startswith("Content-Length:"):
                        content_length = int(line.split(":")[1].strip())
                        break

                # Read remaining body if needed
                while len(body) < content_length:
                    body += conn.recv(1024).decode()

                params = parse_query_string(body)

                if path == "/save-ap":
                    config = {
                        "SSID": params.get("ssid", DEFAULT_CONFIG["SSID"]),
                        "PASSWORD": params.get("password", DEFAULT_CONFIG["PASSWORD"]),
                        "KIT_NO": params.get("kit_no", DEFAULT_CONFIG["KIT_NO"]),
                        "STATIC_NO": params.get(
                            "static_no", DEFAULT_CONFIG["STATIC_NO"]
                        ),
                    }
                    save_config(config)
                    conn.send("HTTP/1.1 303 See Other\r\nLocation: /setup-ap\r\n\r\n")

                elif path == "/set-time":
                    try:
                        time_str = params.get("time", "")
                        time_str = urldecode(time_str).replace("%3A", ":")

                        if time_str:
                            # Parse time string (format: HH:MM)
                            hour, minute = map(int, time_str.split(":"))
                            second = 0

                            # Validate time components
                            if hour < 0 or hour > 23:
                                raise ValueError("Hour must be between 0 and 23")
                            if minute < 0 or minute > 59:
                                raise ValueError("Minute must be between 0 and 59")

                            # Get current date from system time as fallback
                            now = utime.localtime()
                            year, month, day = now[0], now[1], now[2]
                            weekday = now[6] + 1  # Convert from (0-6) to (1-7)

                            # Ensure weekday is valid (1-7)
                            if weekday < 1 or weekday > 7:
                                weekday = 1  # Default to Monday if invalid

                            print(
                                f"Setting time to: {year}-{month}-{day} {hour}:{minute}:{second} (weekday:{weekday})"
                            )

                            try:
                                rtc.set_time(
                                    year, month, day, hour, minute, second, weekday
                                )
                                print("Time set successfully")
                            except Exception as rtc_error:
                                print(f"RTC set_time failed: {rtc_error}")
                                # Fallback: Update system time instead
                                new_time = (
                                    year,
                                    month,
                                    day,
                                    hour,
                                    minute,
                                    second,
                                    weekday - 1,
                                    0,
                                )
                                utime.mktime(new_time)
                                print("Updated system time as fallback")

                        conn.send(
                            "HTTP/1.1 303 See Other\r\nLocation: /time-management\r\n\r\n"
                        )

                    except ValueError as ve:
                        print(f"Invalid time format: {ve}")
                        conn.send("HTTP/1.1 400 Bad Request\r\n\r\nInvalid time format")
                    except Exception as e:
                        print(f"Error setting time: {e}")
                        conn.send(
                            "HTTP/1.1 500 Internal Server Error\r\n\r\nTime setting failed"
                        )

                elif path.startswith("/add-schedule/"):
                    try:
                        device_id = int(path.split("/")[2])
                        schedule_data = get_schedule()

                        # Manual URL decoding for MicroPython

                        # Get and decode time value
                        time_value = params.get("time", "00:00")
                        time_value = urldecode(time_value).replace("%3A", ":")

                        # Validate time format (HH:MM)
                        if ":" in time_value:
                            hh, mm = time_value.split(":", 1)
                            if hh.isdigit() and mm.isdigit():
                                hh = max(0, min(23, int(hh)))
                                mm = max(0, min(59, int(mm)))
                                time_value = f"{hh:02d}:{mm:02d}"
                            else:
                                time_value = "00:00"
                        else:
                            time_value = "00:00"

                        enabled = "enabled" in params

                        # Parse color - handle string format "R,G,B"
                        color = [65, 65, 65]  # Default to white
                        color_str = params.get("color", "255,255,255")

                        color_str = urldecode(color_str)

                        print("-------------------")
                        print("Raw color:", color_str)

                        color_parts = color_str.split(",")
                        if len(color_parts) == 3:
                            try:
                                r, g, b = map(int, color_parts)
                                # Normalize to 0-65 with bounds checking
                                r_norm = max(0, min(65, round((r / 255) * 65)))
                                g_norm = max(0, min(65, round((g / 255) * 65)))
                                b_norm = max(0, min(65, round((b / 255) * 65)))
                                color = [r_norm, g_norm, b_norm]
                            except (ValueError, TypeError):
                                pass  # Keep default color if parsing fails

                        if 0 <= device_id < 4:
                            schedule_data[device_id]["schedules"].append(
                                {
                                    "time": time_value,
                                    "color": color,
                                    "enabled": enabled,
                                }
                            )
                            schedule_data[device_id]["schedules"] = (
                                sort_schedules_by_time(
                                    schedule_data[device_id]["schedules"]
                                )
                            )
                            save_schedule(schedule_data)

                        conn.send(
                            "HTTP/1.1 303 See Other\r\nLocation: /setup-schedule/{}\r\n\r\n".format(
                                device_id
                            )
                        )
                    except Exception as e:
                        print("Error adding schedule:", e)
                        conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")

                else:
                    conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
            except Exception as e:
                print("Error handling POST:", e)
                conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")

        else:
            conn.send("HTTP/1.1 405 Method Not Allowed\r\n\r\n")

    except Exception as e:
        print("Error in handle_request:", e)
    finally:
        try:
            conn.close()
        except:
            pass
        gc.collect()
