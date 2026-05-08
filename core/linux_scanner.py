import subprocess
import os
import re
from datetime import datetime

class LinuxDriverScanner:
	"""
	Collects raw driver metadata on Linux using:
	- lspci: PCI device and kernel module info
	- lsmod: currently loaded kernel modules
	- modinfo: detailed metadata per module
	- dmesg: kernel ring buffer for driver errors
	- lsusb: USB device drivers
	"""

	def scanAll(self):
		"""Run all scans and return a unified driver list."""
		print("      Collecting PCI device and driver list...")
		pciDrivers = self._scanPCI()

		print("      Collecting loaded kernel modules...")
		loadedModules = self._scanLoadedModules()

		print("      Collecting module metadata...")
		moduleDetails = self._scanModuleDetails(loadedModules)

		print("      Reading dmesg for driver errors...")
		dmesgErrors = self._scanDmesg()

		print("      Collecting USB driver info...")
		usbDrivers = self._scanUSB()

		print("      Collecting GPU driver info...")
		gpuDrivers = self._scanGPU()

		merged = self._mergeAll(pciDrivers, moduleDetails, dmesgErrors, usbDrivers, gpuDrivers)
		return merged

	def _run(self, command, timeout=15):
		"""Helper to run a shell command and return stdout."""
		try:
			result = subprocess.run(
				command, capture_output=True, text=True, timeout=timeout
			)
			return result.stdout.strip()
		except FileNotFoundError:
			print(f"\033[33m      Command not found: {command[0]} (install it and retry)\033[0m")
			return ""
		except Exception as e:
			print(f"\033[31m      Error running {command[0]}: {e}\033[0m")
			return ""

	def _scanPCI(self):
		"""Use lspci -nnkq to get PCI devices and their kernel drivers."""
		output = self._run(["lspci", "-nnkq"])
		drivers = []
		if not output:
			return drivers

		# Each device block is separated by a blank line
		blocks = output.strip().split("\n\n")
		for block in blocks:
			if not block.strip():
				continue
			lines = block.strip().split("\n")
			entry = {
				"name": lines[0] if lines else "Unknown PCI Device",
				"kernelDriver": None,
				"kernelModules": [],
				"type": "PCI",
				"source": "lspci"
			}
			for line in lines[1:]:
				line = line.strip()
				if "Kernel driver in use:" in line:
					entry["kernelDriver"] = line.split(":", 1)[1].strip()
				elif "Kernel modules:" in line:
					mods = line.split(":", 1)[1].strip()
					entry["kernelModules"] = [m.strip() for m in mods.split(",")]
			drivers.append(entry)
		return drivers

	def _scanLoadedModules(self):
		"""Use lsmod to get all currently loaded kernel modules."""
		output = self._run(["lsmod"])
		modules = []
		for line in output.split("\n")[1:]:  # Skip header
			parts = line.split()
			if parts:
				modules.append(parts[0])
		return modules

	def _scanModuleDetails(self, modules):
		"""Use modinfo to get detailed metadata for each loaded module."""
		details = []
		for module in modules:
			output = self._run(["modinfo", module])
			if not output:
				continue
			info = {"moduleName": module, "source": "modinfo"}
			for line in output.split("\n"):
				if ":" in line:
					key, _, value = line.partition(":")
					key = key.strip().lower()
					value = value.strip()
					if key == "description":
						info["name"] = value
					elif key == "version":
						info["version"] = value
					elif key == "author":
						info["manufacturer"] = value
					elif key == "filename":
						info["filename"] = value
					elif key == "date":
						info["date"] = value
					elif key == "signature":
						info["signed"] = True
					elif key == "sig_key":
						info["sigKey"] = value
			if "signed" not in info:
				info["signed"] = False
			if "name" not in info:
				info["name"] = module
			details.append(info)
		return details

	def _scanDmesg(self):
		"""Parse dmesg for driver-related errors and warnings."""
		output = self._run(["dmesg", "--level=err,warn", "--notime"], timeout=10)
		errors = []
		driverKeywords = ["driver", "module", "firmware", "kernel", "device", "failed", "error"]
		for line in output.split("\n"):
			lineLower = line.lower()
			if any(kw in lineLower for kw in driverKeywords):
				errors.append(line.strip())
		return errors

	def _scanUSB(self):
		"""Use lsusb to collect USB device info."""
		output = self._run(["lsusb"])
		devices = []
		for line in output.split("\n"):
			if line.strip():
				devices.append({
					"name": line.strip(),
					"type": "USB",
					"source": "lsusb",
					"signed": True,  # USB devices don't have signatures in the same way
					"version": "Unknown",
					"manufacturer": "Unknown",
					"eventErrors": []
				})
		return devices

	def _scanGPU(self):
		"""Try to detect GPU driver using glxinfo or nvidia-smi."""
		gpus = []

		# Try nvidia-smi first
		output = self._run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
		if output:
			for line in output.split("\n"):
				parts = line.split(",")
				if len(parts) >= 2:
					gpus.append({
						"name": parts[0].strip(),
						"version": parts[1].strip(),
						"type": "GPU",
						"manufacturer": "NVIDIA",
						"source": "nvidia-smi",
						"signed": True,
						"eventErrors": []
					})

		# Try lspci for AMD/Intel GPU if no NVIDIA found
		if not gpus:
			output = self._run(["lspci", "-nnk"])
			for block in output.split("\n\n"):
				if "vga" in block.lower() or "display" in block.lower() or "3d" in block.lower():
					lines = block.strip().split("\n")
					entry = {
						"name": lines[0] if lines else "Unknown GPU",
						"type": "GPU",
						"source": "lspci-gpu",
						"signed": True,
						"version": "Unknown",
						"manufacturer": "Unknown",
						"eventErrors": []
					}
					for line in lines[1:]:
						if "Kernel driver in use:" in line:
							entry["version"] = line.split(":", 1)[1].strip()
					gpus.append(entry)

		return gpus

	def _mergeAll(self, pciDrivers, moduleDetails, dmesgErrors, usbDrivers, gpuDrivers):
		"""Combine all sources into a unified driver list."""
		merged = []

		# Build a lookup of module details by module name
		moduleMap = {m["moduleName"]: m for m in moduleDetails}

		for pci in pciDrivers:
			entry = {
				"name": (pci.get("name") or "Unknown PCI Device"),
				"version": "Unknown",
				"manufacturer": "Unknown",
				"signed": False,
				"type": pci.get("type", "PCI"),
				"source": "lspci",
				"kernelDriver": pci.get("kernelDriver"),
				"eventErrors": []
			}

			# Enrich with modinfo data if we have it for this driver
			kernelDriver = pci.get("kernelDriver")
			if kernelDriver and kernelDriver in moduleMap:
				mod = moduleMap[kernelDriver]
				entry["version"] = mod.get("version", "Unknown")
				entry["manufacturer"] = mod.get("manufacturer", "Unknown")
				entry["signed"] = mod.get("signed", False)
				entry["filename"] = mod.get("filename", "")
				entry["date"] = mod.get("date", "")

			# Attach relevant dmesg errors
			nameLower = entry["name"].lower()
			driverName = (kernelDriver or "").lower()
			for error in dmesgErrors:
				if nameLower in error.lower() or (driverName and driverName in error.lower()):
					entry["eventErrors"].append({"message": error})

			merged.append(entry)

		# Add USB devices
		merged.extend(usbDrivers)

		# Add GPU entries
		for gpu in gpuDrivers:
			# Attach any dmesg errors mentioning the GPU
			for error in dmesgErrors:
				if "gpu" in error.lower() or "nvidia" in error.lower() or "amd" in error.lower() or "radeon" in error.lower():
					gpu["eventErrors"].append({"message": error})
			merged.append(gpu)

		return merged
