reldplay --name p1 launch
timeout /t 30
maamgr m9a import -p "EXAMPLES/1999_CN_TASK.json" -k "resource,task"
maamgr m9a auto -l 3600
reldplay --name p1 killapp -p com.shenlan.m.reverse1999