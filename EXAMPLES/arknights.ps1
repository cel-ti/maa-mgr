reldplay --name p1 launch
maamgr maa patch -p "config/gui.json" "Configurations/Default/Start.RunDirectly=True"
Start-Sleep -Seconds 10
maa-arknights
Start-Sleep -Seconds 2400
reldplay --name p1 killapp -p com.hypergryph.arknights.bilibili
Stop-Process -Name "*MAA*" -Force 