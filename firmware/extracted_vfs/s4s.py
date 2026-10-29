import time,machine,i2c,os,gc
from micropython import const
import esp_audio,json

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import lcd_bus,st7789,task_handler,ft6x36,fs_driver
import lvgl as lv  
from machine import Pin, PWM, ADC,time_pulse_us,reset
import sys
import uselect
from esp32 import NVS
import ui
import version
_WIDTH = const(320)
_HEIGHT = const(240)
MAINBOARD_ADDR = 0x0F

CHARGE_ADDR = 0x00
AMBIENT_LIGHT_ADDR  = 0x0A
RTC_ADDR            = 0x14
SERVO_ADDR          = 0x1E
VOICE_ADDR          = 0x28

ENCODER_MOTOR_REG    = [0x50, 0x6E, 0x8C, 0xAA]
ENCODER_MOTOR_PAIR_REG     = 0xC8

LSM6DS3_ADDR = 0x6B
ULTR_ADDR = 0x57
GYRO_ADDR = 0x6F

K210_ADDR = 0x24

spi_bus = machine.SPI.Bus(host=1,mosi=40,miso=38,sck=39)
i2c_bus = i2c.I2C.Bus(host=0, scl=41, sda=42, freq=100000, use_locks=True)
i2c2_bus = i2c.I2C.Bus(host=1, scl=2, sda=1, freq=100000, use_locks=True)

def load_config(path="config.txt"):
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except Exception as e:
        try:
            default = {
                "wifi": {
                    "ssid": " ",
                    "pswd": " "
                },
                "websocket": "ws://139.129.32.56:3000/ws/device",
                "iot": "123.com"
            }
            with open(path, "w") as f:
                f.write(json.dumps(default))
            return default
        except Exception as e2:
            return {}

def save_config(cfg, path="config.txt"):
    try:
        with open(path, "w") as f:
            f.write(json.dumps(cfg))
        return True
    except Exception as e:
        return False

def save_file(code,path = "user_code.py"):
    try:
        with open(path, "w") as f:
            f.write(code)
            nvs = NVS("mode")
            nvs.set_i32("opt", 1)
            nvs.commit()
            restart()
    except Exception as e:
        return False

def update_wifi_config(ssid, pswd, path="config.txt"):

    cfg = load_config(path)
    if not isinstance(cfg, dict):
        cfg = {}
    wifi = cfg.get("wifi")
    if not isinstance(wifi, dict):
        wifi = {}
    wifi["ssid"] = ssid
    wifi["pswd"] = pswd
    cfg["wifi"] = wifi
    return save_config(cfg, path)

def restart():
    reset()
def get_device_info():
    return version.version
def set_opt(opt):
    nvs = NVS("mode")
    nvs.set_i32("opt", opt)
    nvs.commit()
class A_B_Button:
    def __init__(self):
        self.A = 0
        self.B = 1
        self.a_button = False
        self.b_button = False
    def is_pressed(self,but):
        if but == self.A:
            return self.a_button
        if but == self.B:
            return self.b_button
button = A_B_Button()

class Display:
    def __init__(self):
        self.spi = spi_bus
        self.i2c = i2c_bus
        display_bus = lcd_bus.SPIBus(spi_bus=self.spi,freq=80000000,dc=5,cs=4,)
        self.s4s_state = ui.state
        # BUF_SIZE = 320 * 120 * 2

        # buf1 = bytearray(BUF_SIZE)
        # buf2 = bytearray(BUF_SIZE)
        self.display = st7789.ST7789(
            data_bus=display_bus,
            display_width=_WIDTH,
            display_height=_HEIGHT,
            frame_buffer1 = None,
            frame_buffer2 = None,
            backlight_pin=15,
            backlight_on_state=st7789.STATE_HIGH,
            reset_pin=6,
            reset_state=st7789.STATE_LOW,
            color_space=lv.COLOR_FORMAT.RGB565,
            color_byte_order=st7789.BYTE_ORDER_BGR,
            rgb565_byte_swap=True,
        )
        self.display.reset()
        self.display.set_power(True)
        self.display.init()
        touch_dev = i2c.I2C.Device(bus=self.i2c, dev_id=ft6x36.I2C_ADDR, reg_bits=ft6x36.BITS)
        indev = ft6x36.FT6x36(touch_dev,debug = False)
        self.indev = indev
        if not indev.is_calibrated:
            self.display.set_backlight(100)
            indev.calibrate()
        indev.enable_input_priority()    
        indev.set_virtual_key_callback(self.vk_handler)
        th = task_handler.TaskHandler(duration=5)
        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'S')
        scr = lv.screen_active()
        scr.set_style_bg_color(lv.color_hex(0x000000), 0)
        scr.set_style_bg_opa(255, 0)
        lv.refr_now(None) 
    def init(self):
        ui.init_ui()
        lv.refr_now(None)   # 立即刷新一帧
        self.display.set_backlight(100)
    def vk_handler(self,key, event):
        if key == "A":
            if event == "pressed":
                button.a_button = True
            elif event == "released":
                button.a_button = False
        elif key == "B":
            if event == "pressed":
                button.b_button = True
            elif event == "released":
                button.b_button = False
    def touch_calibration(self):
        self.indev.calibrate()
display = Display()
class i2c_device:
    def __init__(self,i2c):
        self.i2c = i2c
        self.error = False

    # 安全读寄存器
    def read_reg(self, addr, reg_offset, length):
        try:
            data = self.i2c.readfrom_mem(addr, reg_offset, length)
            if len(data) != length:
                raise OSError("I2C read length mismatch")
            self.error = False
            return data
        except OSError as e:
            self.error = True
            return bytes([0]*length)
    # 安全写寄存器
    def write_reg(self, addr, reg_offset, data: bytes):
        try:
            self.i2c.writeto_mem(addr, reg_offset, data)
        except OSError as e:
            pass
    # 安全写
    def write_data(self,addr,buf:bytes):
        try:
            self.i2c.writeto(addr,buf)
        except OSError as e:
            pass    
    # 安全读
    def read_data(self,addr,length):
        try:
            data = self.i2c.readfrom(addr,length)
            if len(data) != length:
                raise OSError("I2C read length mismatch")
            return data
        except OSError as e:
            return bytes([0]*length)

