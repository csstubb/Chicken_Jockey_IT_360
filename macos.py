import subprocess
import re

def getInstanceID(driver):
  # Get a driver ID from the driver info
  for line in driver.split("\n"):
    if "IORegistryEntryName" in line or "CFBundleIdentifier" in line:
      match = re.search(r'=\s*"?([^"\n]+)"?', line)
      if match:
        return match.group(1).strip()
  print("\033[31mDriver ID not Found\033[0m")
  return None

def getInstanceName(driverID):
  # Try to get a readable driver name
  try:
    output = subprocess.check_output(
      ["ioreg", "-r", "-c", driverID],
      text=True,
      stderr=subprocess.DEVNULL
    )
    for line in output.split("\n"):
      if "IOProviderClass" in line or "IOClass" in line:
        match = re.search(r'"([^"]+)"$', line)
        if match:
          return match.group(1)
  except subprocess.CalledProcessError:
    pass

  # Return ID if no name is found
  return driverID

def getFaultDrivers():
  # Look for drivers that may have issues
  try:
    output = subprocess.check_output(
      ["ioreg", "-l", "-w", "0"],
      text=True,
      stderr=subprocess.DEVNULL
    )
  except subprocess.CalledProcessError as e:
    print(f"\033[31mFailed to run ioreg: {e}\033[0m")
    return []

  problemDrivers = []
  currentDevice = []
  hasDriver = False

  for line in output.split("\n"):

    # New device section
    if "+-o" in line:

      # Check previous device
      if currentDevice and not hasDriver:
        entry = "\n".join(currentDevice)

        # Only keep hardware devices
        if "IOPCIDevice" in entry or "IOUSBDevice" in entry or "IOAHCIDevice" in entry:
          problemDrivers.append(entry)

      currentDevice = [line]
      hasDriver = False

    else:
      currentDevice.append(line)

      # Check if device has a loaded driver
      if "CFBundleIdentifier" in line or "IOKitDebug" in line:
        hasDriver = True

  if problemDrivers:
    print("\033[33mPossible Problem Drivers\033[0m")

    for driver in problemDrivers:
      # Print device name
      print(f"\033[31m[-]\033[0m {driver.split(chr(10))[0].strip()}")

  else:
    print("\033[32mAll detected drivers appear healthy\033[0m")

  return problemDrivers

def repairDrivers(drivers):
  # Try to reload problem drivers

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

    if driverID is not None:
      driverIDs.append(driverID)
      print(driverID)

    else:
      print(f"\033[31mSkipping driver — could not resolve ID\033[0m")

  driverNames = []

  for driverID in driverIDs:
    print(f"Getting Driver Name...", end="")

    driverName = getInstanceName(driverID)

    print(driverName)
    driverNames.append(driverName)

    # Try to reload driver with kmutil
    print(f"Attempting to reload kext for: {driverName}")

    try:
      result = subprocess.run(
        ["kmutil", "load", "-b", driverID],
        capture_output=True,
        text=True
      )

      if result.returncode == 0:
        print(f"\033[32m[+] Successfully reloaded: {driverName}\033[0m")

      else:
        print(f"\033[31m[-] Failed to reload {driverName}: {result.stderr.strip()}\033[0m")
        print("\033[33m    Note: kext loading requires root privileges (sudo)\033[0m")

    except FileNotFoundError:

      # Use kextload if kmutil is not available
      try:
        subprocess.run(["kextload", "-b", driverID], check=True)

        print(f"\033[32m[+] Successfully reloaded via kextload: {driverName}\033[0m")

      except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\033[31m[-] Could not reload {driverName}: {e}\033[0m")

  return driverNames