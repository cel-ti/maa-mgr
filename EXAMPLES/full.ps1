# Schedule shutdown in 4 hours (14400 seconds)
shutdown.exe /s /f /t 14400

# Install/upgrade current package
pip install . --upgrade

# Execute other scripts
& "$PSScriptRoot\arknights.ps1"
& "$PSScriptRoot\re1999_cn.ps1"
& "$PSScriptRoot\re1999_en.ps1" 