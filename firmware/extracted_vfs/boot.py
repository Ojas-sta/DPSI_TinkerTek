# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import os


def is_firmware_present(fs_path="/main_board_bin"):
    try:
        files = os.listdir(fs_path)
    except OSError as e:
        return None

    if files:
        filename = files[0]
        return fs_path + "/" + filename
    else:
        return None
filename = is_firmware_present()
if filename is not None:
    from xmodem import *
    flag = xmodem_send_file(filename)
    if flag:
        try:
            os.remove(filename)
            print("firmware deleted")
        except:
            print("delete failed")
    from machine import reset
    reset()