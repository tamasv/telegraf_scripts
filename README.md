# Plugins for telegraf inputs.exec

Please make sure, that you have pyhon3 installed

## apc_stats.py

### Deps
```

pip install apcaccess

```

### Configuration
```toml

[[inputs.exec]]
 commands=["python3 /opt/telegraf/scripts/apc_stats.py"]
 timeout = "10s"
data_format = "influx"

```

### Example
```
root@myserver:/opt/telegraf/scripts# ./apc_stats.py 
apcaccess_status,serial="XXXXXX",ups_alias="myups" STATUS="ONLINE",WATTS=76.0,CUMONBATT=22.0,BATTV=13.6,ITEMP=29.2,LOADPCT=19.0,NOMPOWER=400.0,TIMELEFT=25.4,BCHARGE=100.0,TONBATT=0.0,OUTPUTV=230.0

```

## urbackup_stats.py

### Deps
```

pip install urbackup-server-web-api-wrapper

```

### Configuration
```toml

[[inputs.exec]]
 commands=["python3 /opt/telegraf/scripts/urbackup_stats.py http://127.0.0.1:55414/x"]
 timeout = "15s"
data_format = "influx"

```

### Example
```

root@myserver:/opt/telegraf/scripts# ./urbackup_stats.py http://127.0.0.1:55414/x
urbackup,client_version_string="2.3.4",file_ok=False,id=2,image_ok=False,ip=None,last_filebackup_issues=2,lastseen=1549116049,name="DESKTOP-22HG3VP",online=False,os_simple="windows",os_version_string="Microsoft\ Windows\ 10\ Pro\ \ (build\ 17134)\,\ 64\ bit" lastbackup=1549102480,lastbackup_image=1549102676,status=0,lastbackup_elapsed=19102315.434444,lastbackup_image_elapsed=19102119.434444
urbackup,client_version_string="2.3.4",file_ok=False,id=1,image_ok=False,ip=None,last_filebackup_issues=0,lastseen=1552236442,name="DESKTOP-4AQQ042",online=False,os_simple="windows",os_version_string="Microsoft\ Windows\ 10\ Pro\ \ (build\ 17134)\,\ 64-bit" lastbackup=1552230511,lastbackup_image=1552213760,status=0,lastbackup_elapsed=15974284.434505,lastbackup_image_elapsed=15991035.434505

```


