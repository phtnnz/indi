# INDI Python Utils

## Installation

On Linux Ubuntu 22.04 LTS

The following system-wide packages must be installed, including support for QHY cameras

```
# apt-add-repository ppa:mutlaqja/ppa
# apt-get update
# apt-get install libindi1 indi-bin
# apt-get install indi-qhy
# apt-get install python3-indi-client
# apt-get install python3-icecream
# apt-get install python3-opencv
# apt-get install python3-astropy
```

QHY USB device found, can be used with indiserver
```
> lsusb
[...]
Bus 008 Device 010: ID 1618:0921 QHY-CCD   QHY5-II
[...]
> qhy_ccd_test
[...]
> indiserver -v indi_qhy_ccd
[...]
```


## Capturing frames with INDI camera (aka ccd)

### qhy5-capture.py

```
usage: qhy5-capture [-h] [-v] [-d] [-c CAMERA] [-g GAIN] [-o OFFSET] [-b BINNING] [-e EXPOSURE]

INDI client, capture frame from QHY5L

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -c CAMERA, --camera CAMERA
                        camera name
  -g GAIN, --gain GAIN  camera gain
  -o OFFSET, --offset OFFSET
                        camera offset
  -b BINNING, --binning BINNING
                        camera binning, 1 (1x1) or 2 (2x2)
  -e EXPOSURE, --exposure EXPOSURE
                        camera exposure time/s
```

