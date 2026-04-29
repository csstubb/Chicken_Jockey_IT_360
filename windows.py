import subprocess

def getDrivers()
	return subprocess("driverquery", capture_out=True, text=True)
