# Start Imports
import os
import re
import elevate as elevate
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


# noinspection PyBroadException
class Nex(object):
	def __init__(self):
		super(Nex, self).__init__()
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
	def asRoot():
		if not elevate.isRootUser():
			elevate.runRoot(wait=False)
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
			input('Minecraft not found...\nPress enter to continue')
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
		except:
			customClient = True

		if customClient is True:
			if 'com.moonsworth.lunar.patcher.LunarMain' in process:
				self.lunarClient = True
			else:
				self.lunarClient = False

	# Downloads all necessary files
	def dependencies(self):
		path = f'{self.drive_letter}/Windows/Temp/Nex'
		if not os.path.exists(path):
			os.mkdir(path)
		with open(f'{path}/strings2.exe', 'wb') as f:
			f.write(requests.get(cfg.stringsSoftware).content)

	def connectDatabase(self):

		# Don't forget to set only read permissions to this user for more security.
		if cfg.enableDatabase is True:
			try:
				self.sqlCnx = mysql.connector.connect(host=f'{cfg.host}', user=f'{cfg.user}', password=f'{cfg.password}', database=f'{cfg.database}')
				self.sqlCursor = self.sqlCnx.cursor()
			except:
				input('Cannot connect to the database...\nPress enter to continue')
				quit()

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

	# Get process start time
	@staticmethod
	def proc_starttime(pid):
		# https://gist.github.com/westhood/1073585
		p = re.compile(r"^btime (\d+)$", re.MULTILINE)
		with open("/proc/stat") as f:
			m = p.search(f.read())
			btime = int(m.groups()[0])

		clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
		with open("/proc/%d/stat" % pid) as f:
			stime = int(f.read().split()[21]) / clk_tck

		return datetime.fromtimestamp(btime + stime)

	# Gets/Dumps strings via a PID
	def dump(self, pid):
		cmd = f'{self.drive_letter}/Windows/Temp/Nex/strings2.exe -pid {pid} -raw -nh'
		strings = str(subprocess.check_output(cmd)).replace('\\\\', "/")
		strings = list(set(strings.split("\\r\\n")))

		return strings

	# Checking for recording software
	@staticmethod
	def recordingCheck():

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #01')
		tasks = str(subprocess.check_output('tasklist')).lower()
		found = [x for x in cfg.recordingSoftwares if x in tasks]

		if found:
			for software in found:
				print(' : ' + Fore.RED + f' Not Clean ({cfg.recordingSoftwares[software]})' + Fore.WHITE)
				Nex.end()
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Checks modification/run times
	def modificationTimes(self):

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #02')
		SID = str(subprocess.check_output(f'wmic useraccount where name="{self.winUsername}" get sid')).split('\\r\\r\\n')[1]
		recycle_bin_path = self.drive_letter+"/$Recycle.Bin/"+SID

		# Recycle bin modified time check
		recyclebinTime = datetime.fromtimestamp(os.path.getmtime(recycle_bin_path))
		currentTime = datetime.now()
		binDiffTime = currentTime - recyclebinTime
		minutes = binDiffTime.total_seconds() / 60

		explorerPid = self.getPID('explorer.exe')
		p = psutil.Process(explorerPid)
		explorerTime = datetime.fromtimestamp(p.create_time())

		explorerDiffTime = currentTime - explorerTime
		minutes2 = explorerDiffTime.total_seconds() / 60

		if minutes2 < 300:
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

		global foundHeuristic
		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #03')
		if self.lunarClient is True:
			javawStrings = self.dump(self.javawPid)
			found = [f'{cfg.javawStrings[x]}' for x in javawStrings if x in cfg.javawStrings]

			if '1.8' in self.mcPath:
				foundHeuristic = [f'{cfg.lunar18Strings[x]}' for x in javawStrings if x in cfg.lunar18Strings]

			if found:
				for hack in found:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			elif foundHeuristic:
				for hack in foundHeuristic:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			else:
				print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)
		else:
			javawStrings = self.dump(self.javawPid)
			found = [f'{cfg.javawStrings[x]}' for x in javawStrings if x in cfg.javawStrings]

			if '1.8' in self.mcPath:
				foundHeuristic = [f'{cfg.minecraft18Strings[x]}' for x in javawStrings if x in cfg.minecraft18Strings]
			elif '1.7' in self.mcPath:
				foundHeuristic = [f'{cfg.minecraft17Strings[x]}' for x in javawStrings if x in cfg.minecraft17Strings]

			if found:
				for hack in found:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			elif foundHeuristic:
				for hack in foundHeuristic:
					self.Check03 = 'failed'
					print(f' :' + Fore.RED + f' Not Clean ({hack})' + Fore.WHITE)
			else:
				print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Out of instance checks
	def outOfInstance(self):

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #04')
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

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #05')
		path = f'{self.user_path}/AppData/Local/Temp'

		found = [x for x in listdir(path) if isfile(f'{path}/{x}') if 'JNativeHook' in x and x.endswith('.dll')]

		if found:
			self.Check05 = 'failed'
			print(f' : ' + Fore.RED + f' Not Clean')
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	# Gets recently executed + deleted files
	def executedDeleted(self):

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #06')
		pcasvcPid = self.getPID('PcaSvc', service=True)
		explorerPid = self.getPID('explorer.exe')
		pcasvcStrings = self.dump(pcasvcPid)
		explorerStrings = self.dump(explorerPid)

		deleted = {}

		for string in pcasvcStrings:
			# string = string.lower()
			if string.startswith(self.drive_letter) and string.endswith('.exe'):
				if not os.path.isfile(string):

					if string in explorerStrings:
						filename = string.split('/')[-1]
						self.Check06 = 'failed'
						if self.deletedFiles == 'none':
							self.deletedFiles = string + ', '
						else:
							self.deletedFiles = self.deletedFiles + string + ', '
						deleted[string] = {'filename': string, 'method': '01'}

		if explorerStrings:
			for string in explorerStrings:
				string = string.lower()
				if 'trace' and 'pcaclient' in string:
					try:
						path = [x for x in string.split(',') if '.exe' in x][0]
						if not os.path.isfile(path):
							filename = path.split('/')[-1]
							deleted[path] = {'filename': path, 'method': '02'}
					except:
						continue

		if deleted:
			print(' :' + Fore.RED + ' Not Clean')
			print('')
			for path in deleted:
				print(f'	- {path}' + Fore.RED)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

		print('')

	# New method to detect deleted dll files.
	def deletedDLL(self):
		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #07')

		dllFiles = {}
		explorerPid = self.getPID('explorer.exe')
		explorerStrings = self.dump(explorerPid)

		if explorerStrings:
			for string in explorerStrings:
				if string.startswith(self.drive_letter) and string.endswith('.dll'):
					if not os.path.exists(string) and 'C:\Windows\system32' not in string and 'C:\Windows\System32' not in string:
						self.Check06 = 'failed'
						if self.deletedFiles == 'none':
							self.deletedFiles = string + ', '
						else:
							self.deletedFiles = self.deletedFiles + string + ', '
						dllFiles[string] = {'filename': string, 'method': '03'}

		if dllFiles is True:
			print(' :' + Fore.RED + ' Not Clean')
			print('')
			for path in dllFiles:
				print(f'	- {path}' + Fore.RED)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)
		print('')

	def checkScansHistory(self):

		print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #08')
		if cfg.enableDatabase is False:
			return

		Result02 = False
		Result03 = False
		Result04 = False
		Result05 = False

		query = f'SELECT Check02 FROM scans WHERE HWID = "{cfg.hwid}"'
		self.sqlCursor.execute(query)
		for Check02 in self.sqlCursor:
			if str(Check02) == '(\'failed\',)':
				Result02 = True

		query = f'SELECT Check03 FROM scans WHERE HWID = "{cfg.hwid}"'
		self.sqlCursor.execute(query)
		for Check03 in self.sqlCursor:
			if str(Check03) == '(\'failed\',)':
				Result03 = True

		query = f'SELECT Check04 FROM scans WHERE HWID = "{cfg.hwid}"'
		self.sqlCursor.execute(query)
		for Check04 in self.sqlCursor:
			if str(Check04) == '(\'failed\',)':
				Result04 = True

		query = f'SELECT Check05 FROM scans WHERE HWID = "{cfg.hwid}"'
		self.sqlCursor.execute(query)
		for Check05 in self.sqlCursor:
			if str(Check05) == '(\'failed\',)':
				Result05 = True
		allResults = ''

		if Result02 is True:
			allResults = 'Check #02, '
		if Result03 is True:
			allResults = allResults + 'Check #03, '
		if Result04 is True:
			allResults = allResults + 'Check #04, '
		if Result05 is True:
			allResults = allResults + 'Check #05'

		if 'Check' in allResults:
			print(' :' + Fore.RED + f' Not Clean ({allResults})' + Fore.WHITE)
		else:
			print(' :' + Fore.GREEN + ' Clean' + Fore.WHITE)

	@staticmethod
	def end():

		input('\nScan finished\nPress enter to exit..')
		# input('\nPress enter to exit...')
		temp = f'{Nex.drive_letter}/Windows/Temp/Nex'
		if os.path.exists(temp):
			shutil.rmtree(temp)
		exit()

	def saveScan(self):
		if self.deletedFiles is None:
			self.deletedFiles = 'none'

		if cfg.enableDatabase is False:
			return

		query = f'INSERT INTO Scans (ScanID, HWID, Check02, Check03, Check04, Check05, Check06, deletedFiles) VALUES '
		query = query + f'("{cfg.scanID}", "{cfg.hwid}", "{self.Check02}", "{self.Check03}", "{self.Check04}", '
		query = query + f'"{self.Check05}", "{self.Check06}", "{self.deletedFiles}")'

		self.sqlCursor.execute(query)
		self.sqlCnx.commit()


