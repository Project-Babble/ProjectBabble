:: Example script to auto build app and make an installer
:: File paths will all need to be updated to your setup
cd X:\Documents\GitHub\ProjectBabble\BabbleApp
pyinstaller babbleapp.spec --noconfirm
cd C:\Users\epicm\Desktop\Build
cd 'C:\Program Files (x86)\Inno Setup 6'
./ISCC X:\Documents\GitHub\ProjectBabble\scripts\installer.iss
cls
@echo off
color 0A
echo -------------------------------
echo ############ DONE #############
echo -------------------------------
PAUSE