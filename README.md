![](https://files.citizenweb.is/img/logrunner.gif)

*LogRunner* is a daemon that stores system logs in ramdisk rather than on the hard drive. This is done to avoid constant writes to disk, which can be detrimental to the lifespan of SD cards or the amount of power used by a hard disk. It is a specialized replacement for utilities like `logrotate`. While it stores all logs in memory, it also has a backup function to keep memory use ideally below 15MB at all times.

On system startup, LogRunner creates a ramdisk and copies all logs into it. It then continuously monitors the size of individual log files. Once a logfile exceeds the specified size (default is 1MB), it is automatically compressed and saved to a secondary backup folder. The file is then cleared to start anew. LogRunner also keeps log backups numbered, rotated and cleared based on their age.

The downside to using LogRunner is that all log backups must be stored in a secondary folder, e.g. `/var/logstore`. This keeps memory use to a bare minimum, as it doesn't need to store active logs _and_ their backups in memory at any given time.
