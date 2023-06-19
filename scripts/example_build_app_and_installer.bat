:: Example script to auto build app and make an installer
:: File paths will all need to be updated to your setup
cd C:\Users\Prohurtz\PycharmProjects\Babble_app\BabbleApp
pyinstaller babbleapp.spec --noconfirm
cd C:\Users\Prohurtz\OneDrive\Desktop
cd C:\Program Files (x86)\Inno Setup 6
ISCC C:\Users\Prohurtz\OneDrive\Desktop\installer.iss
cls
@echo off
color 0A
echo -------------------------------
echo ############ DONE #############
echo -------------------------------
PAUSE