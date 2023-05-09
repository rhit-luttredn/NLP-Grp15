@ECHO off
ECHO =============== INSTALLING PIP REQS ===============
pip install -r requirements.txt && ^
pip install grobid_client || ^
ECHO "Error installing pip requirements" && ^
goto:exit

ECHO =============== SETTING UP GROBID ===============
docker -v && ^
docker pull lfoppiano/grobid:0.7.2 && ^
cd grobid_client_python && ^
python setup.py install && cd .. || ^
ECHO "Error installing grobid" && ^
goto:exit


:exit