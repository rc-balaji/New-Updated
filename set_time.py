from lib.ds3231 import DS3231
import utime

def parse_time_input(time_str):
    """Parse HH:MM:SS string into components"""
    try:
        hh, mm, ss = map(int, time_str.split(':'))
        if not (0 <= hh < 24 and 0 <= mm < 60 and 0 <= ss < 60):
            raise ValueError
        return hh, mm, ss
    except:
        print("Invalid time format. Use HH:MM:SS")
        return None

def set_current_time(rtc):
    """Set RTC to current time with user input"""
    print("\nCurrent RTC Time:", rtc.get_formatted_time())
    
    # Get time from user
    while True:
        time_str = "12:19:03"
        
        if time_str.lower() == 'now':
            # Use system time
            now = utime.localtime()
            year, month, day = now[0], now[1], now[2]
            hour, minute, second = now[3], now[4], now[5]
            weekday = now[6] + 1
            break
        else:
            # Parse user input
            time_parts = parse_time_input(time_str)
            if time_parts:
                hour, minute, second = time_parts
                # Get current date
                now = utime.localtime()
                year, month, day = now[0], now[1], now[2]
                weekday = now[6] + 1
                break
    
    # Set the time
    rtc.set_time(year, month, day, hour, minute, second, weekday)
    print(f"Time set to: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")

def main():
    print("DS3231 Time Setting Utility")
    try:
        rtc = DS3231()
        set_current_time(rtc)
        
        # Continuous time display
        print("\nCurrent RTC Time (Ctrl+C to exit):")
        while True:
            print(f"\r{rtc.get_formatted_date()} {rtc.get_formatted_time()}", end='')
            utime.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        print("Check your wiring and try again")

if __name__ == "__main__":
    main()