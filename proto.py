#!/usr/bin/env python

from PIL import Image, ImageDraw, ImageFont
import socket
import subprocess
from time import sleep
import re


# Prototype: get with /usr/bin/vcgencmd measure_temp
tempstr = "temp=38.1'C"


def get_temp():
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


# Memory: get with `free`:
memstr = """
               total        used        free      shared  buff/cache   available
Mem:          436980      109240      213468         948      166464      327740
Swap:         102396           0      102396
"""


def get_mem():
    match = re.search(r"Mem:\s+(\d+)\s+(\d+)\s+(\d+)", memstr)
    if not match:
        return "NO MEM"
    used = int(match.group(2))
    total = int(match.group(1))
    used_percent = int(used / total * 100)
    return f"{used_percent}%"


font14 = ImageFont.truetype("Font.ttc", 14)

fields = [
    [None, get_ip_address(), font14, [10, 10]],
    [None, get_temp(), font14, [10, 30]],
    ["Mem", get_mem(), font14, [10, 50]],
]


def main():
    get_temp()
    # Make a 250 × 122 image:
    image = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(image)
    for name, field, font, (x, y) in fields:
        print(name, field, x, y)
        if name:
            draw.text((x, y), f"{name} {field}", font=font, fill=0)
        else:
            draw.text((x, y), f"{field}", font=font, fill=0)

    # Draw the image on the screen
    #         #
    # image.show()
    # Write image to a file (PNG):
    # delete old image

    image.save("proto.png")

    print(subprocess.Popen("killall Preview", shell=True))
    sleep(0.5)
    print(subprocess.Popen("open -g proto.png", shell=True))
    print("OK")


if __name__ == "__main__":
    main()
