from serial import Serial, SerialException
from sys import stderr, exit
from gi.repository import Gtk
from exceptions import *
import logging

class Device:

    def __init__(self, address, timeout, bitrate):
        try:
            self.device = Serial(address, bitrate)
            self.device.timeout = timeout
        except SerialException:
            stderr.write("Error connecting to " + address + ".\n")
            #self.errorMessage("Error connecting", "Problems connecting with " + address)
            exit(1)
            
    def get_data(self):
        self.send_command(b"\xFF\x16\x00\x00\x1A\x00\x0C")
        raw_data = self.read_input(55)#27)
        if raw_data != None:
            data = self.parse_data(raw_data)
            return data
        else:
            return None

    def reset_rsoc(self):
        self.send_command(b"\xFF\x13\x05\x00\x00\x64\x72")
        raw_data = self.read_input(3)
        return True

    def send_command(self, command):
        logging.debug("Send command: "+str(command))
        self.device.write(command)

    def read_input(self, size):
        raw_data = self.device.read(size)
        logging.debug("Receive data: "+str(raw_data))
        if len(raw_data) != 0:
            if not self.ack(raw_data):
                raise ACKError(raw_data[1])
            elif not self.crc(raw_data):
                raise CRCError(raw_data[-1])
            elif size != len(raw_data):
                raise sizeError(len(raw_data))
            else:
                return raw_data
        else:
            raise timeoutError("Timeout finished")
        return None

    def parse_data(self, raw_data):
        logging.debug("Raw data to parse: " + str(raw_data))
        data = {}
        data['voltage'] = (raw_data[7] << 8) + raw_data[6]
        #konp_balioa = b"\xFF\xFF"
        if raw_data[9] > 160:
                data['current'] = ((65535 - ((raw_data[9] << 8) + raw_data[8]) + 1)*100)*-1
        else:
            data['current'] = ((raw_data[9] << 8) + raw_data[8])*100
        if raw_data[19] > 160:
            data['avg_current'] = ((65535 - ((raw_data[19] << 8) + raw_data[18]) + 1)*100)*-1
        else:
            data['avg_current'] = ((raw_data[19] << 8) + raw_data[18])*100
        data['temperature'] = (raw_data[5] << 8) + raw_data[4]
        data['rsoc'] = (raw_data[25] << 8) + raw_data[24]
        return data

    def crc(self, data):
        result = 0
        for c in data[1:-1]:
            result = result ^ c
        print(result)
        print(data)
        return result == data[-1]

    def ack(self, data):
        return data[1] == 33