class Movement:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.FORWARD = 0
        self.BACKWARD = 1
        self.LEFT = 2
        self.RIGHT = 3
        self.SECONDS = 0
        self.ROTATIONS = 1 
        self.CENTIMETERS = 2 
    def wait_for_motor_action_complete(self):
        time.sleep_ms(200)

        while True:
            status = self.i2c.read_reg(MAINBOARD_ADDR,ENCODER_MOTOR_PAIR_REG + 0x06,1)[0]
            time.sleep_ms(100)
            if status == 0:
                break

    def set_motors(self,left_id, right_id):
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG + 0x01, bytes([left_id, right_id]))
    def start(self,direction):
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG, bytes([direction+1]))
    def move(self,direction, num, state): 
        if state >0:
            buf = bytearray(4)

            buf[0] = (num >> 8) & 0xFF
            buf[1] = num & 0xFF

            buf[2] = buf[0]
            buf[3] = buf[1]
        else:
            buf = bytearray(2)

            buf[0] = (num >> 8) & 0xFF
            buf[1] = num & 0xFF
        offset = state + 3


        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG+offset, bytes(buf))
        action = direction + 5 + state * 4
        
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG, bytes([action]))
        self.wait_for_motor_action_complete()

    def drive(self,l_speed,r_speed):

        l_dir = 0 if l_speed < 0 else 1
        r_dir = 0 if r_speed < 0 else 1

        l_speed = min(100, abs(int(l_speed)))
        r_speed = min(100, abs(int(r_speed)))

        buf = bytearray(4)

        buf[0] = (l_speed >> 8) & 0xFF
        buf[1] = l_speed & 0xFF

        buf[2] = (r_speed >> 8) & 0xFF
        buf[3] = r_speed & 0xFF
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG+0x02, bytes(buf))
        direction = 0
        if l_dir and r_dir:
            direction = 1
        elif (not l_dir) and (not r_dir):
            direction = 2
            if not l_speed and not r_speed:
                direction = 0
        elif (not l_dir) and r_dir:
            direction = 3
        elif l_dir and (not r_dir):
            direction = 4
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG, bytes([direction]))

    def drive_for(self,l_speed,r_speed,num, state):
        l_dir = 0 if l_speed < 0 else 1
        r_dir = 0 if r_speed < 0 else 1

        l_speed = min(100, abs(int(l_speed)))
        r_speed = min(100, abs(int(r_speed)))

        speed_buf = bytearray(4)

        speed_buf[0] = (l_speed >> 8) & 0xFF
        speed_buf[1] = l_speed & 0xFF

        speed_buf[2] = (r_speed >> 8) & 0xFF
        speed_buf[3] = r_speed & 0xFF
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG+0x02, bytes(speed_buf))

        offset = state + 3

        if state >0:
            buf = bytearray(4)

            buf[0] = (num >> 8) & 0xFF
            buf[1] = num & 0xFF

            buf[2] = buf[0]
            buf[3] = buf[1]
        else:
            buf = bytearray(2)

            buf[0] = (num >> 8) & 0xFF
            buf[1] = num & 0xFF
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG+offset, bytes(buf))

        direction = 0
        if l_dir and r_dir:
            direction = 5
        elif (not l_dir) and (not r_dir):
            direction = 6
        elif (not l_dir) and r_dir:
            direction = 7
        elif l_dir and (not r_dir):
            direction = 8
        direction += state * 4
        if not l_speed and not r_speed:
            direction = 0

        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG, bytes([direction]))
        self.wait_for_motor_action_complete()

        return direction

    def stop(self):
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG, bytes([0]))
    def set_speed(self,speed):

        speed = min(100, abs(int(speed)))
        buf = bytearray(4)
        buf[0] = (speed >> 8) & 0xFF
        buf[1] = speed & 0xFF
        buf[2] = buf[0]
        buf[3] = buf[1]
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_PAIR_REG+0x02, bytes(buf))
movement = Movement()

class Motors:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.FORWARD = 0
        self.BACKWARD = 1

        self.ROTATIONS = 0
        self.DEGREES = 1
        self.SECONDS = 2
        self.CENTIMETERS = 3 
        self.speed_cache = [5, 5, 5, 5]
    def _clamp_speed(self, s):
        return max(0, min(100, abs(int(s))))

    def _write_action(self, motorid, action):
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x04, bytes([action]))

    def wait_for_motor_action_complete(self,motorid):
        time.sleep_ms(200)

        while True:
            status = self.i2c.read_reg(MAINBOARD_ADDR,ENCODER_MOTOR_REG[motorid] + 0x0C,1)[0]
            time.sleep_ms(100)
            if status == 0:
                break

    def run_for(self, motorid, direction, num, mode):
        num = int(num)
        buf = bytes([
            (num >> 8) & 0xFF,
            num & 0xFF
        ])

        # 写目标值
        reg_map = {
            0: 0x08,  # rotations
            1: 0x09,  # degrees
            2: 0x0A,  # seconds
            3: 0x0B   # cm
        }
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + reg_map[mode],buf)

        # action映射（对齐C逻辑）
        base = {
            0: 7,
            1: 9,
            2: 11,
            3: 13
        }[mode]
        action = base + direction
        self._write_action(motorid, action)
        self.wait_for_motor_action_complete(motorid)

    def start(self, motorid, direction):
        buf = bytes([
            (self.speed_cache[motorid] >> 8) & 0xFF,
            self.speed_cache[motorid] & 0xFF
        ])
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x06,buf)
        time.sleep_ms(10)
        self._write_action(motorid, direction + 3)

    def stop(self, motorid):
        self._write_action(motorid, 0)

    def set_speed(self, motorid, speed):
        speed = self._clamp_speed(speed)
        self.speed_cache[motorid] = speed

        buf = bytes([(speed >> 8) & 0xFF, speed & 0xFF])
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x06, buf)

    def start_rpm(self, motorid, rpm):
        direction = 1 if rpm > 0 else 2

        rpm = self._clamp_speed(rpm)
        actual = rpm * 180 // 100

        buf = bytes([(actual >> 8) & 0xFF, actual & 0xFF])

        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x05, buf)
        self._write_action(motorid, direction)

    def position(self, motorid):
        data = self.i2c.read_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid], 4)
        angle = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
        if angle & 0x80000000:
            angle -= 0x100000000
        return angle 

    def speed(self, motorid):
        data = self.i2c.read_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x02, 2)
        speed = (data[0] << 8) | data[1]
        if speed & 0x8000:
            speed -= 0x10000
        return speed

    def rpm(self, motorid):
        data = self.i2c.read_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid] + 0x01, 2)
        rpm = (data[0] << 8) | data[1]
        if rpm & 0x8000:
            rpm -= 0x10000
        return rpm * 100 // 180

    def reset_position(self, motorid):
        self.i2c.write_reg(MAINBOARD_ADDR, ENCODER_MOTOR_REG[motorid], bytes([0,0,0,0]))
