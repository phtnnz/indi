#!/usr/bin/env python3

# Copyright 2024 Martin Junius
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
# Version 0.1 / 2024-05-14
#       First version based on qhy5-capture
# Versopm 0.2 / 2024-05-15
#       Auto-exposure implemented

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


VERSION = "0.2 / 2024-05-15"
AUTHOR  = "Martin Junius"
NAME    = "qhy5-auto"
DESC    = "INDI client, capture frames from QHY5L with auto-exposure"

# INDI timeout for getXXX() functions (seconds)
TIMEOUT = 0.1
# Default server:port
HOST    = "localhost"
PORT    = 7624
# Max numbers of auto-exposure attempts
MAXTRY  = 15
# Expected mean ADU (0..255) and deviation
MEANADU = 128
DEVADU  = 20
EXPOSURE_THRESHOLD = 1.0 # s


# QHY 5L II mono:
#   gain 1 ... 29
#   offset 1 ... 512; +100 -> ~+25 ADU min value
MINGAIN   = 1
MAXGAIN   = 29
STEPGAIN  = 4
MINOFFSET = 1
MAXOFFSET = 512

# Command line options
class Options:
    camera   = "QHY CCD QHY5LII-M-6077d"    # -c --camera
    gain     = MINGAIN                      # -g --gain         1 ... 29
    offset   = MINOFFSET                    # -o --offset       1 ... 512
    exposure = 0.5                          # -e --exposure
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
        # verbose(
        #     f"new property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        # )

    # def updateProperty(self, p):
    #     """Emmited when a new property value arrives from INDI server."""
    #     verbose(
    #         f"update property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
    #     )

    def removeProperty(self, p):
        """Emmited when a property is deleted for an INDI driver."""
        # verbose(
        #     f"remove property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        # )

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
        # verbose(f"update property {prop.getName()} as {prop.getTypeAsString()} for device {prop.getDeviceName()}")
        global blobEvent
        if prop.getType() == PyIndi.INDI_BLOB:
            ic(prop.getName())
            blobEvent.set()


    # Refactored from main()
    def verboseDevices(self):
        # list devices
        while not (deviceList := self.getDevices()):
            time.sleep(TIMEOUT)
        for device in deviceList:
            verbose(f"device found: {device.getDeviceName()}")


    def getCCDAttr(self, name):
        while not (attr := self.device_ccd.getNumber(name)):
            time.sleep(TIMEOUT)
        return attr
            

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

        self.ccd_exposure = self.getCCDAttr("CCD_EXPOSURE")
        self.ccd_binning  = self.getCCDAttr("CCD_BINNING")
        self.ccd_gain     = self.getCCDAttr("CCD_GAIN")
        self.ccd_offset   = self.getCCDAttr("CCD_OFFSET")
        self.ccd_info     = self.getCCDAttr("CCD_INFO")

        self.current_binning  = Options.binning
        self.current_gain     = Options.gain 
        self.current_offset   = Options.offset 
        self.current_exposure = Options.exposure 

        # inform the indi server that we want to receive the "CCD1" blob from this device
        self.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")
        while not (ccd_ccd1 := device_ccd.getBLOB("CCD1")):
            time.sleep(TIMEOUT)
        self.ccd_ccd1 = ccd_ccd1

        # we use here the threading.Event facility of Python
        global blobEvent
        blobEvent = threading.Event()


    def CCDcapture(self):
        # set gain and offset
        self.ccd_gain[0].setValue(self.current_gain)
        self.sendNewProperty(self.ccd_gain)
        self.ccd_offset[0].setValue(self.current_offset)
        self.sendNewProperty(self.ccd_offset)
        # set binning
        self.ccd_binning[0].setValue(self.current_binning)
        self.ccd_binning[1].setValue(self.current_binning)
        self.sendNewProperty(self.ccd_binning)

        # start exposure
        blobEvent.clear()
        self.ccd_exposure[0].setValue(self.current_exposure)
        self.sendNewProperty(self.ccd_exposure)

        # self.verboseCCDAttr()


    def CCDgetImg(self):
        # wait for exposure(s)
        blobEvent.wait()
        # seems to help with early terminate errors
        time.sleep(0.1)

        # process the received one
        for blob in self.ccd_ccd1:
            verbose(
                "name: ",
                blob.getName(),
                " size: ",
                blob.getSize(),
                " format: ",
                blob.getFormat(),
            )
            fitsdata = blob.getblobdata()
            # print("fits data type: ", type(fitsdata))

            # Directly convert bytearray to FITS
            hdul = fits.HDUList.fromstring(bytes(fitsdata))
            # hdul.info()
            imgdata = hdul[0].data

            return imgdata
    

    def CCDsaveImg(self):
        img = self.CCDgetImg()
        self.CCDwriteImg(img)


    def CCDwriteImg(self, img):
        # Normalize to 0 .. 255
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        # FIXME: file name handling
        cv2.imwrite("blob.jpg", img)


    def CCDauto(self):
        count = MAXTRY
        low   = MEANADU - DEVADU
        high  = MEANADU + DEVADU
        img   = None
        last_exp_inc = False
        last_exp_dec = False
        last_gain_inc = False
        last_gain_dec = False

        while count > 0:
            ic("--- ITERATION ---")
            ic(count, self.current_gain, self.current_offset, self.current_exposure)
            count -= 1
            self.CCDcapture()
            img = self.CCDgetImg()
            mean = np.average(img)
            min  = np.min(img)
            ic(low, high, mean, min)
            if mean >= high:
                # exposure too bright
                if self.current_exposure <= EXPOSURE_THRESHOLD and self.current_gain > MINGAIN and not last_gain_inc:
                    self.current_gain -= STEPGAIN
                    if self.current_gain < MINGAIN: self.current_gain = MINGAIN
                    last_gain_dec = True
                else:
                    self.current_exposure /= 1.4 if last_exp_inc else 2
                    last_exp_dec = True
                    last_gain_dec = False
                ic("too bright, new exposure:")
                ic(self.current_exposure, self.current_gain)
            elif mean <= low:
                # exposure too dark
                if self.current_exposure >= EXPOSURE_THRESHOLD and self.current_gain < MAXGAIN and not last_gain_dec:
                    self.current_gain += STEPGAIN
                    if self.current_gain > MAXGAIN: self.current_gain = MAXGAIN
                    last_gain_inc = True
                else:
                    self.current_exposure *= 1.4 if last_exp_dec else 2
                    last_gain_inc = False
                    last_exp_inc  = True
                ic("too dark, new exposure:")
                ic(self.current_exposure, self.current_gain)
            else:
                # exposure ok
                ic("ok, saving image")
                break

        verbose(f"auto-exposure {self.current_exposure:.3f}s gain={self.current_gain} mean={mean:.0f}")
        self.CCDwriteImg(img)


    def _verbose_list(name, list):
        for i in list:
            verbose(name+":", i.getName(), "=", i.getValue())


    def verboseCCDAttr(self):
        IndiClient._verbose_list("CCD exposure", self.ccd_exposure)
        IndiClient._verbose_list("CCD binning",  self.ccd_binning)
        IndiClient._verbose_list("CCD gain",     self.ccd_gain)
        IndiClient._verbose_list("CCD offset",   self.ccd_offset)
        # IndiClient._verbose_list("CCD info",     self.ccd_info)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESC,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-c", "--camera", help=f"camera name (default {Options.camera})")
    arg.add_argument("-g", "--gain", type=int, help=f"initial camera gain (default: {Options.gain})")
    arg.add_argument("-o", "--offset", type=int, help=f"initial camera offset (default: {Options.offset})")
    arg.add_argument("-b", "--binning", type=int, help=f"initial camera binning, 1 (1x1) or 2 (2x2) (default: {Options.binning})")
    arg.add_argument("-e", "--exposure", type=float, help=f"initial camera exposure time/s (default: {Options.exposure})")

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
    # indi.verboseDevices()

    # Connect camera
    indi.CCDconnect(Options.camera)
    # indi.CCDcapture()
    # indi.CCDsaveImg()
    indi.CCDauto()

    # Disconnect from the indiserver
    indi.disconnectServer()



if __name__ == "__main__":
    main()