reldplay --name p1 launch
Start-Sleep -Seconds 30
maamgr m9a patch -p "resource/global_jp/pipeline/startup.json" "Start1999/package=com.bluepoch.m.en.reverse1999"
maamgr m9a import -p "EXAMPLES/1999_EN_TASK.json" -k "resource,task"
maamgr m9a auto -l 3600
reldplay --name p1 killapp -p com.bluepoch.m.en.reverse1999 