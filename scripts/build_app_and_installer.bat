:: File paths will all need to be updated to your setup

set babblepath=X:\Documents\GitHub\ProjectBabble
set innopath="C:\Program Files (x86)\Inno Setup 6"

cd /d %babblepath%\BabbleApp
pyinstaller babbleapp.spec --noconfirm
:: Copy the Models directory + content into dist because I can't get pyinstaller to not flatten the file structure
cd /d %babblepath%\BabbleApp\dist\Babble_App\Models
robocopy %babblepath%\BabbleApp\Models %babblepath%\BabbleApp\dist\Babble_App\Models\ /E
cd %babblepath%\BabbleApp\dist\Babble_App\Models
rmdir /s /q dev

start /D %innopath% cmd /k ISCC %babblepath%\scripts\installer.iss
