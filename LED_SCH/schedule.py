import gc

import time

from file_opertaions import get_data, get_bin_queue, set_bin_queue, set_data


def check_schedules(rtc, bin_obj):
    while True:
        # Get current time from DS3231 RTC
        current_time = rtc.get_time()
        current_hour = current_time[3]
        current_minute = current_time[4]

        print(f"Current Time: {current_hour:02}:{current_minute:02}")
        data = get_data()

        bin_queue = get_bin_queue()
        # print(bin_queue)

        for index, _bin in enumerate(data["bins"]):
            for schedule in _bin["schedules"]:
                if schedule["enabled"]:
                    schedule_hour, schedule_minute = map(
                        int, schedule["time"].split(":")
                    )
                    if (
                        current_hour == schedule_hour
                        and current_minute == schedule_minute
                    ):
                        if bin_obj.bins[index].clicked:
                            _bin["colorESP"] = schedule["colorESP"]
                            _bin["clicked"] = False
                            bin_obj.bins[index].color = tuple(schedule["colorESP"])
                            bin_obj.bins[index].change_led_color()
                            bin_obj.bins[index].clicked = False
                            bin_obj.bins[index].active_schedules.append(schedule)
                        else:
                            bin_queue[str(index)].append(tuple(schedule["colorESP"]))
                            print(
                                f"Schedule missed for bin {index}, color added to queue"
                            )

        # print(bin_queue)
        set_data(data)
        set_bin_queue(bin_queue)

        gc.collect()
        time.sleep(60)
