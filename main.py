import sys
import glob
import serial
import argparse
import dataclasses
import datetime
import os

# LOGGER INTERVAL IN SECONDS
LOGGER_INTERVAL = 60
last_update = datetime.datetime.now().replace(microsecond=0)
filename = datetime.datetime.now().strftime("%y_%m_%d_%H")
header = ["time", "temp - C", "pH"]


@dataclasses.dataclass
class logger_data:
    temp: float
    ph: float


last_data = logger_data(None, None)


def list_serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def write_to_file(data, units):
    if units == "°C":
        last_data.temp = data
    elif units == "pH":
        last_data.ph = data

    # check current time vs last update
    # if time since last update is greater than LOGGER_INTERVAL
    # then write to file
    current_time = datetime.datetime.now().replace(microsecond=0)
    if (current_time - last_update).seconds > LOGGER_INTERVAL:
        last_update + datetime.timedelta(0, LOGGER_INTERVAL)
        with open(f"{filename}.csv", "a") as f:
            f.write(f"{last_update},{last_data.temp},{last_data.ph}\n")


def print_serial(name):
    serial_port = serial.Serial(name, 115200)
    print(f"The Port name is {serial_port.name}")
    units = ""
    value = ""

    with open(f"{filename}.csv", "w") as f:
        f.write(",".join(header) + "\n")

    # discard first 10 lines
    for i in range(10):
        byte_line = serial_port.readline()

    while True:
        byte_line = serial_port.readline()
        line = byte_line.decode("utf-8").strip()
        if line.startswith("upper") or line.startswith("lower"):
            units = line.split(" ")[1]
        else:
            value = line

        print(value, units)
        write_to_file(value, units)


if __name__ == "__main__":
    print("Please plug in or unplug and replug the device now")
    old_ports = list_serial_ports()
    new_ports = list_serial_ports()
    while len(old_ports) >= len(new_ports):
        # if device is plugged in
        # then unplugged, the list will be shorter
        if len(new_ports) < len(old_ports):
            old_ports = list_serial_ports()
        new_ports = list_serial_ports()

    print("Device plugged in")
    dev = list(set(new_ports) - set(old_ports))
    print_serial(dev[0])
