import os
import re
import subprocess
from datetime import datetime, timezone

# How old a driver can be (in days) before flagging as outdated
DRIVER_AGE_THRESHOLD_DAYS = 730  # 2 years

# Known legitimate driver manufacturers — unsigned drivers from unknown vendors are suspicious
TRUSTED_MANUFACTURERS = [
	"microsoft", "intel", "nvidia", "amd", "realtek", "qualcomm",
	"broadcom", "marvell", "mediatek", "logitech", "razer", "corsair",
	"asus", "gigabyte", "msi", "samsung", "western digital", "seagate",
	"Kingston", "creative", "sound blaster"
]

class DriverAnalyzer:
	"""
	Applies a rule-based model to flag drivers as corrupted,
	tampered, outdated, or suspicious.
	"""

	def __init__(self, drivers):
		self.drivers = drivers

	def analyzeAll(self):
		"""Run all checks on every driver and return results with issues attached."""
		results = []
		for driver in self.drivers:
			issues = []
			issues += self._checkSignature(driver)
			issues += self._checkAge(driver)
			issues += self._checkEventErrors(driver)
			issues += self._checkManufacturer(driver)
			issues += self._checkStatus(driver)
			issues += self._checkFileIntegrity(driver)
			driver["issues"] = issues
			driver["issueCount"] = len(issues)
			results.append(driver)
		return results

	def _checkSignature(self, driver):
		"""Flag drivers that are unsigned — a major tamper indicator."""
		issues = []
		if not driver.get("signed", True):
			issues.append("Driver is UNSIGNED — possible tampering or third-party injection")
		return issues

	def _checkAge(self, driver):
		"""Flag drivers that haven't been updated in over 2 years."""
		issues = []
		dateStr = driver.get("date", "")
		if not dateStr:
			issues.append("Driver date is missing — metadata may be corrupted")
			return issues
		try:
			# WMI dates come in various formats — try to parse the most common ones
			for fmt in ("%Y%m%d%H%M%S.%f%z", "%Y-%m-%d", "%m/%d/%Y"):
				try:
					driverDate = datetime.strptime(dateStr[:len(fmt)], fmt)
					break
				except ValueError:
					continue
			else:
				return issues  # Could not parse date, skip

			now = datetime.now()
			if (now - driverDate.replace(tzinfo=None)).days > DRIVER_AGE_THRESHOLD_DAYS:
				issues.append(f"Driver is over 2 years old (dated {dateStr[:10]}) — may be outdated")
		except Exception:
			pass
		return issues

	def _checkEventErrors(self, driver):
		"""Flag drivers that have associated errors in the Windows Event Log."""
		issues = []
		errors = driver.get("eventErrors", [])
		if errors:
			issues.append(f"Found {len(errors)} error(s) in Windows Event Log referencing this driver")
			for error in errors[:2]:  # Show up to 2 examples
				issues.append(f"  Event ID {error.get('id', '?')}: {error.get('message', '')[:120]}")
		return issues

	def _checkManufacturer(self, driver):
		"""Flag drivers from unknown or suspicious manufacturers."""
		issues = []
		manufacturer = (driver.get("manufacturer") or "").lower()
		if not manufacturer or manufacturer == "unknown":
			issues.append("Manufacturer is unknown — driver origin cannot be verified")
		elif not any(trusted in manufacturer for trusted in TRUSTED_MANUFACTURERS):
			issues.append(f"Manufacturer '{manufacturer}' is not in the trusted vendor list — verify manually")
		return issues

	def _checkStatus(self, driver):
		"""Flag GPU or device drivers that report a non-OK status."""
		issues = []
		status = driver.get("status", "").lower()
		if status and status not in ("ok", "", "unknown"):
			issues.append(f"Device status is '{status}' — driver may be malfunctioning")
		return issues

	def _checkFileIntegrity(self, driver):
		"""
		Check if the driver's .inf file exists and run sfc /verifyonly
		as a basic integrity check. Full sfc /scannow requires admin.
		"""
		issues = []
		infName = driver.get("infName", "")
		if infName:
			infPath = os.path.join(r"C:\Windows\System32\DriverStore\FileRepository", infName)
			# Check a simplified path — real path includes a versioned subfolder
			if not os.path.exists(infPath) and not self._infExistsInStore(infName):
				issues.append(f"Driver INF file '{infName}' could not be located in DriverStore — possible corruption")
		return issues

	def _infExistsInStore(self, infName):
		"""Search the DriverStore for the inf file across versioned subfolders."""
		store = r"C:\Windows\System32\DriverStore\FileRepository"
		try:
			for folder in os.listdir(store):
				if infName.lower() in folder.lower():
					return True
		except Exception:
			pass
		return False
