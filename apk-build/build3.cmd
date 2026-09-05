@echo off
chcp 65001 >nul
set "JAVA_HOME=C:\Users\ASUS\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
set "ANDROID_HOME=C:\Users\ASUS\AppData\Local\Android\Sdk"
set "NODE_HOME=C:\Users\ASUS\AppData\Local\hermes\node"
set "PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%NODE_HOME%;%PATH%"

echo JAVA_HOME=%JAVA_HOME%
echo ANDROID_HOME=%ANDROID_HOME%
echo NODE_HOME=%NODE_HOME%

java -version
javac -version
node --version

cd /d D:\桌面\to_hermes_work\gps\apk-build
echo current dir: %cd%

echo.
echo ==== Initializing Bubblewrap ====
npx bubblewrap init --manifest=manifest.json < bubblewrap_input.txt

echo.
echo ==== Building APK ====
npx bubblewrap build --skipSigning

pause
