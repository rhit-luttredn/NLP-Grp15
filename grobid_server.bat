@ECHO off
set container_name=grobid_server

if "%1"=="stop" (
    ECHO.
    ECHO Stopping Grobid Server...
    docker stop %container_name% >nul

) else if "%1"=="start" (
    ECHO.
    ECHO Starting Grobid Server...
    docker run --name %container_name% -t --rm -p 8070:8070 lfoppiano/grobid:0.7.2

) else if "%1"=="restart" (
    ECHO.
    ECHO Restarting Grobid Server...
    docker restart %container_name% >nul

) else if "%1"=="status" (
    docker container inspect -f "{{.State.Status}}" %container_name%

) else (
    ECHO.
    ECHO Usage: grobid_server.bat [start^|stop^|restart^|status]
    ECHO    start: starts the grobid server
    ECHO    stop: stops the grobid server
    ECHO    restart: restarts the grobid server
    ECHO    status: shows the status of the grobid server
    ECHO.
)