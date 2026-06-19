#!/bin/bash
#
# From:
# https://indilib.org/forum/ccds-dslrs/1730-asi-120mc-bug.html?start=12#12977
#
indi_setprop "ZWO CCD ASI120MC.CONNECTION.CONNECT=On"
indi_setprop "ZWO CCD ASI120MC.CCD_CONTROLS_MODE.AUTO_Gain=Off"
indi_setprop "ZWO CCD ASI120MC.CCD_CONTROLS.Gain=75"

indi_setprop "ZWO CCD ASI120MC.UPLOAD_MODE.UPLOAD_LOCAL=On"
indi_setprop "ZWO CCD ASI120MC.CCD_COMPRESSION.CCD_RAW=Off"
indi_setprop "ZWO CCD ASI120MC.CCD_COMPRESSION.CCD_COMPRESS=On"
indi_setprop "ZWO CCD ASI120MC.CCD_VIDEO_FORMAT.ASI_IMG_RGB24=On"

for exp in 1 0.1 0.01 0.001 0.0001; do
    for n in $(seq 1 100); do
        date
        rm -f IMAGE_*.fits
        indi_setprop "ZWO CCD ASI120MC.CCD_EXPOSURE.CCD_EXPOSURE_VALUE=$exp"

        slp=$(echo $exp+1 | bc -l)
        sleep $slp"s"
        for i in $(seq 1 1000); do
            if [ "$(indi_getprop 'ZWO CCD ASI120MC.CCD_EXPOSURE.CCD_EXPOSURE_VALUE' 2>/dev/null | cut -d '=' -f 2)" == "0" ]; then
                break
            fi
            sleep 0.25s
        done
        sleep 5s
        if ! [ -f IMAGE_001.fits ]; then
            echo Nothing captured, exp="$exp", n="$n"...
        else
            echo Frame captured, exp="$exp", n="$n"...
        fi
    done
done
