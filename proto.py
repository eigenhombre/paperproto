#!/usr/bin/env python

# Device-dependent imports:
from PIL import Image, ImageDraw, ImageFont
import os
import re
import socket
import subprocess
import sys
import time
import warnings


def get_hostname():
    return socket.gethostname().lower()


hostname = get_hostname()

if hostname == "pion":
    is_pi = True
else:
    is_pi = False

pi_parent_dir = "/home/rpi/e-Paper/RaspberryPi_JetsonNano/python"

if is_pi:
    sys.path.append(os.path.join(pi_parent_dir, "lib"))
    # Suppress warnings about GPIO:
    with warnings.catch_warnings(action="ignore"):
        from waveshare_epd import epd2in13_V4


# Set up fonts:
if is_pi:
    picdir = os.path.join(pi_parent_dir, "pic")
    font24 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 24)
    font14 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 14)
else:
    font24 = ImageFont.truetype("Font.ttc", 24)
    font14 = ImageFont.truetype("Font.ttc", 14)


def get_temp():
    # Prototype: get with /usr/bin/vcgencmd measure_temp
    if is_pi:
        tempstr = subprocess.check_output(
            "/usr/bin/vcgencmd measure_temp", shell=True
        ).decode("utf-8")
    else:
        tempstr = "temp=38.1'C"

    number_val = re.search(r"temp\=(\d+\.\d+)'C", tempstr)
    if number_val:
        return number_val.group(1) + " C"
    return "NO TEMP"


# This works on either platform:
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip_address = s.getsockname()[0]
        s.close()
        return local_ip_address
    except Exception as e:
        return f"Error: {e}"


def get_mem():
    if is_pi:
        memstr = subprocess.check_output("free", shell=True).decode("utf-8")
    else:
        # Memory: get with `free`:
        memstr = """
                    total        used        free      shared  buff/cache   available
        Mem:          436980      109240      213468         948      166464      327740
        Swap:         102396           0      102396
        """

    match = re.search(r"Mem:\s+(\d+)\s+(\d+)\s+(\d+)", memstr)
    if not match:
        return "NO MEM"
    used = int(match.group(2))
    total = int(match.group(1))
    used_percent = int(used / total * 100)
    return f"{used_percent}%"


def get_uptime():
    if is_pi:
        uptimestr = subprocess.check_output("cat /proc/uptime", shell=True).decode(
            "utf-8"
        )
    else:
        uptimestr = """
        4544.69 18031.09
        """
    match = re.search(r"(\d+\.\d+)\s+(\d+\.\d+)", uptimestr)
    if not match:
        return "NO UPTIME"
    total_seconds = float(match.group(1))
    idle_cores = float(match.group(2))
    up_days = float(total_seconds / 86400)
    active_percent = float((1 - idle_cores / (4 * total_seconds)) * 100)
    return f"{up_days:.2f}d, active {active_percent:.2f}%"


def get_wifi_strength():
    if is_pi:
        wifistr = subprocess.check_output(
            "/usr/sbin/iwconfig wlan0", shell=True
        ).decode("utf-8")
    else:
        wifistr = """
        wlan0     IEEE 802.11  ESSID:"CornellCroft"
                  Mode:Managed  Frequency:2.437 GHz  Access Point: F4:92:BF:7F:55:E4
                  Bit Rate=72.2 Mb/s   Tx-Power=31 dBm
                  Retry short limit:7   RTS thr:off   Fragment thr:off
                  Power Management:on
                  Link Quality=64/70  Signal level=-46 dBm
                  Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
                  Tx excessive retries:1  Invalid misc:0   Missed beacon:0
        """
    match = re.search(r"Link Quality=(\d+)/(\d+).+Signal level=(-\d+) dBm", wifistr)
    if not match:
        return "NO WIFI"
    return f"{match.group(1)}/{match.group(2)} {match.group(3)} dBm"


def get_disk():
    if is_pi:
        diskstr = subprocess.check_output("df -k", shell=True).decode("utf-8")
    else:
        diskstr = """
Filesystem     1K-blocks    Used Available Use% Mounted on
udev               81736       0     81736   0% /dev
tmpfs              43700     932     42768   3% /run
/dev/mmcblk0p2 122364296 4306628 111824324   4% /
tmpfs             218488       0    218488   0% /dev/shm
tmpfs               5120       8      5112   1% /run/lock
/dev/mmcblk0p1    522232   95702    426530  19% /boot/firmware
tmpfs              43696       0     43696   0% /run/user/1000
"""
    lines = diskstr.split("\n")
    # Find line ending in "/\s*":
    [line] = [line for line in lines if re.search(r"/\s*$", line)]

    (dev, total, used, avail, percent, mount, *_) = line.split()
    return f"{int(used)//1000000}G/{int(total)//1000000}G {percent}"


def get_datetime():
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


fields = [
    [None, get_hostname(), font24, [0, 0]],
    [None, get_ip_address(), font14, [0, 40]],
    ["WiFi", get_wifi_strength(), font14, [120, 40]],
    [None, get_datetime(), font14, [0, 60]],
    ["Mem", get_mem(), font14, [120, 60]],
    ["Disk", get_disk(), font14, [0, 80]],
    [None, get_temp(), font14, [120, 80]],
    ["Up", get_uptime(), font14, [0, 100]],
]


def main():
    if is_pi:
        epd = epd2in13_V4.EPD()
        epd.init()
        epd.Clear(0xFF)
    try:
        image = Image.new("1", (250, 122), 255)
        draw = ImageDraw.Draw(image)
        for name, field, font, (x, y) in fields:
            print(name, field, x, y)
            if name:
                draw.text((x, y), f"{name} {field}", font=font, fill=0)
            else:
                draw.text((x, y), f"{field}", font=font, fill=0)
        if is_pi:
            epd.display(epd.getbuffer(image))
        else:
            image.save("proto.png")
            time.sleep(0.5)
            print(subprocess.Popen("killall Preview", shell=True))
            time.sleep(0.5)
            print(subprocess.Popen("open -g proto.png", shell=True))
        if is_pi:
            epd.sleep()
    except KeyboardInterrupt:
        if is_pi:
            epd2in13_V4.epdconfig.module_exit()
        print()
        print("OK")


if __name__ == "__main__":
    main()
