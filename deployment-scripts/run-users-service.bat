@echo off
setlocal enabledelayedexpansion

REM Configuration
set NETWORK_NAME=librarypal-net
set VOLUME_NAME=librarypal_mysql_data

set DB_CONTAINER=librarypal-db
set DB_IMAGE=mysql:8.0
set DB_PORT=3306
set DB_ROOT_PASSWORD=admin123
set DB_NAME=library

set PMA_CONTAINER=librarypal-db-admin
set PMA_IMAGE=phpmyadmin
set PMA_PORT=8080

set USER_CONTAINER=librarypal-users-service-container
set USER_IMAGE=librarypal-users-service
set USER_PORT=8000

REM MySQL env vars for user-service
set DB_USER=root
set DB_PASSWORD=%DB_ROOT_PASSWORD%
set DB_HOST=%DB_CONTAINER%

REM Create network and volume if not exist
echo ➡️ Creating Docker network and volume if not exists...
docker network inspect %NETWORK_NAME% >nul 2>&1 || docker network create %NETWORK_NAME%
docker volume inspect %VOLUME_NAME% >nul 2>&1 || docker volume create %VOLUME_NAME%

REM Start MySQL container if not running
for /f "tokens=*" %%a in ('docker ps -q -f name=%DB_CONTAINER%') do set DB_RUNNING=%%a
if defined DB_RUNNING (
    echo 🐬 MySQL container '%DB_CONTAINER%' is already running.
) else (
    for /f "tokens=*" %%b in ('docker ps -aq -f name=%DB_CONTAINER%') do set DB_EXISTS=%%b
    if defined DB_EXISTS (
        echo 🐬 Starting existing MySQL container...
        docker start %DB_CONTAINER%
    ) else (
        echo 🐬 Running new MySQL container...
        docker run -d ^
          --name %DB_CONTAINER% ^
          --network %NETWORK_NAME% ^
          -e MYSQL_ROOT_PASSWORD=%DB_ROOT_PASSWORD% ^
          -e MYSQL_DATABASE=%DB_NAME% ^
          -v %VOLUME_NAME%:/var/lib/mysql ^
          -p %DB_PORT%:3306 ^
          %DB_IMAGE%
    )
)

REM Start phpMyAdmin container if not running
for /f "tokens=*" %%c in ('docker ps -q -f name=%PMA_CONTAINER%') do set PMA_RUNNING=%%c
if defined PMA_RUNNING (
    echo 🧰 phpMyAdmin container '%PMA_CONTAINER%' is already running.
) else (
    for /f "tokens=*" %%d in ('docker ps -aq -f name=%PMA_CONTAINER%') do set PMA_EXISTS=%%d
    if defined PMA_EXISTS (
        echo 🧰 Starting existing phpMyAdmin container...
        docker start %PMA_CONTAINER%
    ) else (
        echo 🧰 Running new phpMyAdmin container...
        docker run -d ^
          --name %PMA_CONTAINER% ^
          --network %NETWORK_NAME% ^
          -e PMA_HOST=%DB_CONTAINER% ^
          -e PMA_PORT=3306 ^
          -e MYSQL_ROOT_PASSWORD=%DB_ROOT_PASSWORD% ^
          -p %PMA_PORT%:80 ^
          %PMA_IMAGE%
    )
)

REM Always rebuild and restart user-service container
echo 🧹 Stopping old users-service container (if any)...
docker rm -f %USER_CONTAINER% 2>nul || true

echo 🔨 Building users-service image...
docker build -t %USER_IMAGE% .

echo 🚀 Starting users-service container...
docker run -d ^
  --name %USER_CONTAINER% ^
  --network %NETWORK_NAME% ^
  -e DB_USER=%DB_USER% ^
  -e DB_PASSWORD=%DB_PASSWORD% ^
  -e DB_HOST=%DB_HOST% ^
  -e DB_NAME=%DB_NAME% ^
  -p %USER_PORT%:%USER_PORT% ^
  %USER_IMAGE%

echo ✅ All services are up:
echo - MySQL:         localhost:%DB_PORT%
echo - phpMyAdmin:    http://localhost:%PMA_PORT%
echo - Users Service:  http://localhost:%USER_PORT%/docs

endlocal
