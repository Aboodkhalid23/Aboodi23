@echo off
chcp 65001 >nul
rem ينصب شاشة عبود على التلفزيون من حاسبة ويندوز على نفس الوايفاي
set TV=192.168.1.154
set /p TV=عنوان التلفزيون (اضغط Enter اذا هو %TV%): 
cd /d "%~dp0"
if not exist platform-tools\adb.exe (
  echo دا انزّل ادوات اندرويد...
  powershell -NoProfile -Command "Invoke-WebRequest https://dl.google.com/android/repository/platform-tools-latest-windows.zip -OutFile pt.zip; Expand-Archive pt.zip -DestinationPath . -Force; Remove-Item pt.zip"
)
echo دا انزّل الواجهة...
powershell -NoProfile -Command "Invoke-WebRequest https://github.com/Aboodkhalid23/Aboodi23/raw/claude/project-thread-4ztr10/tv-launcher/release/AboodTV.apk -OutFile AboodTV.apk"
platform-tools\adb.exe connect %TV%:5555
echo.
echo اذا طلعت رسالة بالتلفزيون: اضغط سماح ودائما. وبعدها اضغط اي زر هنا.
pause >nul
platform-tools\adb.exe connect %TV%:5555
platform-tools\adb.exe -s %TV%:5555 install -r AboodTV.apk
platform-tools\adb.exe -s %TV%:5555 shell cmd package set-home-activity com.aboodi.tvhome/.MainActivity
platform-tools\adb.exe -s %TV%:5555 shell input keyevent KEYCODE_HOME
echo.
echo خلص. شوف التلفزيون. اذا اكو خطأ صوّر هالشاشة ودزها.
pause
