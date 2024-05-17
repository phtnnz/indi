# INDI Python Utils

Python scripts for image capture with INDI, currently tailored for a QHY 5L II mono

Copyright 2024 Martin Junius

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


## References

Based on the following code examples for PyIndi:

https://github.com/indilib/pyindi-client/tree/master/examples \
https://github.com/jkoenig72/indiCapture


## Installation

On Linux Ubuntu (Server) 22.04 LTS

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

### qhy5-capture

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

Version 0.1 / 2024-05-14 / Martin Junius
```

(writes image to hardcoded blob.jpg)


### qhy5-auto

Capture image with auto-exposure

```
usage: qhy5-auto [-h] [-v] [-d] [-c CAMERA] [-g GAIN] [-o OFFSET] [-b BINNING] [-e EXPOSURE] [-l LOOP]

INDI client, capture frames from QHY5L with auto-exposure

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -c CAMERA, --camera CAMERA
                        camera name (default QHY CCD QHY5LII-M-6077d)
  -g GAIN, --gain GAIN  initial camera gain (default: 1)
  -o OFFSET, --offset OFFSET
                        initial camera offset (default: 1)
  -b BINNING, --binning BINNING
                        initial camera binning, 1 (1x1) or 2 (2x2) (default: 2)
  -e EXPOSURE, --exposure EXPOSURE
                        initial camera exposure time/s (default: 0.5)
  -l LOOP, --loop LOOP  loop exposure, interval LOOP s

Version 0.2 / 2024-05-15 / Martin Junius
```

(writes image to hardcoded blob.jpg)

