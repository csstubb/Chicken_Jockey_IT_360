import subprocess

def getInstanceID(driver):
	lines = driver.split("\n")
	instanceID = None
	for line in lines:
		if "instance id" in line.lower():
			for word in line.split("  "):
				if "Instance ID:" not in word and " " not in word:
					instanceID = word
	if instanceID is not None:	
		return instanceID	

def getFaultDrivers(array=True):
	drivers = subprocess.run("pnputil /enum-devices /problem", capture_output=True, text=True).stdout.strip()
	popList = drivers.split("\n")
	for index in range(0, len(popList)):
		catchLast = False
		if "microsoft pnp utility" in popList[index].lower() or catchLast:
			print("Line: " + popList[index])
			popList[index] = ""
			if catchLast:
				catchLast = False
			else:
				catchLast = True
		
	drivers = "\n".join(popList)
	print({"microsoft pnp utility" in drivers.lower()})
	return drivers.split("\n\n") if array else drivers

def repairDrivers(drivers):
	if not isinstance(drivers, list):
		print("\033[31mWrong Data Type for repairDrivers!!\033[0m")
		return None
	driverIDs = []
	for driver in drivers:
		print(driver + "\n\nGetting Driver IDs...", end="")
		driverID = getInstanceID(driver)
		driverIDs.append(driverID)
		print(driverID)