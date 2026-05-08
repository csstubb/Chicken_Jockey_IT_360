import os, sys

def exitStatement(code):
	color = "\033[0m"
	if code == 0:
		color = "\033[32m"
	print(f"{color}Exiting with code: {code}\033[0m")
	exit(code)

def getUID():
	## UID 0 is root
	return os.getuid()

def printStatus(data):
	if isinstance(data, list):
		data = "\n\n".join(data)
	printString = ""
	for line in data.split("\n"):
		if "problem" in line.lower():
			line = f"\033[33m{line}\033[0m"
		if "disabled" in line.lower():
			line = f"\033[31m{line}\033[0m"
		printString += line + "\n"
	print(printString)

lib = None
platform = sys.platform
if(platform == "linux"):
	#Linux
	try:
		import linux as lib
		lib.cl()
		print("\033[32mlinux.py Loaded\033[0m")
	except Exception as e:
		print(f"\033[31mLinux detected as OS. Unable to load linux.py!!\nError: {e}\033[0m")
elif(platform == "win32"):
	#Windows
	try:
		import windows as lib
		lib.cl()
		print("\033[32mwindows.py Loaded\033[0m")
	except Exception as e:
		print(f"\033[31mWindows detected as OS. Unable to load windows.py!!\nError: {e}\033[0m")
elif(platform == "darwin"):
	#MacOS
	print("Mac Detected")
else:
	print("\033[31mUnrecognized OS!!\033[0m")
	exit(0)

if lib == None:
	print("Exiting")
	exit(0)

try:
	#fix = False
	if getUID() != 0:
		print("\033[31mNot Running as Root. Please follow one of the solutions below\033[0m")
		#fix = lib.fixPermissions()
		#lib.cl()
		#if isinstance(fix, str):
		#	print(fix)
		#	exitStatement(0)
	print("\nGetting Problem Drivers...")
	drivers = lib.getFaultDrivers()
	if platform != "linux":
		printStatus(drivers)
	if len(drivers) > -1: #<----- Change to 0 for push
		fix = False
		if getUID() != 0:
			print("\033[31mNot Running as Root. Please follow one of the solutions below\033[0m")
			fix = lib.fixPermissions()
			lib.cl()
			if isinstance(fix, str):
				print(fix)
				exitStatement(0)
		lib.repairDrivers(drivers, fix)
except Exception as e:
	print(f"\033[31mException Error: {e}\033[0m")
