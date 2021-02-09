# Start Imports
import os
import admin
import shutil
import psutil
import requests
import colorama
import subprocess
import config as cfg
# mysql-connector-python
import mysql.connector

from sys import exit
from os import listdir
from colorama import Fore
from os.path import isfile
from datetime import datetime
# End Imports


class Screenshare(object):
	def __init__(self):
		super(Screenshare, self).__init__()
		self.sqlCnx = None
		self.sqlCursor = None
		self.user_path = '/'.join(os.getcwd().split('\\', 3)[:3])
		self.drive_letter = os.getcwd().split('\\', 1)[0]+'/'
		self.winUsername = os.getlogin()
		self.javawPid = ''
		self.mcPath = ''
		self.lunarClient = False

		self.Check02 = 'passed'
		self.Check03 = 'passed'
		self.Check04 = 'passed'
		self.Check05 = 'passed'
		self.Check06 = 'passed'
		self.deletedFiles = 'none'
		colorama.init()

	@staticmethod
	def asAdmin():
		if not admin.isUserAdmin():
			admin.runAsAdmin(wait=False)
			exit()

	# Finds minecraft process and gets info
	def mcProcess(self):
		pid = 0
		mcprocess_info = {}

		# Get processes with the name "javaw"
		process = [p for p in psutil.process_iter(attrs=['pid', 'name']) if 'javaw' in p.info['name']]
		if process:
			process = process[0]
			pid = process.info['pid']
			# print(f'{cfg.prefix} Minecraft found on PID: {pid}')
		else:
			input(f'Minecraft not found...\nPress enter to continue')
			quit()

		# Get all command line arguments of process
		process = process.cmdline()
		for argument in process:
			if "--" in argument:
				mcprocess_info[argument.split("--")[1]] = process[process.index(argument) + 1]

		self.javawPid = pid
		self.mcPath = mcprocess_info["version"]

		customClient = False
		try:
			detectCustom = mcprocess_info["username"]
		except Exception as inst:
			p = inst
			customClient = True

		if customClient is True:
			if 'com.moonsworth.lunar.patcher.LunarMain' in process:
				self.lunarClient = True
			else:
				self.lunarClient = False

	# Downloads all necessary files
	def dependencies(self):
		path = f'{self.drive_letter}/Windows/Temp/Astro'
		if not os.path.exists(path):
			os.mkdir(path)
		with open(f'{path}/strings2.exe', 'wb') as f:
			f.write(requests.get(cfg.stringsSoftware).content)

	def connectDatabase(self):
		# Don't forget to set only read permissions to this user for more security.
		self.sqlCnx = mysql.connector.connect(host=f'{cfg.host}', user=f'{cfg.user}', password=f'{cfg.password}', database=f'{cfg.database}')
		self.sqlCursor = self.sqlCnx.cursor()

	# Gets PID of a process from name
	@staticmethod
	def getPID(name, service=False):
		if service:
			response = str(subprocess.check_output(f'tasklist /svc /FI "Services eq {name}')).split('\\r\\n')
			for process in response:
				if name in process:
					pid = process.split()[1]
					return pid
		else:
			pid = [p.pid for p in psutil.process_iter(attrs=['pid', 'name']) if name == p.name()][0]
			return pid

	# Gets/Dumps strings via a PID
	def dump(self, pid):
		cmd = f'{self.drive_letter}/Windows/Temp/Astro/strings2.exe -pid {pid} -raw -nh'
		strings = str(subprocess.check_output(cmd)).replace('\\\\', "/")
		strings = list(set(strings.split("\\r\\n")))

		return strings

	# Checking for recording software
	@staticmethod
	def recordingCheck():

		tasks = str(subprocess.check_output('tasklist')).lower()
		found = [x for x in cfg.recordingSoftwares if x in tasks]

		if found:
			for software in found:
				print(' : ' + Fore.RED + f' Not Clean ({cfg.recordingSoftwares[software]})' + Fore.WHITE)
				sshare.end()
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Checks modification/run times
	def modificationTimes(self):

		SID = str(subprocess.check_output(f'wmic useraccount where name="{self.winUsername}" get sid')).split('\\r\\r\\n')[1]
		recycle_bin_path = self.drive_letter+"/$Recycle.Bin/"+SID

		# Recycle bin modified time check
		a = datetime.fromtimestamp(os.path.getmtime(recycle_bin_path))
		b = datetime.now()
		c = b - a
		minutes = c.total_seconds() / 60
		if minutes < 5:
			self.Check02 = 'failed'
			print(' :' + Fore.RED + ' Not Clean' + Fore.WHITE)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	@staticmethod
	def mins_between(d1, d2):

		d1 = datetime.strptime(d1, "%H-%M-%S")
		d2 = datetime.strptime(d2, "%H-%M-%S")
		return abs((d2 - d1).minutes)

	# In Instance Checks
	def inInstance(self):

		if self.lunarClient is True:
			javawStrings = self.dump(self.javawPid)
			found = [f'{cfg.lunarStrings[x]}' for x in javawStrings if x in cfg.lunarStrings]

			if found:
				for hack in found:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			else:
				print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)
		else:
			javawStrings = self.dump(self.javawPid)
			found = [f'{cfg.javawStrings[x]}' for x in javawStrings if x in cfg.javawStrings]

			if found:
				for hack in found:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			else:
				print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Out of instance checks
	def outOfInstance(self):
		dpsPid = self.getPID('DPS', service=True)
		strings = self.dump(dpsPid)
		strings = ['.exe!'+x.split('!')[3] for x in strings if '.exe!' in x and x.startswith('!!')]

		found = [x for x in cfg.dpsStrings if x in strings]

		if found:
			for string in found:
				self.Check04 = 'failed'
				print(f' :' + Fore.RED + f' Not Clean ({cfg.dpsStrings[string]})' + Fore.WHITE)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Checks for JNativeHook based autoclicker
	def jnativehook(self):
		path = f'{self.user_path}/AppData/Local/Temp'

		found = [x for x in listdir(path) if isfile(f'{path}/{x}') if 'JNativeHook' in x and x.endswith('.dll')]

		if found:
			self.Check05 = 'failed'
			print(f' : ' + Fore.RED + f' Not Clean')
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Gets recently executed + deleted files
	def executedDeleted(self):
		pcasvcPid = self.getPID('PcaSvc', service=True)
		explorerPid = self.getPID('explorer.exe')
		pcasvcStrings = self.dump(pcasvcPid)
		explorerStrings = self.dump(explorerPid)

		deleted = {}

		for string in pcasvcStrings:
			string = string.lower()
			if string.startswith(self.drive_letter.lower()) and string.endswith('.exe'):
				if not os.path.isfile(string):
					if string in explorerStrings:
						filename = string.split('/')[-1]
						self.Check06 = 'failed'
						if self.deletedFiles is 'none':
							self.deletedFiles = string + ', '
						else:
							self.deletedFiles = self.deletedFiles + string + ', '
						deleted[string] = {'filename': filename, 'method': '01'}

		# Check 02 (Explorer PcaClient)
		if explorerStrings:
			for string in explorerStrings:
				string = string.lower()
				if 'trace' and 'pcaclient' in string:
					path: str = [x for x in string.split(',') if '.exe' in x][0]
					if not os.path.isfile(path):
						if self.deletedFiles is 'none':
							self.deletedFiles = path + ', '
						else:
							self.deletedFiles = self.deletedFiles + path + ', '
						filename = path.split('/')[-1]
						self.Check06 = 'failed'
						deleted[path] = {'filename': filename, 'method': '02'}

		if deleted is True:
			print(' :' + Fore.RED + ' Not Clean')
			print('')
			for path in deleted:
				print(f' - {path}' + Fore.WHITE)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	@staticmethod
	def end():
		# input('\nScan finished\nPress enter to exit..')
		input('\nPress enter to exit..')
		temp = f'{sshare.drive_letter}/Windows/Temp/Astro'
		if os.path.exists(temp):
			shutil.rmtree(temp)
		exit()

	def saveScan(self):
		if self.deletedFiles is None:
			self.deletedFiles = 'none'

		query = f'INSERT INTO Scans (ScanID, HWID, Check02, Check03, Check04, Check05, Check06, deletedFiles) VALUES '
		query = query + f'("{cfg.scanID}", "{cfg.hwid}", "{self.Check02}", "{self.Check03}", "{self.Check04}", '
		query = query + f'"{self.Check05}", "{self.Check06}", "{self.deletedFiles}")'
		
		self.sqlCursor.execute(query)
		self.sqlCnx.commit()



sshare = Screenshare()

sshare.asAdmin()
sshare.mcProcess()
sshare.dependencies()
sshare.connectDatabase()

print(f'{cfg.prefix} Starting Scan with ID: {cfg.scanID}\n')
# print(f'{cfg.prefix} HWID : {cfg.hwid}\n')

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #01')
sshare.recordingCheck()

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #02')
sshare.modificationTimes()

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #03')
sshare.inInstance()

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #04')
sshare.outOfInstance()

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #05')
sshare.jnativehook()

print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #06')
sshare.executedDeleted()


sshare.saveScan()

print('')
sshare.end()
