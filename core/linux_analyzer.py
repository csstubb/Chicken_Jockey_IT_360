import os
import re
import subprocess

# Trusted kernel module manufacturers/authors
TRUSTED_AUTHORS = [
	"linux kernel", "intel", "nvidia", "amd", "realtek", "qualcomm",
	"broadcom", "microsoft", "red hat", "canonical", "linus torvalds",
	"kernel.org", "free software", "open source"
]

# Modules known to be commonly problematic or suspicious
SUSPICIOUS_MODULES = [
	"rootkit", "hide", "intercept", "hook"
]

# Expected location for legitimate kernel modules
VALID_MODULE_PATHS = [
	"/lib/modules",
	"/usr/lib/modules"
]

class LinuxDriverAnalyzer:
	"""
	Applies Linux-specific rule-based checks to flag drivers as:
	- Unsigned / unverified
	- Loaded from suspicious paths
	- Missing kernel driver (device has no module bound)
	- Flagged in dmesg
	- From unknown authors
	- Potentially tampered (loaded from outside standard paths)
	"""

	def __init__(self, drivers):
		self.drivers = drivers
		self.kernelVersion = self._getKernelVersion()

	def analyzeAll(self):
		"""Run all checks on every driver and return results with issues attached."""
		results = []
		for driver in self.drivers:
			issues = []
			issues += self._checkSignature(driver)
			issues += self._checkModulePath(driver)
			issues += self._checkMissingDriver(driver)
			issues += self._checkDmesgErrors(driver)
			issues += self._checkAuthor(driver)
			issues += self._checkSuspiciousName(driver)
			issues += self._checkOutOfTreeModule(driver)
			driver["issues"] = issues
			driver["issueCount"] = len(issues)
			results.append(driver)
		return results

	def _getKernelVersion(self):
		"""Get the running kernel version for module path validation."""
		try:
			return subprocess.check_output(["uname", "-r"], text=True).strip()
		except Exception:
			return ""

	def _checkSignature(self, driver):
		"""Flag unsigned kernel modules — a key tamper indicator on Linux."""
		issues = []
		if not driver.get("signed", True):
			issues.append("Module is UNSIGNED — not verified by kernel module signing. Possible tampering or third-party injection")
		return issues

	def _checkModulePath(self, driver):
		"""Flag modules loaded from outside standard kernel module directories."""
		issues = []
		filename = driver.get("filename", "")
		if not filename:
			return issues
		# Check if loaded from a legitimate path
		if not any(filename.startswith(path) for path in VALID_MODULE_PATHS):
			issues.append(f"Module loaded from non-standard path: '{filename}' — verify this is legitimate")
		return issues

	def _checkMissingDriver(self, driver):
		"""Flag PCI devices that have no kernel driver bound to them."""
		issues = []
		if driver.get("source") == "lspci" and driver.get("kernelDriver") is None:
			issues.append("PCI device has no kernel driver bound — device may be unsupported, disabled, or driver failed to load")
		return issues

	def _checkDmesgErrors(self, driver):
		"""Flag drivers with associated errors in the kernel ring buffer."""
		issues = []
		errors = driver.get("eventErrors", [])
		if errors:
			issues.append(f"Found {len(errors)} error(s) in dmesg referencing this driver")
			for error in errors[:2]:
				msg = error.get("message", "")
				if msg:
					issues.append(f"  dmesg: {msg[:120]}")
		return issues

	def _checkAuthor(self, driver):
		"""Flag modules from unknown or unrecognized authors."""
		issues = []
		manufacturer = (driver.get("manufacturer") or "").lower()
		if not manufacturer or manufacturer == "unknown":
			# Only flag this for non-USB/non-PCI-stub entries that have modinfo data
			if driver.get("source") == "modinfo":
				issues.append("Module author is unknown — origin cannot be verified")
		elif not any(trusted in manufacturer for trusted in TRUSTED_AUTHORS):
			issues.append(f"Module author '{manufacturer}' is not a recognized vendor — verify manually")
		return issues

	def _checkSuspiciousName(self, driver):
		"""Flag modules whose names contain known suspicious keywords."""
		issues = []
		name = (driver.get("name") or "").lower()
		moduleName = (driver.get("moduleName") or "").lower()
		for keyword in SUSPICIOUS_MODULES:
			if keyword in name or keyword in moduleName:
				issues.append(f"Module name contains suspicious keyword '{keyword}' — investigate immediately")
		return issues

	def _checkOutOfTreeModule(self, driver):
		"""
		Flag modules that aren't part of the mainline kernel tree.
		Out-of-tree modules show '(OE)' or similar in modinfo on some distros,
		or live outside the versioned kernel module directory.
		"""
		issues = []
		filename = driver.get("filename", "")
		if filename and self.kernelVersion:
			# A legitimate in-tree module path includes the kernel version
			if self.kernelVersion not in filename and any(filename.startswith(p) for p in VALID_MODULE_PATHS):
				issues.append(f"Module may be out-of-tree (kernel version '{self.kernelVersion}' not in path '{filename}') — could be a third-party or DKMS module")
		return issues
