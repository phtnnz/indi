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
> sudo apt-add-repository ppa:mutlaqja/ppa
> sudo apt-get update
> sudo apt-get install libindi1 indi-bin
> sudo apt-get install indi-qhy
> sudo apt-get install python3-indi-client
> sudo apt-get install python3-icecream
> sudo apt-get install python3-opencv
> sudo apt-get install python3-astropy
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
usage: qhy5-auto [-h] [-v] [-d] [-M] [-c CAMERA] [-g GAIN] [-o OFFSET] [-b BINNING] [-e EXPOSURE] [-l LOOP] [-O OUTPUT]

INDI client, capture frames from QHY5L with auto-exposure

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -M, --new-message     verbose log new INDI messages
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
  -O OUTPUT, --output OUTPUT
                        output JPG file ./blob.jpg)

Version 0.5 / 2024-05-26 / Martin Junius
```

### Setup as a systemd service

For Ubuntu Server 22.04 LTS, YMMV, install the qhy5lii-webcam.service file and start the service.

```
> sudo cp qhy5lii-webcam.service /lib/systemd/system
> sudo ln -s /lib/systemd/system/qhy5lii-webcam.service /etc/systemd/system/multi-user.target.wants

> sudo systemctl daemon-reload
> sudo systemctl start qhy5lii-webcam
```

You can check the status of the qhy5lii-webcam service with systemctl status, 
output should look below.

```
> sudo systemctl status qhy5lii-webcam
● qhy5lii-webcam.service - QHY5LII Webcam (User qhy5lii)
     Loaded: loaded (/lib/systemd/system/qhy5lii-webcam.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2024-07-18 13:51:40 CAT; 4 days ago
   Main PID: 6854 (run)
      Tasks: 16 (limit: 4279)
     Memory: 86.4M
        CPU: 2h 16min 52.145s
     CGroup: /system.slice/qhy5lii-webcam.service
             ├─6854 /bin/sh /home/qhy5lii/indi/run
             ├─6856 /bin/sh ./run-server
             ├─6857 /bin/sh ./run-client
             ├─6858 python3 ./qhy5-auto.py -l 10 -O /var/www/html/0c55167f/camera.jpg
             ├─6859 indiserver -l . indi_qhy_ccd
             └─6860 indi_qhy_ccd

... systemd[1]: Started QHY5LII Webcam (User qh5lii).
... run[6854]: Starting Webcam - INDI server
... run[6854]: Starting Webcam - INDI qhy-auto client
```
