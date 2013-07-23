![](https://files.citizenweb.is/img/logrunner.gif)

**LogRunner** is a daemon that stores system logs in ramdisk rather than on the hard drive. This is done to avoid constant writes to disk, which can be detrimental to the lifespan of SD cards or the amount of power used by a hard disk. It is a specialized replacement for utilities like `logrotate`. While it stores all logs in memory, it also has a backup function to keep memory use ideally below 15MB at all times.

On system startup, LogRunner creates a ramdisk and copies all logs into it. It then continuously monitors the size of individual log files. Once a logfile exceeds the specified size (default is 1MB), it is automatically compressed and saved to a secondary backup folder. The file is then cleared to start anew. LogRunner also keeps log backups numbered, rotated and cleared based on their age.

## Install

Download the file, unzip, `cd` to the directory, then run `sudo ./setup.py install`.

## Configure

Edit `/etc/logrunner.conf`.

* If in rare cases your system logs are stored elsewhere, change `path`. The default is `/var/log`.
* If you want your log backups to go somewhere else, change `gzpath`. The default is `/var/logstore`.
* Set the maximum size in KB for a file to reach before it is 'retired', a.k.a. backed up and cleared. The default is 1MB.
* Set the maximum size in MB of RAM for logrunner to consume (default is 16MB)
* Folders that shouldn't be rotated go in the `folders` line under `[Ignore]`. Files that shouldn't be rotated go in the `files` line of the same section. Multiple items should be comma-separated. Note that journald binary logs are managed by journald and are added to ignore by default.

## How to use

Run as a daemon with `sudo logrunnerd -d`. Stop the process with `sudo logrunnerd -s`. A systemd service file is included for systems that use them.

All log backups are stored in a secondary folder, e.g. `/var/logstore`. This keeps memory use to a bare minimum, as it doesn't need to store active logs _and_ their backups in memory at any given time. So you can view active log files in `/var/log`, or recent backups (up to 5 are kept at a time) in `/var/logstore`.

In order to successfully save your logs, you will need to shutdown your computer as normal, via a shutdown command or clicking the Shutdown button. If you are using this on a Raspberry Pi, for example, do NOT simply unplug the device without having it shutdown first, or else your logs won't save. If this happens on accident or if your system suffers a major crash, you won't lose all logs; only the revisions since the last successful stop are lost.

## Other

Feel free to file bug reports or suggestions as issues in this repository.
