@echo off
"C:\Users\ASUS\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot\bin\java.exe" -version
"C:\Users\ASUS\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot\bin\javac.exe" -version
"C:\Users\ASUS\AppData\Local\hermes\node\node.exe" --version
cd /d D:\桌面\to_hermes_work\gps\apk-build
echo.
echo ==== Initializing Bubblewrap ====
"C:\Users\ASUS\AppData\Local\hermes\node\npx.cmd" bubblewrap init --manifest=manifest.json --non-interactive
echo.
echo ==== Building APK ====
"C:\Users\ASUS\AppData\Local\hermes\node\npx.cmd" bubblewrap build --skipSigning
pause