motors = Motors()

class Servo:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
    def set_angle(self, id, angle):
        if id > 1: return
        angle = max(0, min(180, abs(int(angle))))
        self.i2c.write_reg(MAINBOARD_ADDR, SERVO_ADDR + id, bytes([angle]))
    
    def release(self, id):
        if id > 1: return
        self.i2c.write_reg(MAINBOARD_ADDR, SERVO_ADDR + 4 + id, bytes([0x00]))

    def set_speed(self, id, speed):
        if id > 1: return
        speed = max(-100, min(100, int(speed)))
        self.i2c.write_reg(MAINBOARD_ADDR, SERVO_ADDR + 2 + id, bytes([speed & 0xFF]))

    def stop(self, servo_id):
        self.set_speed(servo_id, 0)
servo = Servo()

class Light:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.default_brightness = 25
    def set_color(self, r, g, b, brightness=None):
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        if brightness is not None:
            self.set_brightness(brightness)
        else:
            self.set_brightness(self.default_brightness)
        self.i2c.write_reg(MAINBOARD_ADDR, AMBIENT_LIGHT_ADDR + 1, bytes([r,g,b]))

    def set_brightness(self,brightness):
        brightness = max(0, min(255, int(brightness)))
        self.i2c.write_reg(MAINBOARD_ADDR, AMBIENT_LIGHT_ADDR, bytes([brightness]))
light = Light()

