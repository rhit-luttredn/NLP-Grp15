@ECHO off
ECHO =============== INSTALLING PIP REQS ===============
pip install -r requirements.txt && ^
ECHO "Error installing pip requirements" && ^
goto:exit

ECHO =============== SETTING UP GROBID ===============
docker -v && ^
docker pull lfoppiano/grobid:0.7.2 && ^
cd grobid_client_python && ^
python setup.py install && ^
pip install grobid_client && ^
pip install grobid_client_python && ^ cd .. || ^
ECHO "Error installing grobid" && ^
goto:exit


:exit