from machine import I2C, Pin, RTC
import utime

class DS3231:
    def __init__(self, i2c_port=0, scl_pin=22, sda_pin=21, freq=100000):
        """Initialize DS3231 RTC"""
        self.i2c = I2C(i2c_port, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
        self.address = 0x68
        self._verify_connection()
        
    def _verify_connection(self):
        """Verify DS3231 is connected"""
        if self.address not in self.i2c.scan():
            raise RuntimeError("DS3231 not found on I2C bus")

    def _read_registers(self, reg, length):
        """Read registers from DS3231"""
        return self.i2c.readfrom_mem(self.address, reg, length)
    
    def _write_register(self, reg, value):
        """Write to a register"""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))
    
    def bcd_to_dec(self, bcd):
        """Convert BCD to decimal"""
        return ((bcd >> 4) * 10) + (bcd & 0x0F)
    
    def dec_to_bcd(self, dec):
        """Convert decimal to BCD"""
        tens, units = divmod(dec, 10)
        return (tens << 4) + units
    
    def get_time(self):
        """Get current time as (year, month, day, hour, minute, second, weekday)"""
        data = self._read_registers(0x00, 7)
        
        ss = self.bcd_to_dec(data[0] & 0x7F)
        mm = self.bcd_to_dec(data[1] & 0x7F)
        
        # Handle 12/24 hour mode
        if data[2] & 0x40:  # 12 hour mode
            hh = self.bcd_to_dec(data[2] & 0x1F)
            if data[2] & 0x20:  # PM
                hh += 12
        else:  # 24 hour mode
            hh = self.bcd_to_dec(data[2] & 0x3F)
        
        wday = data[3] & 0x07
        dd = self.bcd_to_dec(data[4] & 0x3F)
        month = self.bcd_to_dec(data[5] & 0x1F)
        
        # Handle century bit
        year = self.bcd_to_dec(data[6])
        year += 2000 if (data[5] & 0x80) else 1900
        
        return (year, month, dd, hh, mm, ss, wday - 1)
    
    def set_time(self, year, month, day, hour, minute, second, weekday=None):
        """Set DS3231 time"""
        if weekday is None:
            weekday = utime.localtime()[6] + 1
            
        data = [
            self.dec_to_bcd(second),
            self.dec_to_bcd(minute),
            self.dec_to_bcd(hour),  # 24-hour mode
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
        
        self.i2c.writeto_mem(self.address, 0x00, bytes(data))
    
    def get_formatted_time(self):
        """Return time as formatted string HH:MM:SS"""
        t = self.get_time()
        return f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    
    def get_formatted_date(self):
        """Return date as formatted string YYYY-MM-DD"""
        t = self.get_time()
        return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"