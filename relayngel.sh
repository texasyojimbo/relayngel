#!/bin/bash

############################################
#
# relayngel.sh
#
############################################
# 
# author: AD5NL (jim.dallas@gmail.com)
# date: 16 Mar 2019
#
############################################
#
# this script starts relayngel web
# server using flask on port 8888
# (default SDRAngel Reverse API port)
#
# if you want to run this remotely,
# you will need to change the "flask run"
# line to --
#
# flask run --host=0.0.0.0 --port=8888
#
# You can also change FLASK_ENV to
# development for debugging purposes
#
############################################

export FLASK_APP=relayngel.py
export FLASK_ENV=production

flask run --port=8888 