Nex = Nex()
Nex.asRoot()

if cfg.disableAuth is False:
	try:
		currentPin = input('Enter the pin to start : ')
		url = f'https://auth2.atome.cc/index.php?pin={currentPin}'
		r = requests.get(url)

		if 'verified' not in r.text:
			quit()
	except:
		input('An error has occured...\nPress enter to exit')
		quit()

os.system('cls')
Nex.connectDatabase()
Nex.mcProcess()
Nex.dependencies()


print(f'{cfg.prefix} Starting Scan with ID: {cfg.scanID}\n')
# print(f'{cfg.prefix} HWID : {cfg.hwid}\n')

# Check #01
Nex.recordingCheck()

# Check #02
Nex.modificationTimes()

# Check #03
Nex.inInstance()

# Check #04
Nex.outOfInstance()

# Check #05
Nex.jnativehook()

# Check #06
Nex.executedDeleted()

# Check #07
Nex.deletedDLL()

# Check #08
if cfg.enableCheck08 is True and cfg.enableDatabase is True:
	Nex.checkScansHistory()
else:
	print(end=f'{cfg.prefix}' + Fore.CYAN + ' Running check #08' + ' :' + Fore.YELLOW + ' Skipped' + Fore.WHITE)


Nex.saveScan()
Nex.end()
