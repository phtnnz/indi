#!/usr/bin/env python3

# Copyright 2024-2026 Martin Junius
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ChangeLog
# Version 0.1 / 2026-06-19
#       New version of capture script for ASI 120 MM
#       TEST --- NOT YET WORKING!!!

# Standard library
import sys
import argparse
import time
import threading

# Extra modules, not part of standard library, on Ubuntu install via apt-get
import PyIndi
from astropy.io import fits
import cv2
import numpy as np
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, warning, error


VERSION = "0.1 / 2026-06-19"
AUTHOR  = "Martin Junius"
NAME    = "asi120-capture"
DESC    = "INDI client, capture frame from ASI120MM"

# INDI timeout for getXXX() functions (seconds)
TIMEOUT = 0.1
# Default server:port
HOST    = "localhost"
PORT    = 7624



# ASI 120 MM:
#   gain 0 ... 100
#   offset 0 ... 1000

# Command line options
class Options:
    camera   = "ZWO CCD ASI120MM"           # -c --camera
    gain     = 0                            # -g --gain         0 ... 100
    offset   = 0                            # -o --offset       0 ... 100
    exposure = 0.1                          # -e --exposure
    binning  = 2                            # -b --binning



# IndiClient class which inherits from the module PyIndi.BaseClient class
class IndiClient(PyIndi.BaseClient):
    def __init__(self, host=HOST, port=PORT):
        super(IndiClient, self).__init__()
        verbose(f"creating an instance of IndiClient, server {host}:{port}")
        self.setServer(host, port)
        if not self.connectServer():
            error("can't connect to indiserver")


    def newDevice(self, d):
        """Emmited when a new device is created from INDI server."""
        verbose(f"new device {d.getDeviceName()}")

    def removeDevice(self, d):
        """Emmited when a device is deleted from INDI server."""
        verbose(f"remove device {d.getDeviceName()}")

    def newProperty(self, p):
        """Emmited when a new property is created for an INDI driver."""
        verbose(
            f"new property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def updateProperty(self, p):
        """Emmited when a new property value arrives from INDI server."""
        verbose(
            f"update property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def removeProperty(self, p):
        """Emmited when a property is deleted for an INDI driver."""
        verbose(
            f"remove property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def newMessage(self, d, m):
        """Emmited when a new message arrives from INDI server."""
        verbose(f"new Message {d.messageQueue(m)}")

    def serverConnected(self):
        """Emmited when the server is connected."""
        verbose(f"server connected ({self.getHost()}:{self.getPort()})")

    def serverDisconnected(self, code):
        """Emmited when the server gets disconnected."""
        verbose(
            f"server disconnected (exit code = {code}, {self.getHost()}:{self.getPort()})"
        )

    def updateProperty(self, prop):
        """Emmited when a new property value arrives from INDI server."""
        verbose(f"update property {prop.getName()} as {prop.getTypeAsString()} for device {prop.getDeviceName()}")



    # Refactored from main()
    def verboseDevices(self):
        # list devices
        while not (deviceList := self.getDevices()):
            time.sleep(TIMEOUT)
        for device in deviceList:
            verbose(f"device found: {device.getDeviceName()}")


    # Connect camera and debug properties
    def CCDconnect(self, ccd):
        # Connect camera
        while not (device_ccd := self.getDevice(ccd)):
            time.sleep(TIMEOUT)
        self.device_ccd = device_ccd

        while not (ccd_connect := device_ccd.getSwitch("CONNECTION")):
            time.sleep(TIMEOUT)
        if not device_ccd.isConnected():
            ccd_connect.reset()
            ccd_connect[0].setState(PyIndi.ISS_ON)  # the "CONNECT" switch
            self.sendNewProperty(ccd_connect)

        self.ccd_controls = device_ccd.getNumber("CCD_CONTROLS")
        self.ic_prop_number(self.ccd_controls)
        self.ccd_gain = self.ccd_controls[0]
        self.ccd_offset = self.ccd_controls[1]
        self.ccd_bandwidth = self.ccd_controls[2]

        self.ccd_binning = device_ccd.getNumber("CCD_BINNING")
        self.ic_prop_number(self.ccd_binning)

        self.ccd_info = device_ccd.getNumber("CCD_INFO")
        self.ic_prop_number(self.ccd_info)

        self.ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
        self.ic_prop_number(self.ccd_exposure)

        self.ccd_capture_format = device_ccd.getSwitch("CCD_CAPTURE_FORMAT")
        self.ic_prop_switch(self.ccd_capture_format)

        self.ccd_transfer_format = device_ccd.getSwitch("CCD_TRANSFER_FORMAT")
        self.ic_prop_switch(self.ccd_transfer_format)

        self.ccd1 = device_ccd.getBLOB("CCD1")
        self.ic_prop_blob(self.ccd1)

        self.upload_mode = device_ccd.getSwitch("UPLOAD_MODE")
        self.ic_prop_switch(self.upload_mode)


        self.list_properties(device_ccd)


    def ic_prop_number(self, prop_list):
        ic("---------------------------------------")
        for i, w in enumerate(prop_list):
            ic(prop_list.getName(), i, w.getName(), w.getValue())

    def ic_prop_switch(self, prop_list):
        ic("---------------------------------------")
        for i, w in enumerate(prop_list):
            ic(prop_list.getName(), i, w.getName(), w.getStateAsString())

    def ic_prop_blob(self, prop_list):
        ic("---------------------------------------")
        for i, w in enumerate(prop_list):
            ic(prop_list.getName(), i, w.getName(), w.getSize())


    def list_properties(self, device):
        print(f"-- {device.getDeviceName()}")
        prop_list = device.getProperties()

        for prop in prop_list:
            print(f"   > {prop.getName()} {prop.getTypeAsString()}")

            if prop.getType() == PyIndi.INDI_TEXT:
                for widget in PyIndi.PropertyText(prop):
                    print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getText()}    (TEXT)")

            if prop.getType() == PyIndi.INDI_NUMBER:
                for widget in PyIndi.PropertyNumber(prop):
                    print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getValue()}    (NUMBER)")

            if prop.getType() == PyIndi.INDI_SWITCH:
                for widget in PyIndi.PropertySwitch(prop):
                    print(f"       {widget.getName()}({widget.getLabel()}) = {widget.getStateAsString()}    (SWITCH)")

            if prop.getType() == PyIndi.INDI_LIGHT:
                for widget in PyIndi.PropertyLight(prop):
                    print(f"       {widget.getLabel()}({widget.getLabel()}) = {widget.getStateAsString()}    (LIGHT)")

            if prop.getType() == PyIndi.INDI_BLOB:
                for widget in PyIndi.PropertyBlob(prop):
                    print(f"       {widget.getName()}({widget.getLabel()}) = <blob {widget.getSize()} bytes>    (BLOB)")



    def verboseCCDAttr(self):
        # IndiClient._verbose_list("CCD exposure", self.ccd_exposure)
        # IndiClient._verbose_list("CCD binning",  self.ccd_binning)
        # IndiClient._verbose_list("CCD gain",     self.ccd_gain)
        # IndiClient._verbose_list("CCD offset",   self.ccd_offset)
        # IndiClient._verbose_list("CCD info",     self.ccd_info)
        ...



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESC,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-c", "--camera", help="camera name")
    arg.add_argument("-g", "--gain", type=int, help="camera gain")
    arg.add_argument("-o", "--offset", type=int, help="camera offset")
    arg.add_argument("-b", "--binning", type=int, help="camera binning, 1 (1x1) or 2 (2x2)")
    arg.add_argument("-e", "--exposure", type=float, help="camera exposure time/s")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info)
        ic(args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    # ... more options ...
    if args.camera:
        Options.camera = args.camera
    if args.gain:
        Options.gain  = args.gain
    if args.offset:
        Options.offset  = args.offset
    if args.binning:
        Options.binning  = args.binning
        if Options.binning != 1 and Options.binning != 2:
            error("argument -b/--binning: must be 1 or 2")
    if args.exposure:
        Options.exposure = float(args.exposure)
        if Options.exposure <= 0:
            error("argument -e/--exposure: must be > 0")
        
    # Connect to the server
    indi = IndiClient("localhost", 7624)

    # List devices
    verbose(">>> List devices")
    indi.verboseDevices()

    # Connect camera
    verbose(">>> Connect camera")
    indi.CCDconnect(Options.camera)
    verbose(">>> Attributes")
    indi.verboseCCDAttr()

    # Disconnect from the indiserver
    indi.disconnectServer()



if __name__ == "__main__":
    main()
