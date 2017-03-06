pyFTPclient
===========

FTP client written in python with monitoring and reconnection; it utilises the ftplib & threading.

Features:
- it shows download progress,
- it changes socket settings for optimal download,  
- it monitors status of the FTP connection
- it can reconnect and download file from the point of disconnect.

Warning : This version of pyFTPclient will download all files containing in remote directory.

Example run:

```
python pyftpclient.py --host 192.168.1.1 --usr UserName --psw MyPassword --local_dir MyDir --remote_dir RemoteDir
```

This command will download all files from FTP server with IP 192.168.1.1 directory RemoteDir local directory MyDir using credentials UserName:MyPassword
