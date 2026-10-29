import network,os
import time
import ujson as json
import machine
import ubinascii
from s4s import *
from websocket_client import MyWebsocket

import uasyncio as asyncio
from esp32 import NVS
import version

_ORIGINAL_PRINT = print


def save_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    file_obj = kwargs.get("file", None)
    text = sep.join(str(arg) for arg in args)
    if text:
        message = text + end
    else:
        message = end

    try:
        with open("print_log.txt", "a") as log_file:
            log_file.write(message)
    except Exception:
        pass

    if file_obj is not None:
        try:
            if hasattr(file_obj, "write"):
                file_obj.write(text + end)
        except Exception:
            pass
    else:
        try:
            _ORIGINAL_PRINT(*args, **kwargs)
        except Exception:
            try:
                _ORIGINAL_PRINT(*args)
            except Exception:
                pass


try:
    import builtins
    if isinstance(builtins, dict):
        builtins["print"] = save_print
    else:
        builtins.print = save_print
except Exception:
    pass

print = save_print


async def execute_file(code):
    try:

        user_code = """
import uasyncio as asyncio

"""
        user_code += code + "\n"
        exec(
            user_code,
            REPL_GLOBALS,
            REPL_GLOBALS
        )

        if "main" in REPL_GLOBALS:
            await REPL_GLOBALS["main"]()

    except Exception as e:
        print("user error:", e)
def get_mac():
    mac = machine.unique_id()
    return ubinascii.hexlify(mac).decode().upper()

def get_device_info():
    return {
        "version": version.version
    }

file_id = None
opt = 0
SERVER = load_config().get("websocket")
REPL_GLOBALS = {}
USER_CALLBACKS = {}
nvs = NVS("mode")
try:
    opt = nvs.get_i32("opt")
except OSError as e:
    nvs.set_i32("opt", opt)
    nvs.commit()

def power_check_once():
    try:
        charge_state = device.is_charge()
        battary = device.battery()
        if battary < 0:
            if display.s4s_state.charging:
                display.s4s_state.charging = False
                display.s4s_state.charging_flag = True
            if display.s4s_state.power:
                display.s4s_state.power = False
                display.s4s_state.power_flag = True
        else:
            if display.s4s_state.charging:
                if not charge_state:
                    display.s4s_state.charging = False
                    display.s4s_state.charging_flag = True
            else:
                if charge_state:
                    display.s4s_state.charging = True
                    display.s4s_state.charging_flag = True
            if not display.s4s_state.power:
                display.s4s_state.power = True
                display.s4s_state.power_flag = True
                display.s4s_state.power_num = battary
                display.s4s_state.power_num_flag = True
            else:
                display.s4s_state.power_num = battary
                display.s4s_state.power_num_flag = True
    except Exception as e:
        pass

last_power_check = time.ticks_ms()

wlan_global = None

def init_wifi():
    global wlan_global
    cfg = load_config()
    wifi_cfg = cfg.get("wifi", {}) if isinstance(cfg, dict) else {}
    ssid = wifi_cfg.get("ssid")
    pwd = wifi_cfg.get("pswd")
    
    if not ssid or (isinstance(ssid, str) and not ssid.strip()):
        display.s4s_state.wifi_flag = True
        display.s4s_state.wifi = False
        return
    
    wlan_global = network.WLAN(network.STA_IF)
    wlan_global.active(True)
    
    if not wlan_global.isconnected():
        try:
            wlan_global.connect(ssid, pwd)
        except Exception as e:
            display.s4s_state.wifi_flag = True
            display.s4s_state.wifi = False

    else:
        display.s4s_state.wifi_flag = True
        display.s4s_state.wifi = True

def wifi_check_once():
    global wlan_global
    try:
        if wlan_global is None:
            return
        
        is_connected = wlan_global.isconnected()
        if is_connected:
            if not display.s4s_state.wifi:
                display.s4s_state.wifi_flag = True
                display.s4s_state.wifi = True

        else:
            if display.s4s_state.wifi:
                display.s4s_state.wifi = False
                display.s4s_state.wifi_flag = True
                
    except Exception as e:
        display.s4s_state.wifi = False
        display.s4s_state.wifi_flag = True

def repl_exec(code):
    try:
        result = eval(code,REPL_GLOBALS,REPL_GLOBALS)
        return {
            "success": True,
            "output": str(result)
        }
    except SyntaxError:
        try:
            exec(code,REPL_GLOBALS,REPL_GLOBALS)
            return {
                "success": True,
                "output": str(
                    REPL_GLOBALS.get("result", "")
                )
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e)
            }
    except Exception as e:
        return {
            "success": False,
            "output": str(e)
        }   

