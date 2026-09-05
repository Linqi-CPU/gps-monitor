$env:JAVA_HOME = 'C:\Users\ASUS\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot'
$env:ANDROID_HOME = 'C:\Users\ASUS\AppData\Local\Android\Sdk'
$env:NODE_HOME = 'C:\Users\ASUS\AppData\Local\hermes\node'
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:NODE_HOME;$env:PATH"

Write-Host "JAVA_HOME=$env:JAVA_HOME"
Write-Host "ANDROID_HOME=$env:ANDROID_HOME"
Write-Host "NODE_HOME=$env:NODE_HOME"

& java -version
& javac -version
& node --version

Set-Location 'D:\桌面\to_hermes_work\gps\apk-build'

Write-Host ''
Write-Host '==== Initializing Bubblewrap ===='
& npx bubblewrap init --manifest=manifest.json --non-interactive

Write-Host ''
Write-Host '==== Building APK ===='
& npx bubblewrap build --skipSigning

Write-Host 'Done. Press any key...'
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
