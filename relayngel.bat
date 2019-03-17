############################################
#
# relayngel.bat
#
############################################
# 
# author: AD5NL (jim.dallas@gmail.com)
# date: 17 Mar 2019
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
############################################

set PYTHON_PATH=C:\Python27
set FLASK_APP=relayngel.py
set FLASK_ENV=production

%PYTHON_PATH%\python -m flask run --port=8888 
