import subprocess, sys, textwrap

def cl():
	subprocess.run('clear')

def format(input, indent):
	return textwrap.indent(textwrap.fill(input), indent)

def fixPermissions():
	user = subprocess.check_output('whoami', text=True).strip()
	path = sys.argv[0]
	optionOne = f"{textwrap.fill('Rerun this program with sudo in order to allow full privilege.', break_long_words=False)}\n\t\t>> \033[32msudo python {path}\033[0m"
	optionTwo = f"""Add an entry to the sudoers list to allow NOPASSWD access.
\t\t>> \033[32msudo visudo\033[0m
\tThen add the line below to the end of the file:
{format(f">> \033[32m{user} ALL=ALL NOPASSWD: /usr/bin/python4 {path}\033[0m", "\t\t")}"""

	print(f"""Options to fix permission errors
1. (\033[32mMost Recomended\033[0m) {optionOne}
\n2. (\033[33mSecond Best\033[0m) {optionTwo}
\n3. (\033[31mMost Tedious Method\033[0m) Enter 'p' now to be prompted for password at every sudo call.
{format("\033[34mNote:\033[0m We ask for your credential at each call so that we don't store sensitive data in this program and increase security.", "\t")}
""")

	action = str(input("\nOption [1, 2, 3/p]: ")).lower()
	askOpts = ["3", "p"]
	if action in askOpts:
		return True
	print("Rerun the program once handled!")
	if action == "1":
		return optionOne
	elif action == "2":
		return optionTwo
	else:
		print("Unrecognized input")
		return False

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

def repairDrivers(drivers, askSudo):
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
