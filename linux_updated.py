import subprocess
import sys
import textwrap

def cl():
    subprocess.run(["clear"])

def format_text(input_text, indent):
    return textwrap.indent(textwrap.fill(input_text), indent)

def fixPermissions():
    user = subprocess.check_output(["whoami"], text=True).strip()
    path = sys.argv[0]

    optionOne = (
        f"{textwrap.fill('Rerun this program with sudo in order to allow full privilege.', break_long_words=False)}"
        f"\n\t\t>> \033[32msudo python3 {path}\033[0m"
    )

    optionTwo = f"""Add an entry to the sudoers list to allow NOPASSWD access.
\t\t>> \033[32msudo visudo\033[0m
\tThen add the line below to the end of the file:
{format_text(f">> \033[32m{user} ALL=ALL NOPASSWD: /usr/bin/python3 {path}\033[0m", "\t\t")}"""

    print(f"""Options to fix permission errors
1. (\033[32mMost Recommended\033[0m) {optionOne}

2. (\033[33mSecond Best\033[0m) {optionTwo}

3. (\033[31mMost Tedious Method\033[0m) Enter 'p' now to be prompted for password at every sudo call.
{format_text("\033[34mNote:\033[0m We ask for your credential at each call so that we don't store sensitive data in this program and increase security.", "\t")}
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
        if "[" in block and "]" in block and ":" in block and block.find(":") < block.find("]"):
            return block.strip()
    print("\033[31mDriver ID not Found\033[0m")
    return None

def getInstanceName(driverID):
    if driverID is None:
        return "No driver ID found"

    clean_id = driverID.strip("[").strip("]")

    try:
        driver = subprocess.check_output(
            ["lspci", "-nnk", "-d", clean_id],
            text=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return "Unable to read driver details"

    for line in driver.split("\n"):
        if "Kernel driver in use:" in line:
            return line.split(":", 1)[1].strip()

    return "No active kernel driver attached"

def shouldIgnoreDevice(driver):
    ignored_devices = [
        "Host bridge",
        "ISA bridge",
        "PCI bridge",
        "SMBus",
        "System peripheral"
    ]

    for item in ignored_devices:
        if item.lower() in driver.lower():
            return True

    return False

def getFaultDrivers():
    try:
        drivers = subprocess.check_output(
            ["lspci", "-nnkq"],
            text=True,
            stderr=subprocess.DEVNULL
        ).split("\n\n")
    except FileNotFoundError:
        print("\033[31mlspci was not found. Install it with: sudo apt install pciutils -y\033[0m")
        return []
    except subprocess.CalledProcessError as e:
        print(f"\033[31mFailed to run lspci: {e}\033[0m")
        return []

    problemDrivers = []

    for driver in drivers:
        if len(driver.strip()) == 0:
            continue

        if shouldIgnoreDevice(driver):
            continue

        if "Kernel driver in use" not in driver:
            problemDrivers.append(driver.split("\n")[0])

    if problemDrivers:
        print("\033[33mPossible Problem Drivers\033[0m")
        for driver in problemDrivers:
            print(f"\033[31m[-]\033[0m {driver}")
    else:
        print("\033[32mAll detected PCI drivers appear healthy\033[0m")

    return problemDrivers

def repairDrivers(drivers, askSudo=False):
    if not isinstance(drivers, list):
        print("\033[31mWrong Data Type for repairDrivers!!\033[0m")
        return None

    if len(drivers) == 0:
        print("No problem drivers. Exiting repairDrivers")
        return None

    driverIDs = []

    for driver in drivers:
        print("Getting Driver ID...", end="")
        driverID = getInstanceID(driver)
        driverIDs.append(driverID)
        print(driverID)

    driverNames = []

    for driverID in driverIDs:
        print("Getting Driver Name...", end="")
        driverName = getInstanceName(driverID)
        print(driverName)
        driverNames.append(driverName)

        if driverName == "No active kernel driver attached":
            print("\033[33mNo automatic repair was attempted because no active driver was found.\033[0m")
            print("\033[33mRecommended action: check the device vendor and install the correct driver package if needed.\033[0m")
        else:
            print(f"\033[34mRecommended repair command if the driver needs to be reloaded:\033[0m sudo modprobe {driverName}")

    return driverNames
