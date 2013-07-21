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

import atexit
import ConfigParser
import gzip
import os
import signal
import subprocess
import sys
import time
import logging
import tempfile

class LogRunner:
	def __init__(self, config_file, logmethod):
		# Create the ramdisk and move any prior logs to memory
		self.stoploop = False
		logging.basicConfig(
			format='%(asctime)s [%(levelname)s] - %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S', 
			level=logging.INFO,
			filename=('/var/log/logrunner.log' if logmethod is 'tofile' else ''),
			)
		logging.info('Initializing LogRunner')

		cfg = ConfigParser.ConfigParser()
		if os.path.exists(config_file):
			cfg.read(config_file)
		else:
			logging.critical('Couldn\'t find the config file. Sorry')
			sys.exit(1)

		self.size = cfg.getint('config', 'size') * 1024
		self.ramsize = cfg.getint('config', 'ramsize') * 1024
		self.path = os.path.abspath(cfg.get('config', 'path'))
		self.gzpath = os.path.abspath(cfg.get('config', 'gzpath'))
		self.igfolds = cfg.get('ignore', 'folders').split(',')
		self.igfiles = cfg.get('ignore', 'files').split(',')

		self.logmount = tempfile.mkdtemp()
		try:
			subprocess.call(['mount', '-t', 'tmpfs', '-o',
				'nosuid,noexec,nodev,mode=0755,errors=continue,size={}'.format(self.ramsize),
				'logrunner', 
				self.logmount])
		except Exception, e:
			logging.error(e)
			logging.critical('Creation of ramdisk/mount failed, exiting')
			sys.exit(1)

		if not os.path.isdir(self.path):
			os.mkdir(self.path, 0754)
		if not os.path.isdir(self.gzpath):
			os.mkdir(self.gzpath, 0754)
		for item in os.listdir(self.path):
			if '.gz' in item:
				subprocess.call(['mv', os.path.join(self.path, item), 
					os.path.join(self.gzpath, item)])
			else:
				subprocess.call(['cp', '-rp', 
					os.path.join(self.path, item), 
					os.path.join(self.logmount, item)])

		subprocess.call(['mount', '--bind', self.path, self.logmount])

		# Normal exit when terminated
		atexit.register(self.stop)
		signal.signal(signal.SIGTERM, lambda signum, stack_frame: sys.exit(0))
		signal.signal(signal.SIGINT, lambda signum, stack_frame: sys.exit(0))

		logging.info('LogRunner is up and hunting for replicants')

		while self.stoploop == False:
			for item in os.walk(self.path):
				if not any(x in item[0] for x in self.igfolds):
					for logfile in item[2]:
						if not any(x in logfile for x in self.igfiles):
							self.check(os.path.join(item[0], logfile))
			time.sleep(60)

	def retire(self, logfile):
		# Write the log to backup location, and flush memory
		absin = os.path.join(self.path, logfile)
		absout = os.path.join(self.gzpath, logfile + '.gz')
		login = open(absin, 'rb')

		if os.path.exists(absout):
			if os.path.exists(absout + '.1'):
				if os.path.exists(absout + '.2'):
					if os.path.exists(absout + '.3'):
						if os.path.exists(absout + '.4'):
							subprocess.call(['rm', absout + '.4'])
						subprocess.call(['mv', absout + '.3', absout + '.4'])
					subprocess.call(['mv', absout + '.2', absout + '.3'])
				subprocess.call(['mv', absout + '.1', absout + '.2'])
			subprocess.call(['mv', absout, absout + '.1'])

		if not os.path.exists(os.path.dirname(absout)):
			os.makedirs(os.path.dirname(absout))
		try:
			logout = gzip.open(absout, 'wb')
			logout.writelines(login)
			logout.close()
			login.close()
		except Exception, e:
			logging.error(e)
			logging.error('Couldn\'t backup the file %s, whoops' % absin)
		else:
			logging.info('%s retired to %s' % (absin, absout))
		open(absin, 'w').close()

	def check(self, logfile):
		# Check memory use. If too high, force log write and flush.
		if os.path.getsize(logfile) >= (int(self.size)*1024):
			lf = logfile.split(self.path, 1)[1].lstrip('/')
			self.retire(lf)

	def stop(self):
		# Unmount everything and stop operation
		self.stoploop = True
		subprocess.call(['umount', self.logmount])
		for item in os.listdir(self.logmount):
			subprocess.call(['cp', '-rp', os.path.join(self.logmount, 
				item), self.path])
		subprocess.call(['umount', 'logrunner'])
		os.rmdir(self.logmount)
		logging.info('LogRunner stopped successfully')
		sys.exit(0)
