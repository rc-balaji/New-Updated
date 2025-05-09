from ds3231 import DS3231
import utime

def main():
    print("DS3231 Time Display")
    try:
        rtc = DS3231()
        
        print("Current RTC Time (Ctrl+C to exit):")
        while True:
            date_str = rtc.get_formatted_date()
            time_str = rtc.get_formatted_time()
            print(f"\r{date_str} {time_str}", end='')
            utime.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        print("Check your wiring and try again")

if __name__ == "__main__":
    main()