def update_program_slot(slot, program_name):
    """
    修改指定坑位
    slot: 坑位号 0~5
    program_name: 程序名
    """

    # 读取原来的6个坑位
    files = []
    try:
        with open("program/program.txt", "r") as f:
            files = [line.strip() for line in f.readlines()]
    except:
        files = []

    # 保证6个坑位
    while len(files) < 6:
        files.append("")
    # 修改指定坑位
    if 0 <= slot < 6:
        files[slot] = program_name

    # 写回
    with open("program/program.txt", "w") as f:
        for name in files[:6]:
            f.write(name + "\n")
async def main_task():
    global repl_exec,file_id
    init_wifi()
    while True:
        ws = None
        try:
            try:
                now = time.ticks_ms()
                if time.ticks_diff(now, last_power_check) >= 1000:
                    power_check_once()
                    wifi_check_once()
                    last_power_check = now
            except Exception:
                # 忽略时间计算问题
                last_power_check = time.ticks_ms()
            ws = MyWebsocket(SERVER)
            ws.connect()
            ws.send(json.dumps({
                "type": "handshake",
                "mac": get_mac()
            }))
            resp_msg = ws.recv(timeout_ms=5000)
            if resp_msg is None:
                raise Exception("handshake timeout")
            resp = json.loads(resp_msg)
            display.s4s_state.code_flag=True
            display.s4s_state.code=resp.get('connKey')
            display.s4s_state.server_flag=True
            display.s4s_state.server=True
            while True:
                msg = ws.recv(timeout_ms=0)
                if msg is not None:
                    try:
                        data = json.loads(msg)
                    except Exception as e:
                        data = None
                    if data:
                        print(data)
                        msg_type = data.get("type")
                        if msg_type == "get_device_info":
                            ws.send(json.dumps({
                                "type": "device_info",
                                "requestId": data["requestId"],
                                "payload": get_device_info()
                            }))
                        elif msg_type == "run_code":
                            if "requestId" in data:
                                if file_id is not None:
                                    try:
                                        file_id.cancel()
                                    except Exception:
                                        pass
                                    file_id = None
                                result = repl_exec(
                                    data.get("payload", {}).get("code", "")
                                )
                                ws.send(json.dumps({
                                    "type": "rpc_result",
                                    "requestId": data["requestId"],
                                    "payload": result
                                }))
                            else:
                                code = data.get("payload", {}).get("code", "")
                                with open("user_run.py", "w") as f:
                                    f.write(code)
                                nvs.set_i32("opt", 2)
                                nvs.commit()
                                restart()
                        elif msg_type == "upload_code":
                            upload_data = data.get("payload", {})
                            slot = upload_data.get("slot", "")
                            projectName = upload_data.get("projectName", "")
                            
                            code = upload_data.get("code", "")

                            with open("py/user_code.py", "w") as f:
                                f.write(code)
                            with open("program/"+projectName, "w") as f:
                                f.write(code)
                            update_program_slot(int(slot)-1,projectName)
                            nvs.set_i32("opt", 1)
                            nvs.commit()
                            restart()
                        elif msg_type == "exec_get":
                            result = repl_exec(data.get("payload", {}).get("func", ""))
                            result = json.dumps({
                                "type": "exec_get",
                                "requestId": data["requestId"],
                                "payload": result
                            })
                            ws.send(result)
                        elif msg_type == "exec":
                            result = repl_exec(data.get("payload", {}).get("func", ""))
                try:
                    now = time.ticks_ms()
                    if time.ticks_diff(now, last_power_check) >= 1000:
                        power_check_once()
                        wifi_check_once()
                        last_power_check = now
                except Exception:
                    # 忽略时间计算问题
                    last_power_check = time.ticks_ms()

                await asyncio.sleep_ms(1)

        except Exception as e:
            display.s4s_state.server_flag=True
            display.s4s_state.server=False
            try:
                ws.close()
            except:
                pass
            await asyncio.sleep_ms(3000)


if opt == 2:
    display.display.set_backlight(100)
    try:
        with open("user_run.py", "r") as f:
            code = f.read()
            os.remove("user_run.py")
            opt = 0
            nvs.set_i32("opt", 0)
            nvs.commit()
        file_id = asyncio.create_task(execute_file(code))
        
    except Exception as e:
        opt = 0
        nvs.set_i32("opt", 0)
        nvs.commit()
    asyncio.run(main_task())
if opt == 0:
    exec("from s4s import *", REPL_GLOBALS, REPL_GLOBALS)
    try:
        display.init()
    except Exception as e:
        print("failed:", e)
    asyncio.run(main_task())
if opt == 1:
    opt = 0
    nvs.set_i32("opt", 0)
    nvs.commit()
    display.display.set_backlight(100)
    try:
        with open("py/user_code.py", "r") as f:
            code = f.read()
        file_id = asyncio.create_task(execute_file(code))
    except Exception as e:
        print(e)
    asyncio.run(main_task())
    