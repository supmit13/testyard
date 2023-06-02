#!/bin/bash

`ffmpeg -f x11grab -r 25 -s 1024x768 -an -i :0.0 -vcodec huffyuv $1`;