class LSM6DS3:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.init()
    def twos_complement(self,val, bits=16):
        """将 val 转为有符号整数"""
        if val & (1 << (bits - 1)):
            val -= 1 << bits
        return val

    def init(self):
        try:
            who = self.i2c.read_reg(LSM6DS3_ADDR, 0x0F, 1)[0]
            if who not in (0x69, 0x6A):
                return False
            # CTRL1_XL  加速度 104Hz 2g
            self.i2c.write_reg(LSM6DS3_ADDR, 0x10, bytes([0x40]))
            # CTRL2_G   陀螺仪 104Hz 2000dps
            self.i2c.write_reg(LSM6DS3_ADDR, 0x11, bytes([0x4C]))
            # CTRL3_C   自动地址递增
            self.i2c.write_reg(LSM6DS3_ADDR, 0x12, bytes([0x04]))
            return True

        except Exception as e:
            return False
    def accel(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x28, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        y = self.twos_complement(y)
        z = self.twos_complement(z)

        return x*0.061*8/1000, y*0.061*8/1000, z*0.061*8/1000
    def gyro(self):
        """返回角速度 (deg/s)"""
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x22, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        y = self.twos_complement(y)
        z = self.twos_complement(z)
        return x*70/1000, y*70/1000, z*70/1000
    def readFloatAccelX(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x28, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        return x*0.061*8/1000
    def readFloatAccelY(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x28, 6)
        # 手动组合 LSB+MSB
        y = data[2] | (data[3] << 8)
        # 转为有符号数
        y = self.twos_complement(y)
        return y*0.061*8/1000
    def readFloatAccelZ(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x28, 6)
        # 手动组合 LSB+MSB
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        z = self.twos_complement(z)
        return z*0.061*8/1000
    def readFloatGyroX(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x22, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        return x*70/1000
    def readFloatGyroY(self):
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x22, 6)
        # 手动组合 LSB+MSB
        y = data[2] | (data[3] << 8)
        # 转为有符号数
        y = self.twos_complement(y)
        return y*70/1000
    def readFloatGyroZ(self):   
        data = self.i2c.read_reg(LSM6DS3_ADDR, 0x22, 6)
        # 手动组合 LSB+MSB
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        z = self.twos_complement(z)
        return z*70/1000 
gyro = LSM6DS3()

class QMC5883:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.init()
    def twos_complement(self,val, bits=16):
        """将 val 转为有符号整数"""
        if val & (1 << (bits - 1)):
            val -= 1 << bits
        return val
    def init(self):
        """初始化 QMC5883L 磁力计"""
        # 检查芯片ID
        try:
            chip_id = self.i2c.read_reg(0x2C, 0, 1)[0]
            if chip_id != 0x80:
                return False
            ctrl1 = self.i2c.read_reg(0x2C,0x0A, 1)[0]
            ctrl1 = (ctrl1 & 0xFC) | (0x03 & 0x03)
            self.i2c.write_reg(0x2C, 0x0A, bytes([ctrl1]))
            ctrl2 = self.i2c.read_reg(0x2C, 0x0B, 1)[0]
            ctrl2 = (ctrl2 & 0xF3) | ((0x02 & 0x03) << 2)
            self.i2c.write_reg(0x2C, 0x0B, bytes([ctrl2]))
            return True
        except OSError as e:
            return False
    def is_data_ready(self):
        status = self.i2c.read_reg(0x2C, 0x09, 1)[0]
        return (status & 0x01) != 0
    def get_raw(self):
        data = self.i2c.read_reg(0x2C, 0x01, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        y = self.twos_complement(y)
        z = self.twos_complement(z)
        return x, y, z
    def get_gauss(self):
        x, y, z = self.get_raw()
        ctrl2 = self.i2c.read_reg(0x2C, 0x0B, 1)[0]
        range_bits = (ctrl2 >> 2) & 0x03
        if range_bits == 0x00:
            lsb_per_gauss = 1000.0
        elif range_bits == 0x01:
            lsb_per_gauss = 2500.0
        elif range_bits == 0x02:
            lsb_per_gauss = 3750.0
        elif range_bits == 0x03:
            lsb_per_gauss = 15000.0
        else:
            lsb_per_gauss = 1000.0
        return x/lsb_per_gauss, y/lsb_per_gauss, z/lsb_per_gauss
    def read_heading(self):
        """直接返回航向角度（°）"""
        x, y, z = self.get_raw()
        from math import atan2, degrees
        return degrees(atan2(
            y,
            x
        )) % 360
    def getRawMagneticX(self):
        data = self.i2c.read_reg(0x2C, 0x01, 6)
        # 手动组合 LSB+MSB
        x = data[0] | (data[1] << 8)
        # 转为有符号数
        x = self.twos_complement(x)
        return x 
    def getRawMagneticY(self):
        data = self.i2c.read_reg(0x2C, 0x01, 6)
        # 手动组合 LSB+MSB
        y = data[2] | (data[3] << 8)
        # 转为有符号数
        y = self.twos_complement(y)
        return y 
    def getRawMagneticZ(self):
        data = self.i2c.read_reg(0x2C, 0x01, 6)
        # 手动组合 LSB+MSB
        z = data[4] | (data[5] << 8)
        # 转为有符号数
        z = self.twos_complement(z)
        return z   
    def getGaussFieldX(self):  
        data = self.getRawMagneticX()
        ctrl2 = self.i2c.read_reg(0x2C, 0x0B, 1)[0]
        range_bits = (ctrl2 >> 2) & 0x03
        if range_bits == 0x00:
            lsb_per_gauss = 1000.0
        elif range_bits == 0x01:
            lsb_per_gauss = 2500.0
        elif range_bits == 0x02:
            lsb_per_gauss = 3750.0
        elif range_bits == 0x03:
            lsb_per_gauss = 15000.0
        else:
            lsb_per_gauss = 1000.0
        return data/lsb_per_gauss
    def getGaussFieldY(self): 
        data = self.getRawMagneticY()
        ctrl2 = self.i2c.read_reg(0x2C, 0x0B, 1)[0]
        range_bits = (ctrl2 >> 2) & 0x03
        if range_bits == 0x00:
            lsb_per_gauss = 1000.0
        elif range_bits == 0x01:
            lsb_per_gauss = 2500.0
        elif range_bits == 0x02:
            lsb_per_gauss = 3750.0
        elif range_bits == 0x03:
            lsb_per_gauss = 15000.0
        else:
            lsb_per_gauss = 1000.0
        return data/lsb_per_gauss
    def getGaussFieldZ(self):  
        data = self.getRawMagneticZ()
        ctrl2 = self.i2c.read_reg(0x2C, 0x0B, 1)[0]
        range_bits = (ctrl2 >> 2) & 0x03
        if range_bits == 0x00:
            lsb_per_gauss = 1000.0
        elif range_bits == 0x01:
            lsb_per_gauss = 2500.0
        elif range_bits == 0x02:
            lsb_per_gauss = 3750.0
        elif range_bits == 0x03:
            lsb_per_gauss = 15000.0
        else:
            lsb_per_gauss = 1000.0
        return data/lsb_per_gauss 
magnetometer = QMC5883()

class Ultrasonic:
    def __init__(self):
        self.i2c = i2c_device(i2c2_bus)
        self.MM = 0
        self.CM = 1
        self.M = 2
        self.INCH = 3
    def is_device(self):
        try:
            self.i2c.write_data(ULTR_ADDR, b'')
            return True
        except:
            return False

    def get_distance(self, unit):
        data = self.i2c.read_reg(ULTR_ADDR, 0x01, 3)
        distance_raw = (data[0] << 16) | (data[1] << 8) | data[2]
        if unit == self.MM:
            return distance_raw / 10.0
        elif unit == self.CM:
            return distance_raw / 10000.0
        elif unit == self.METER:
            return distance_raw / 1000000.0
        elif unit == self.INCH:
            return distance_raw / (25.4*100.0)
        return distance_raw / 10.0

    def set_color(self, r, g, b, brightness=125):
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        brightness = max(0, min(255, int(brightness)))

        data = bytes([brightness,r,g,b])
        self.i2c.write_reg(ULTR_ADDR, 0x02, data)
ultrasonic = Ultrasonic()
    
class Line_sensor:
    def __init__(self):
        self.i2c = i2c_device(i2c2_bus)
        self.GRAY = -2
        self.COLOR_NONE = -1
        self.RED = 2
        self.GREEN = 3
        self.BLUE = 4
        self.YELLOW = 5
        self.CYAN = 6
        self.PURPLE = 7
        self.BLACK = 8
        self.WHITE = 9

        self.PROBE_L1 = 1
        self.PROBE_L2 = 0
        self.PROBE_R1 = 2
        self.PROBE_R2 = 3

        self. COLOR_STUDY_MAP = {
            self.RED: 7,
            self.GREEN: 8,
            self.BLUE: 9,
            self.YELLOW: 10,
            self.CYAN: 11,
            self.PURPLE: 12,
            self.BLACK: 13,
            self.WHITE: 14

        }
    def wait_for_motor_action_complete(self,mode):
        time.sleep_ms(200)

        for _ in range(10):  # 最多循环10次
            data = self.i2c.read_data(GYRO_ADDR, 5)
            time.sleep_ms(100)
            if data[4] == mode:
                return data
        else:
            data = [0,0,0,0,0]
            return data

    def is_device(self):
        try:
            self.i2c.write_data(GYRO_ADDR, b'')
            return True
        except:
            return False

    def learn(self,color):

        if color == self.GRAY:
            self.i2c.write_data(GYRO_ADDR,bytes([4]))
            return
        if color == self.COLOR_NONE:
            self.i2c.write_data(GYRO_ADDR, bytes([6]))
            return
        cmd = self.COLOR_STUDY_MAP.get(color)

        if cmd is None:
            raise ValueError("unsupported color")

        self.i2c.write_data(GYRO_ADDR, bytes([cmd]))
    def gray(self,probe=None):
        self.i2c.write_data(GYRO_ADDR,bytes([0x02]))
        data = self.i2c.read_data(GYRO_ADDR,5)
        if data[4] != 0x02:
            data = self.wait_for_motor_action_complete(0x02)
        
        if probe is None:
            return data

        return data[probe]
    
    def color(self,probe,target=None):
        self.i2c.write_data(GYRO_ADDR,bytes([0x01]))
        data = self.i2c.read_data(GYRO_ADDR,5)
        if data[4] != 0x01:
            data = self.wait_for_motor_action_complete(0x01)
        values = []
        for v in data:
            v += 1

            if v == 1:
                values.append(self.COLOR_NONE)
            else:
                values.append(v)

        c = values[probe]
        if target is None:
            return c

        # 返回bool
        return c == target

    def detect_line(self,probe=None):
        self.i2c.write_data(GYRO_ADDR,bytes([0x03]))
        data = self.i2c.read_data(GYRO_ADDR,5)
        if data[4] != 0x03:
            data = self.wait_for_motor_action_complete(0x03)
        
        return bool(data[probe])
line_sensor = Line_sensor()

class Voice:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.UNKNOWN = 0
        self.LINKBOT = 1
        self.GO_FORWARD = 2
        self.GO_BACK = 3
        self.TURN_LEFT = 4
        self.TURN_RIGHT = 5
        self.START_MOVING = 6
        self.STOP_MOVING = 7
        self.SPEED_UP = 8
        self.SLOW_DOWN = 9
        self.SPIN_AROUND = 10
        self.FOLLOW_LINE = 11
        self.LIGHTS_ON = 12
        self.LIGHTS_OFF = 13
        self.SHOW_RED = 14
        self.SHOW_GREEN = 15
        self.SHOW_BLUE = 16
        self.CHECK_DISTANCE = 17
        self.SCAN_SURROUNDINGS = 18
        self.DETECT_OBJECT = 19
        self.DETECT_FACE = 20
        self.DETECT_CARD = 21
        self.READ_SENSOR = 22
        self.CHECK_BATTERY = 23
        self.FIND_LINE = 24
        self.WHO_AM_I = 25
        self.WHO_ARE_YOU = 26
        self.START = 27
        self.STOP = 28
        self.REPEAT = 29
        self.NEXT = 30
        self.RETURN_HOME = 31
        self.PICK_UP = 32
        self.PUT_DOWN = 33
        self.SLEEP = 34
        self.WAKE_UP = 35
        self.PLAY_MUSIC = 36
        self.RECORD_DATA = 37
        self.SEND_MESSAGE = 38
        self.RECEIVE_MESSAGE = 39
        self.ATTACK_NOW = 40
        self.DEFEND_YOURSELF = 41
        self.SHOW_ME_A_DANCE = 42
        self.TELL_ME_A_JOKE = 43

    def recognized(self,cmd = None):
        time.sleep_ms(10)
        data = self.i2c.read_reg(MAINBOARD_ADDR, VOICE_ADDR, 1)
        if cmd is None:
            return data
        comt = bool(data[0] == cmd)
        if comt:
            self.i2c.write_reg(MAINBOARD_ADDR, VOICE_ADDR, bytes([0]))
        return comt
voice = Voice()

class Rtc:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
        self.YEAR   = 0
        self.MONTH  = 1
        self.DAY    = 2
        self.WEEK   = 3
        self.HOUR   = 4
        self.MINUTE = 5
        self.SECOND = 6

    def set_date(self, year, month, day):
        year %= 100
        if not (1 <= month <= 12):
            raise ValueError("month must be 1~12")
        if not (1 <= day <= 31):
            raise ValueError("day must be 1~31")
        data = bytes([0, month, day, year])
        self.i2c.write_reg(MAINBOARD_ADDR, RTC_ADDR+1, data)

    def set_time(self, hour, minute, second):
        if not (0 <= hour <= 23):
            raise ValueError("hour must be 0~23")
        if not (0 <= minute <= 59):
            raise ValueError("minute must be 0~59")
        if not (0 <= second <= 59):
            raise ValueError("second must be 0~59")
        data = bytes([hour, minute, second])
        self.i2c.write_reg(MAINBOARD_ADDR, RTC_ADDR, data)

    def get(self, field):
        if field in (self.YEAR, self.MONTH, self.DAY, self.WEEK):
            buf = self.i2c.read_reg(MAINBOARD_ADDR, RTC_ADDR+1, 4)
            if field == self.YEAR:
                return buf[3] + 2000
            elif field == self.MONTH:
                return buf[1]
            elif field == self.DAY:
                return buf[2]
            elif field == self.WEEK:
                return buf[0]
        elif field in (self.HOUR, self.MINUTE, self.SECOND):
            buf = self.i2c.read_reg(MAINBOARD_ADDR, RTC_ADDR, 3)
            return buf[field - 4]
        else:
            raise ValueError("Invalid RTC field")
rtc = Rtc()

class Device:
    def __init__(self):
        self.i2c = i2c_device(i2c_bus)
    def battery(self):
        data = self.i2c.read_reg(MAINBOARD_ADDR, CHARGE_ADDR, 1)
        if self.i2c.error:
            return -1
        return data[0]  # 电量百分比 (0-100)
    def voltage(self):
        data = self.i2c.read_reg(MAINBOARD_ADDR, CHARGE_ADDR + 1, 1)
        return data[0] / 10.0  # 电压单位为伏特 
    def version(self):  
        data = self.i2c.read_reg(MAINBOARD_ADDR, CHARGE_ADDR + 4, 3)
        version = ".".join(map(str, data))  # 三字节版本号
        return version
    def is_charge(self):
        data = self.i2c.read_reg(MAINBOARD_ADDR, CHARGE_ADDR+2, 1)
        return bool(data[0])  # 电量百分比 (0-100)
device = Device()

class Vision:
    def __init__(self):
        self.i2c = i2c_device(i2c2_bus)
        self.GO_FORWARD   = 0
        self.GO_BACKWARD  = 1
        self.TURN_LEFT    = 2
        self.TURN_RIGHT   = 3
        self.STOP_MOVING  = 4
        self.EVENT_HONK   = 5
        self.EVENT_TARGET = 6

        self.COLOR          = 0
        self.COLOR_TRACK    = 1
        self.TAG            = 2
        self.LINE           = 3
        self.OBJECT         = 4
        self.QR             = 5
        self.FACE_DETECT    = 6
        self.FACE_RECOGNIZE = 7
        self.AI             = 8
        self.CARD           = 9

        self.AXIS_X = 1
        self.AXIS_Y = 2
        self.AXIS_W = 3
        self.AXIS_H = 4

        self.OBJECT_AIRPLANE    = 0
        self.OBJECT_BICYCLE     = 1
        self.OBJECT_BIRD        = 2
        self.OBJECT_BOAT        = 3
        self.OBJECT_BOTTLE      = 4
        self.OBJECT_BUS         = 5
        self.OBJECT_CAR         = 6
        self.OBJECT_CAT         = 7
        self.OBJECT_CHAIR       = 8
        self.OBJECT_COW         = 9
        self.OBJECT_DININGTABLE = 10
        self.OBJECT_DOG         = 11
        self.OBJECT_HORSE       = 12
        self.OBJECT_MOTORBIKE   = 13
        self.OBJECT_PERSON      = 14
        self.OBJECT_POTTEDPLANT = 15
        self.OBJECT_SHEEP       = 16
        self.OBJECT_SOFA        = 17
        self.OBJECT_TRAIN       = 18
        self.OBJECT_TV          = 19

        self.UP     = 1
        self.MIDDLE = 2
        self.DOWN   = 3

        self.RED    = 1
        self.GREEN  = 2
        self.BLUE   = 3
        self.YELLOW = 4
        self.BLACK  = 5
        self.WHITE  = 6

        self.AI_OFF          = 0
        self.AI_CONNECTING   = 1
        self.AI_IDLE         = 2
        self.AI_LISTENING    = 3
        self.AI_SPEAKING     = 4
        self.AI_CONFIGURING  = 5

        self.FACE_OPEN_MOUTH = 1
        self.FACE_SMILE = 2
        self.FACE_GLASSES = 3

    def set_mode(self,mode):
        self.i2c.write_reg(K210_ADDR, 0, bytes([mode]))
        for _ in range(10):  # 最多循环10次
            data = self.get_mode()
            time.sleep_ms(100)
            if data == mode:
                return True
    def get_mode(self):
        return self.i2c.read_reg(K210_ADDR, 0, 1)[0]
    def color_value(self,channel):
        channel = channel - 1
        data = self.i2c.read_reg(K210_ADDR, 15, 3)
        if channel < 0 or channel >= 3:
            return 0
        return data[channel]
    def set_color(self,color):
        time.sleep(0.1)
        self.i2c.write_reg(K210_ADDR, 30, bytes([color]))
    def color_detected(self):
        data = self.i2c.read_reg(K210_ADDR, 31, 1)[0]
        if data == 0:
            return False
        else:
            return True
    def color_position(self,index):
        data = self.i2c.read_reg(K210_ADDR, 32, 8)
        if index == self.AXIS_X:
            return (data[0] << 8) | data[1]
        elif index == self.AXIS_Y:
            return (data[2] << 8) | data[3]
        elif index == self.AXIS_W:
            return (data[4] << 8) | data[5]
        elif index == self.AXIS_H:
            return (data[6] << 8) | data[7]
        else:
            return 0     
   
    def _vision_tag(self,index,order):
        data = self.i2c.read_reg(K210_ADDR, 45 + order, 12)
        if index == -1:
            return (data[0] << 8) | data[1]
        elif index == 0:
            return (data[2] << 8) | data[3]
        elif index == self.AXIS_X:
            return (data[4] << 8) | data[5]
        elif index == self.AXIS_Y:
            return (data[6] << 8) | data[7]
        elif index == self.AXIS_W:
            return (data[8] << 8) | data[9]
        elif index == self.AXIS_H:
            return (data[10] << 8) | data[11]
        else:
            return 0   
    def tag_count(self):
        return self.i2c.read_reg(K210_ADDR,45, 1)[0]
    def tag_id(self,id = 1):
        return self._vision_tag(-1,id)
    def tag_rotation(self,id = 1):
        return self._vision_tag(0,id)
    def tag_position(self,index,id = 1):
        return self._vision_tag(index,id)
    
    def line_detected(self):
        data = self.i2c.read_reg(K210_ADDR, 60, 1)[0]
        if data == 0:
            return False
        else:
            return True
    def line_position(self,line,index):
        data = self.i2c.read_reg(K210_ADDR, 60 + line, 8)
        if index == self.AXIS_X:
            return (data[0] << 8) | data[1]
        elif index == self.AXIS_Y:
            return (data[2] << 8) | data[3]
        elif index == self.AXIS_W:
            return (data[4] << 8) | data[5]
        elif index == self.AXIS_H:
            return (data[6] << 8) | data[7]
        else:
            return 0  
        
    def _vision_object(self,index,order):
        data = self.i2c.read_reg(K210_ADDR, 75 + order, 9)
        if index == -1:
            return data[0]
        elif index == self.AXIS_X:
            return (data[1] << 8) | data[2]
        elif index == self.AXIS_Y:
            return (data[3] << 8) | data[4]
        elif index == self.AXIS_W:
            return (data[5] << 8) | data[6]
        elif index == self.AXIS_H:
            return (data[7] << 8) | data[8]
        else:
            return 0 
    def object_count(self):
        return self.i2c.read_reg(K210_ADDR,75, 1)[0]
    def object_detected(self,object_id,order=1):
        if self._vision_object(-1,order) == object_id:
            return True
        else:
            return False
    def object_position(self,index,order = 1):
        return self._vision_object(index,order)
    
    def qr_detected(self):
        data = self.i2c.read_reg(K210_ADDR, 90, 1)[0]
        if data == 0:
            return False
        else:
            return True
    def qr_data(self):
        buf = self.i2c.read_reg(K210_ADDR, 93, 100)
        return buf.split(b'\x00')[0].decode()
    def qr_position(self,index):
        data = self.i2c.read_reg(K210_ADDR, 92, 8)
        if index == self.AXIS_X:
            return (data[0] << 8) | data[1]
        elif index == self.AXIS_Y:
            return (data[2] << 8) | data[3]
        elif index == self.AXIS_W:
            return (data[4] << 8) | data[5]
        elif index == self.AXIS_H:
            return (data[6] << 8) | data[7]
        else:
            return 0  
         
    def face_count(self):
        return self.i2c.read_reg(K210_ADDR,105, 1)[0]
    def face_position(self,index,face_id):
        data = self.i2c.read_reg(K210_ADDR, 105+face_id, 8)
        if index == self.AXIS_X:
            return (data[0] << 8) | data[1]
        elif index == self.AXIS_Y:
            return (data[2] << 8) | data[3]
        elif index == self.AXIS_W:
            return (data[4] << 8) | data[5]
        elif index == self.AXIS_H:
            return (data[6] << 8) | data[7]
        else:
            return 0   
    def face_attribute(self,attr,index):
        if self.face_count() == 0:
            return False
        data = self.i2c.read_reg(K210_ADDR, 105+index+4, 4)
        return bool(data[attr])
    
    def face_recognized_learn(self):
        self.i2c.write_reg(K210_ADDR, 120+6, bytes([1]))
    def face_recognized_count(self):
        return self.i2c.read_reg(K210_ADDR,120+1, 1)[0]
    def face_recognized_detected(self):
        if self.face_recognized_count()>0:
            return True
        else:
            return False
    def face_recognized_position(self,index,face_id):
        data = self.i2c.read_reg(K210_ADDR, 120+face_id+1, 9)
        if index == self.AXIS_X:
            return (data[1] << 8) | data[2]
        elif index == self.AXIS_Y:
            return (data[3] << 8) | data[4]
        elif index == self.AXIS_W:
            return (data[5] << 8) | data[6]
        elif index == self.AXIS_H:
            return (data[7] << 8) | data[8]
        else:
            return 0 

    def class_recognized(self,class_id):
        return bool(class_id == self.i2c.read_reg(K210_ADDR,135+2,1)[0])
    def card_count(self):
        return self.i2c.read_reg(K210_ADDR,150,1)[0]
    def _vision_card(self,index,order):
        if self.card_count():
            data = self.i2c.read_reg(K210_ADDR, 150 + order, 9)
            if index == 0:
                return data[0]
            elif index == self.AXIS_X:
                return (data[1] << 8) | data[2]
            elif index == self.AXIS_Y:
                return (data[3] << 8) | data[4]
            elif index == self.AXIS_W:
                return (data[5] << 8) | data[6]
            elif index == self.AXIS_H:
                return (data[7] << 8) | data[8]
            else:
                return 0 
        else:
            return -1
    def card_detected(self,target_id,type,order=1):
        if self.card_count() == 0:
            return False
        card_id = self._vision_card(0,order)
        if type == 1:
            if target_id == self.GREEN:
                if card_id == 0:
                    return True
            elif target_id == self.RED:
                if card_id == 3:
                    return True
        if type == 2:
            if target_id == self.EVENT_HONK:
                if card_id == 5:
                    return True
            elif target_id == self.EVENT_TARGET:
                if card_id == 6:
                    return True
            elif target_id == self.TURN_LEFT:
                if card_id == 1:
                    return True
            elif target_id == self.TURN_RIGHT:
                if card_id == 4:
                    return True   
            elif target_id == self.STOP_MOVING:
                if card_id == 2:
                    return True
        return False
    def card_position(self,index,order=1):
        return self._vision_card(index,order)

    def state_is(self,status):
        return bool(status == self.i2c.read_reg(K210_ADDR,165+4,1)[0])
    
    def motion_command_detected(self,index):
        return bool(index+1 == self.i2c.read_reg(K210_ADDR,165+5,2)[0])
    def motion_speed(self):
        return self.i2c.read_reg(K210_ADDR,165+5,2)[1]
    def custom_command(self):
        return self.i2c.read_reg(K210_ADDR,165,1)[0]
    def joystick_position(self,index):
        buf = self.i2c.read_reg(K210_ADDR,165+7,2)
        if index == self.AXIS_X:
            return buf[0]
        elif index == self.AXIS_Y:
            return buf[1]
        else:
            return 0
    def button_pressed(self,button):
        position = self.i2c.read_reg(K210_ADDR,165+ 0x08,1)[0]
        button_index = 7 - button
        return bool((position >> button_index) & 0x01)
    def key_pressed(self,key):
        position = self.i2c.read_reg(K210_ADDR,165+ 0x09,1)[0]
        key_index = 3 - key
        return bool((position >> key_index) & 0x01)
    def fill_light(self,one):
        self.i2c.write_reg(K210_ADDR, 180, bytes([5]))
        self.i2c.write_reg(K210_ADDR, 180+1, bytes([one]))
    def set_fill_light_brightness(self,brightness):
        self.i2c.write_reg(K210_ADDR, 180, bytes([brightness]))
    def get_fill_light_brightness(self):
        return self.i2c.read_reg(K210_ADDR,180, 1)[0]
vision = Vision()
IO8 = "IO8"
IO9 = "IO9"
IO17 = "IO17"
IO18 = "IO18"
IO19 = "IO19"
IO20 = "IO20"

# IO35 = "IO35"
# IO36 = "IO36"
# IO37 = "IO37"
IO45 = "IO45"
IO46 = "IO46"
IO48 = "IO48"
class EspPin:
    def __init__(self):
        # GPIO 映射表
        self.pin_map = {
            IO8: 8,
            IO9: 9,
            IO17: 17,
            IO18: 18,
            IO19: 19,
            IO20: 20,

            # IO35: 35,
            # IO36: 36,
            # IO37: 37,
            IO45: 45,
            IO46: 46,
            IO48: 48,
        }
        # 缓存对象（核心优化）
        self._pins = {}
        self._pwms = {}
        self._adcs = {}

    def _get_pin(self, pin_name, mode):
        key = (pin_name, mode)
        if key not in self._pins:
            pin_num = self.pin_map[pin_name]
            self._pins[key] = Pin(pin_num, mode)
        return self._pins[key]
    # -------------------------
    # 数字输出
    # -------------------------
    def digitalWrite(self, pin_name, state):
        pin = self._get_pin(pin_name, Pin.OUT)
        pin.value(state)
    # -------------------------
    # 数字输入
    # -------------------------
    def digitalRead(self, pin_name):
        pin = self._get_pin(pin_name, Pin.IN)
        return pin.value()
    # ------------------------
    # PWM 输出
    # -------------------------
    def analogWrite(self, pin_const, duty, freq=1000):
        duty_u16 = int(duty)
        # ---- 2. 创建 PWM ----
        if pin_const not in self._pwms:
            pin = Pin(self.pin_map[pin_const])
            pwm = PWM(pin, freq=freq, duty_u16=duty_u16)
            self._pwms[pin_const] = pwm
        else:
            pwm = self._pwms[pin_const]
            pwm.freq(freq)
            pwm.duty_u16(duty_u16)

    # -------------------------
    # ADC 读取
    # -------------------------
    def analogRead(self, pin_name):
        if pin_name not in self._adcs:
            pin = Pin(self.pin_map[pin_name])
            adc = ADC(pin)
            adc.atten(ADC.ATTN_11DB)
            adc.width(ADC.WIDTH_12BIT)
            self._adcs[pin_name] = adc
        return self._adcs[pin_name].read()
    # -------------------------
    # 脉冲测量（微秒）
    # -------------------------
    def pulseIn(self, pin_name, level=1, timeout=1000000):
        pin = self._get_pin(pin_name, Pin.IN)
        try:
            return time_pulse_us(pin, level, timeout)
        except OSError:
            return None
esp_pin = EspPin() 
class System:
    def __init__(self):
        self.start_time = time.ticks_ms()
    def tick_reset(self):
        self.start_time = time.ticks_ms()
    def tick_get(self):
        return time.ticks_diff(time.ticks_ms(), self.start_time)
    def get_version(self):
        return '0.0.1'
system = System()

class SerialREPL:
    def __init__(self):
        self.poll = uselect.poll()
        self.poll.register(sys.stdin, uselect.POLLIN)
    # 发送字符串
    def write(self, text):
        if text is not None or text == '':
            print(str(text))
    # 是否有数据
    def available(self):
        return len(self.poll.poll(0)) > 0
    # 读取1字节
    def read(self):
        if self.available():
            return sys.stdin.read(1)
        return None
    # 读取一行
    def readline(self):
        if self.available():
            return sys.stdin.readline()
        return None
    # 读取直到分隔符
    def read_until(self, end='\n'):
        data = ""
        while True:
            ch = sys.stdin.read(1)

            if ch == end:
                break
            data += ch
        return data
uart = SerialREPL()
class SD_Card:
    def __init__(self):
        self.spi = spi_bus
    def init(self):
        try:
            self.sd = machine.SDCard(slot=1, spi_bus = self.spi, cs=3,freq=20000000)
            os.mount(self.sd, "/sd")
            return True
        except Exception as e:
            return False
sd_flag = SD_Card().init()

class Audio: 

    def __init__(self):
        esp_audio.audio_init()
        self.music_flag = False
        self.music_start = False
        self.music_task = None

    def get_sound_level(self):
        """读取一次音量，返回0-100"""
        time.sleep(0.02)
        return int(esp_audio.audio_vol_get())
    def start_recording(self,filename,time):
        esp_audio.audio_record(filename, time)
    def play_recording(self,filename):
        self.play_audio(filename)
    async def music_play_task(self, filename):
        self.music_start = True
        self.music_flag = True
        try:
            with open(filename, 'rb') as f:
                f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据
                while self.music_flag:
                    data = f.read(4096)
                    if not data:  # 文件结束时退出
                        break
                    esp_audio.music_play(data)  # 发送音频数据进行播放
                    await asyncio.sleep_ms(1)
        finally:
            self.music_flag = False
            self.music_start = False
            self.music_task = None
            esp_audio.audio_close()
    def parse_wav_header(self,wav_bytes):
        num_channels = int.from_bytes(wav_bytes[22:24], 'little')
        sample_rate = int.from_bytes(wav_bytes[24:28], 'little')
        bits_per_sample = int.from_bytes(wav_bytes[34:36], 'little')
        data_offset = 44
        return num_channels, sample_rate, bits_per_sample, data_offset
    def play_audio(self,filename):
        """
        播放音乐(非阻塞)
        """
        if self.music_flag:
            self.music_flag = False
        while self.music_start:
            time.sleep_ms(1)
        gc.collect()
        try:
            with open(filename, "rb") as f:
                header = f.read(44)
        except OSError as e:
            return False
        channels, sample_rate, bits, offset = self.parse_wav_header(header)
        esp_audio.audio_config(sample_rate, bits, channels)
        esp_audio.audio_open()
        self.music_task = asyncio.create_task(self.music_play_task(filename))
        time.sleep(0.5)
    def stop_sounds(self):
        """
        停止所有声音
        """
        self.music_flag = False
        if self.music_task is not None:
            try:
                self.music_task.cancel()
            except Exception:
                pass
            self.music_task = None
        esp_audio.audio_close()
    def set_volume(self,vol):
        """
        设置喇叭音量
        """
        esp_audio.music_vol_set(vol)
    
    def play_audiono(self,filename):
        """
        播放音乐(阻塞)
        """
        if self.music_flag:
            self.music_flag = False
            time.sleep(0.1)
        self.music_flag = True
        with open(filename, "rb") as f:
            header = f.read(44)
            channels, sample_rate, bits, offset = self.parse_wav_header(header)
        esp_audio.audio_config(sample_rate, bits, channels)
        esp_audio.audio_open()
        with open(filename, 'rb') as f:
            f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
            while self.music_flag:
                data = f.read(1024)
                if not data:  # 文件结束时退出
                    break
                esp_audio.music_play(data)  # 发送音频数据进行播放
                time.sleep_ms(2)
            self.music_flag = False
            esp_audio.audio_close()
audio = Audio()


