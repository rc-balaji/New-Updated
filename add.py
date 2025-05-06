from machine import I2C, Pin, RTC
import utime
import sys
import machine

# Constants
DS3231_I2C_ADDR = 0x68  # 104 in decimal
REG_SECONDS = 0x00
REG_CONTROL = 0x0E
REG_TEMP_MSB = 0x11

class DS3231:
    def __init__(self, i2c_port=0, scl_pin=22, sda_pin=21, freq=100000):
        """Initialize DS3231 RTC"""
        self.i2c = I2C(i2c_port, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
        self.rtc = RTC() if 'RTC' in dir(machine) else None
        self._verify_connection()
        
    def _verify_connection(self):
        """Verify DS3231 is connected and responding"""
        try:
            devices = self.i2c.scan()
            if DS3231_I2C_ADDR not in devices:
                raise RuntimeError(f"DS3231 not found on I2C bus. Found devices: {[hex(x) for x in devices]}")
            # Test read the first register
            self._read_registers(REG_SECONDS, 1)
        except Exception as e:
            raise RuntimeError(f"DS3231 communication error: {str(e)}. Check wiring and pull-up resistors.")

    def _read_registers(self, reg, length):
        """Read one or more registers"""
        return self.i2c.readfrom_mem(DS3231_I2C_ADDR, reg, length)
    
    def _write_register(self, reg, value):
        """Write to a single register"""
        self.i2c.writeto_mem(DS3231_I2C_ADDR, reg, bytes([value]))
    
    def bcd_to_dec(self, bcd):
        """Convert BCD to decimal"""
        return ((bcd >> 4) * 10) + (bcd & 0x0F)
    
    def dec_to_bcd(self, dec):
        """Convert decimal to BCD"""
        tens, units = divmod(dec, 10)
        return (tens << 4) + units
    
    def get_time(self, set_system_rtc=False):
        """Get current time from DS3231"""
        try:
            data = self._read_registers(REG_SECONDS, 7)
            
            # Parse the registers
            ss = self.bcd_to_dec(data[0] & 0x7F)  # seconds
            mm = self.bcd_to_dec(data[1] & 0x7F)  # minutes
            
            # Handle 12/24 hour mode
            if data[2] & 0x40:  # 12 hour mode
                hh = self.bcd_to_dec(data[2] & 0x1F)
                if data[2] & 0x20:  # PM flag
                    hh += 12
            else:  # 24 hour mode
                hh = self.bcd_to_dec(data[2] & 0x3F)
            
            wday = data[3] & 0x07  # day of week (1-7)
            dd = self.bcd_to_dec(data[4] & 0x3F)  # day of month
            month = self.bcd_to_dec(data[5] & 0x1F)  # month
            
            # Handle century bit
            year = self.bcd_to_dec(data[6])
            if data[5] & 0x80:  # century bit
                year += 2000
            else:
                year += 1900
            
            time_tuple = (year, month, dd, hh, mm, ss, wday - 1, 0)
            
            if set_system_rtc and self.rtc:
                self.rtc.datetime(time_tuple)
            
            return time_tuple
        except Exception as e:
            print(f"Error reading time: {e}")
            return None
    
    def set_time(self, year, month, day, hour, minute, second, weekday=None):
        """Set DS3231 time"""
        try:
            if weekday is None:
                weekday = utime.localtime()[6] + 1  # Get current weekday
            
            # Convert values to BCD
            data = [
                self.dec_to_bcd(second),
                self.dec_to_bcd(minute),
                self.dec_to_bcd(hour),  # Sets to 24-hour mode
                self.dec_to_bcd(weekday),
                self.dec_to_bcd(day),
                self.dec_to_bcd(month)
            ]
            
            # Handle century bit
            if year >= 2000:
                data[5] |= 0x80  # Set century bit
                data.append(self.dec_to_bcd(year - 2000))
            else:
                data.append(self.dec_to_bcd(year - 1900))
            
            # Write all time registers at once
            self.i2c.writeto_mem(DS3231_I2C_ADDR, REG_SECONDS, bytes(data))
            return True
        except Exception as e:
            print(f"Error setting time: {e}")
            return False
    
    def get_temperature(self):
        """Get temperature in Celsius"""
        try:
            data = self._read_registers(REG_TEMP_MSB, 2)
            temp = data[0] + (data[1] >> 6) * 0.25
            if data[0] & 0x80:  # Negative temperature
                temp -= 256
            return temp
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return None
    
    def enable_oscillator(self, enable=True):
        """Enable or disable the oscillator (stop/start the clock)"""
        try:
            control = self._read_registers(REG_CONTROL, 1)[0]
            if enable:
                control &= ~0x80  # Clear EOSC bit
            else:
                control |= 0x80  # Set EOSC bit
            self._write_register(REG_CONTROL, control)
            return True
        except Exception as e:
            print(f"Error controlling oscillator: {e}")
            return False

# Example Usage
def main():
    print("Initializing DS3231...")
    
    try:
        # Initialize with default pins (22 for SCL, 21 for SDA)
        rtc = DS3231()
        
        # Example: Set RTC to compile time (comment out after first run)
        # year, month, day, hour, minute, second, weekday = utime.localtime()[:7]
        # rtc.set_time(year, month, day, hour, minute, second, weekday)
        
        while True:
            # Get and print time
            time_data = rtc.get_time(set_system_rtc=True)
            if time_data:
                print(f"DS3231 Time: {time_data[0]}-{time_data[1]:02d}-{time_data[2]:02d} "
                      f"{time_data[3]:02d}:{time_data[4]:02d}:{time_data[5]:02d}")
            
            # Get and print temperature
            temp = rtc.get_temperature()
            if temp is not None:
                print(f"Temperature: {temp:.2f}°C")
            
            utime.sleep(1)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()