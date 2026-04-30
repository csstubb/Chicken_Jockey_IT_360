import subprocess

def getFaultDrivers():
	return subprocess.run(["lsmod", "dmesg | grep -iE 'error|fail|taint'"], capture_output=True, text=True)
