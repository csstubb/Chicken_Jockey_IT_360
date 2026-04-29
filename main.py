import os, sys

lib = None
if(sys.platform == "linux"):
	#Linux
	try:
		import linux
		print("\033[32mlinux.py Loaded\033[0m")
		lib = linux
	except Exception as e:
		print(f"\033[31mLinux detected as OS. Unable to load linux.py!!\nError: {e}\033[0m")
elif(sys.platform == "win32"):
	#Windows
	try:
		import windows
		print("\033[32mwindows.py Loaded\033[0m")
		lib = windows
	except Exception as e:
		print(f"\033[31mWindows detected as OS. Unable to load windows.py!!\nError: {e}\033[0m")
elif(sys.platform == "darwin"):
	#MacOS
	print("Mac Detected")
else:
	print("\033[31mUnrecognized OS!!\033[0m")
	exit(0)

if lib == None:
	print("Exiting")
	exit(0)

print("Getting Drivers...")
try:
	print(str(lib.getDrivers().stdout.strip()))
except Exception as e:
	print(f"\033[31mUnexpected Error: {e}\033[0m")
