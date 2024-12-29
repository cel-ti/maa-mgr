reldplay --name p1 launch
maamgr maa patch -p "config/gui.json" "Configurations/Default/Start.RunDirectly=True"
timeout /t 10
maa-arknights
timeout /t 2400
reldplay --name p1 killapp -p com.hypergryph.arknights.bilibili
taskkill /f /fi "WINDOWTITLE eq MAA*"
