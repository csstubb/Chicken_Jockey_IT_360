import subprocess

def getInstanceID(driver):
	for block in driver.split(" "):
		if "[" in block and "]" in block and ":" in block and block.find(':') < block.find(']'):
			print(block)
			return block
	print("\033[31mDriver ID not Found\033[0m")
	return None

def getInstanceName(driverID):
	driver = subprocess.check_output(["lspci", "-nnk", "-d", driverID.strip("[").strip("]")], text=True).replace("\n", "")
	for line in driver.lower().split("\t"):
		if "kernel" in line:
			return line[line.find(":") + 2:]
	return "\033[31mUnable to resolve driver name!!\033[0m"

def getFaultDrivers():
	drivers = subprocess.check_output(["lspci", "-nnkq"], text=True).split('\n\n')
	problemDrivers = []
	for driver in drivers:
		if "Kernal driver in use" not in driver and len(driver) > 0:
			problemDrivers.append(driver.split('\n')[0])

	if problemDrivers:
		print("\033[33mPossible Problem Drivers\033[0m")
		for driver in problemDrivers:
			print(f"\033[31m[-]\033[0m {driver}")
	else:
		print("\033[32mAll detectedPCI drivers are healthy\033[0m")
	return problemDrivers

def repairDrivers(drivers):
	if not isinstance(drivers, list):
		print("\033[31Wrong Data Type for repairDrivers!!\033[0m")
		return None
	if len(drivers) == 0:
		print("No problem drivers. Exiting repairDrivers")
		return None
	driverIDs = []
	for driver in drivers:
		print("Getting Driver ID...", end="")
		driverID = getInstanceID(driver)
		driverIDs.append(driverID)

	driverNames = []
	for driverID in driverIDs:
		print(f"Getting Driver Name...", end="")
		driverName = getInstanceName(driverID)
		print(driverName)
		driverNames.append(driverName)
