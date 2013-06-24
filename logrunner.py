#!/usr/bin/env python
#########################################################################
##
##  LogRunner
##  Copyright (C) 2013 Jacob Cook
##  jacob@jcook.cc
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
#########################################################################

import argparse
import ConfigParser
import gzip
import os
import shutil
import sys
import logging
from tempfile import mkdtemp
from fs.memoryfs import MemoryFS
from fs.expose import fuse

class LogRunner:
	def __init__(self, path, gzpath, size):
		# Create the ramdisk, mount the disk and move any prior logs to memory
		logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S', filename='/var/log/logrunner.log', level=logging.INFO)
		logging.info('Initializing LogRunner')

		cfg = ConfigParser.ConfigParser()
		if os.path.exists('/etc/logrunner.conf'):
			cfg.read('/etc/logrunner.conf')
		else:
			cfgfile = open('/etc/logrunner.conf', 'w')
			cfg.add_section('config')
			cfg.set('config', 'path', '/var/log')
			cfg.set('config', 'gzpath', '/var/logstore')
			cfg.set('config', 'size', 1024)
			cfg.write()
			cfgfile.close()
			cfg.read('/etc/logrunner.conf')

		if path:
			self.path = path
		else:
			self.path = cfg.get('config', 'path')
		if size:
			self.size = size
		else:
			self.size = cfg.get('config', 'size')
		if gzpath:
			self.gzpath = gzpath
		else:
			self.gzpath = cfg.get('config', 'gzpath')

		tempdir = mkdtemp()
		try:
			tempfs = MemoryFS()
			tempmp = fuse.mount(tempfs, tempdir)
		except Exception, e:
			logging.error(e)
			logging.critical('Creation of temporary ramdisk/mount failed, exiting')
			sys.exit()
		for item in os.listdir(self.path):
			shutil.move(os.path.join(self.path, item), tempdir)

		if not os.path.isdir(self.path):
			os.mkdir(self.path, 0754)

		try:
			fs = MemoryFS()
			mp = fuse.mount(fs, self.path)
		except Exception, e:
			logging.error(e)
			logging.critical('Creation of ramdisk/mount failed, exiting')
			sys.exit()

		for item in os.listdir(tempdir):
			shutil.move(os.path.join(tempdir, item), self.path)
		tempmp.unmount()
		tempfs.close()
		os.unlink(tempdir)

		logging.info('LogRunner is up and hunting for replicants')

		# TODO: what comes after this

	def retire(self, logfile):
		# Write the log to backup location, and flush memory
		absin = os.path.join(self.path, logfile)
		absout = os.path.join(self.gzpath, logfile + '.gz')
		login = open(absin, 'rb')
		if not os.path.exists(os.path.dirname(absout))
			os.makedirs(os.path.dirname(absout))
		try:
			logout = gzip.open(absout, 'wb')
		except Exception, e:
			logging.error(e)
			logging.error('Couldn\'t backup the file %s, whoops' % absin)
		else:
			logging.info('%s retired to %s' % (absin, absout))
		logout.writelines(login)
		logout.close()
		login.write()
		login.close()
		open(absin, 'w').close()

	def check(self, file):
		# TODO
		# Check memory use. If too high, force log write and flush.
		pass

	def watch(self):
		# TODO
		# Periodically check memory use compared to spec
		pass

	def stop(self, fs, mp):
		# Unmount everything and stop operation
		tempdir = mkdtemp()
		try:
			tempfs = MemoryFS()
			tempmp = fuse.mount(tempfs, tempdir)
		except Exception, e:
			logging.error(e)
			logging.critical('Creation of temporary ramdisk/mount on exit failed, aborting')
			sys.exit()
		for item in os.listdir(self.path):
			shutil.move(os.path.join(self.path, item), tempdir)
		mp.unmount()
		fs.close()
		for item in os.listdir(tempdir):
			shutil.move(os.path.join(tempdir, item), self.path)
		logging.info('LogRunner stopped successfully')
		sys.exit()


def main():
	# Check commandline params and execute as necessary
	parser = ArgumentParser()
	parser.add_argument("-p", "--path", help="set path to log directory")
	parser.add_argument("-s", "--size", type=int, help="set max size (in KB) for log file before forced cycle")
	parser.add_argument("-z", "--gzpath", help="set path to log backups directory")
	args = parser.parse_args()

	if args.path:
		path = args.path
	else:
		path = ''
	if args.gzpath:
		gzpath = args.gzpath
	else:
		gzpath = ''
	if args.size:
		size = args.size
	else:
		size = 0

	LogRunner(path, gzpath, size)

main()
