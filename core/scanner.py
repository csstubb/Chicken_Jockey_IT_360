import subprocess
import json
import os
import re
from datetime import datetime

class DriverScanner:
	"""
	Collects raw driver metadata from Windows-native sources.
	Uses pnputil, Get-WmiObject, sigverif data, and the Windows Event Log.
	"""

	def scanAll(self):
		"""Run all scans and merge results into a unified driver list."""
		print("      Collecting PnP driver list...")
		pnpDrivers = self._scanPnP()

		print("      Collecting WMI driver metadata...")
		wmiDrivers = self._scanWMI()

		print("      Checking driver signatures...")
		self._mergeSignatures(pnpDrivers, wmiDrivers)

		print("      Reading Windows Event Log for driver errors...")
		eventErrors = self._scanEventLog()

		print("      Collecting GPU driver info...")
		gpuDrivers = self._scanGPU()

		print("      Collecting CPU info...")
		cpuInfo = self._scanCPU()

		# Merge all sources into one list keyed by driver name
		merged = self._mergeAll(pnpDrivers, wmiDrivers, eventErrors, gpuDrivers, cpuInfo)
		return merged

	def _runPowerShell(self, command):
		"""Helper to run a PowerShell command and return stdout."""
		try:
			result = subprocess.run(
				["powershell", "-NoProfile", "-Command", command],
				capture_output=True, text=True, timeout=30
			)
			return result.stdout.strip()
		except Exception as e:
			print(f"\033[31m      PowerShell error: {e}\033[0m")
			return ""

	def _scanPnP(self):
		"""Use pnputil to list all driver packages with metadata."""
		drivers = []
		try:
			output = subprocess.run(
				["pnputil", "/enum-drivers"],
				capture_output=True, text=True
			).stdout
			# Each driver block is separated by a blank line
			blocks = output.strip().split("\n\n")
			for block in blocks:
				if not block.strip():
					continue
				driver = {}
				for line in block.split("\n"):
					if ":" in line:
						key, _, value = line.partition(":")
						driver[key.strip()] = value.strip()
				if driver:
					drivers.append(driver)
		except Exception as e:
			print(f"\033[31m      pnputil error: {e}\033[0m")
		return drivers

	def _scanWMI(self):
		"""Use WMI (via PowerShell) to get detailed driver info."""
		cmd = """
		Get-WmiObject Win32_PnPSignedDriver |
		Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer, IsSigned, DeviceID, InfName |
		ConvertTo-Json -Depth 2
		"""
		output = self._runPowerShell(cmd)
		try:
			data = json.loads(output)
			if isinstance(data, dict):
				data = [data]
			return data if data else []
		except Exception:
			return []

	def _mergeSignatures(self, pnpDrivers, wmiDrivers):
		"""Check driver signatures using PowerShell Get-AuthenticodeSignature."""
		cmd = """
		Get-WmiObject Win32_PnPSignedDriver |
		Where-Object { $_.IsSigned -eq $false } |
		Select-Object DeviceName, InfName |
		ConvertTo-Json -Depth 2
		"""
		output = self._runPowerShell(cmd)
		try:
			unsigned = json.loads(output)
			if isinstance(unsigned, dict):
				unsigned = [unsigned]
			for driver in unsigned or []:
				name = driver.get("DeviceName", "")
				for wmi in wmiDrivers:
					if wmi.get("DeviceName") == name:
						wmi["unsigned"] = True
		except Exception:
			pass

	def _scanEventLog(self):
		"""Pull driver-related errors from the Windows System Event Log."""
		cmd = """
		Get-WinEvent -LogName System -MaxEvents 500 |
		Where-Object { $_.LevelDisplayName -eq 'Error' -and $_.Message -like '*driver*' } |
		Select-Object TimeCreated, Id, Message |
		ConvertTo-Json -Depth 2
		"""
		output = self._runPowerShell(cmd)
		events = []
		try:
			data = json.loads(output)
			if isinstance(data, dict):
				data = [data]
			for event in data or []:
				events.append({
					"time": str(event.get("TimeCreated", "")),
					"id": event.get("Id", ""),
					"message": event.get("Message", "")[:300]
				})
		except Exception:
			pass
		return events

	def _scanGPU(self):
		"""Collect GPU driver version and details via WMI."""
		cmd = """
		Get-WmiObject Win32_VideoController |
		Select-Object Name, DriverVersion, Status, AdapterRAM |
		ConvertTo-Json -Depth 2
		"""
		output = self._runPowerShell(cmd)
		try:
			data = json.loads(output)
			if isinstance(data, dict):
				data = [data]
			return data if data else []
		except Exception:
			return []

	def _scanCPU(self):
		"""Collect CPU info to help contextualize driver compatibility."""
		cmd = """
		Get-WmiObject Win32_Processor |
		Select-Object Name, Manufacturer, Caption, NumberOfCores |
		ConvertTo-Json -Depth 2
		"""
		output = self._runPowerShell(cmd)
		try:
			data = json.loads(output)
			if isinstance(data, dict):
				data = [data]
			return data if data else []
		except Exception:
			return []

	def _mergeAll(self, pnpDrivers, wmiDrivers, eventErrors, gpuDrivers, cpuInfo):
		"""Combine all data sources into a unified list."""
		merged = []

		for wmi in wmiDrivers:
			entry = {
				"name": wmi.get("DeviceName") or "Unknown",
				"version": wmi.get("DriverVersion", "Unknown"),
				"date": str(wmi.get("DriverDate", "")),
				"manufacturer": wmi.get("Manufacturer", "Unknown"),
				"signed": not wmi.get("unsigned", False),
				"deviceID": wmi.get("DeviceID", ""),
				"infName": wmi.get("InfName", ""),
				"eventErrors": [],
				"source": "wmi"
			}
			# Attach any event log errors that mention this driver
			driverName = (entry["name"] or "").lower()
			for event in eventErrors:
				if driverName in event.get("message", "").lower():
					entry["eventErrors"].append(event)

			merged.append(entry)

		# Add GPU drivers as separate entries
		for gpu in gpuDrivers:
			merged.append({
				"name": gpu.get("Name", "Unknown GPU"),
				"version": gpu.get("DriverVersion", "Unknown"),
				"status": gpu.get("Status", "Unknown"),
				"type": "GPU",
				"signed": True,
				"eventErrors": [],
				"source": "gpu"
			})

		return merged
