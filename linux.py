import subprocess

def getDrivers():
	return subprocess.run("lsmod", capture_output=True, text=True)
