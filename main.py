import os, sys



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
		print("\033[32mlinux.py Loaded\033[0m")
	except Exception as e:
		print(f"\033[31mLinux detected as OS. Unable to load linux.py!!\nError: {e}\033[0m")
elif(platform == "win32"):
	#Windows
	try:
		import windows as lib
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

print("Getting Problem Drivers...")
#Linux on gets drivers

try:
	drivers = lib.getFaultDrivers()
	if platform != "linux":
		printStatus(drivers)
	lib.repairDrivers(drivers)
except Exception as e:
	print(f"\033[31mException Error: {e}\033[0m")
