import json
import csv
import os
from datetime import datetime

class Exporter:
	"""Exports driver analysis results to JSON and CSV formats."""

	def __init__(self, drivers):
		self.drivers = drivers
		self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

	def toJSON(self, path="logs/results.json"):
		"""Export full results to a JSON file."""
		os.makedirs(os.path.dirname(path), exist_ok=True)
		output = {
			"scanTime": self.timestamp,
			"totalDrivers": len(self.drivers),
			"highPriority": len([d for d in self.drivers if d.get("priority", 0) >= 7]),
			"drivers": self.drivers
		}
		with open(path, "w", encoding="utf-8") as f:
			json.dump(output, f, indent=2, default=str)
		print(f"      \033[32mJSON saved to {path}\033[0m")

	def toCSV(self, path="logs/results.csv"):
		"""Export a summary to CSV — useful for importing into forensic tools."""
		os.makedirs(os.path.dirname(path), exist_ok=True)
		fields = [
			"name", "version", "latestVersion", "versionOutdated",
			"manufacturer", "signed", "priority", "corruptionRisk",
			"issueCount", "aiNotes", "reinstallCommand", "date", "source"
		]
		with open(path, "w", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
			writer.writeheader()
			for driver in self.drivers:
				# Flatten issues list to a count for CSV readability
				row = {field: driver.get(field, "") for field in fields}
				writer.writerow(row)
		print(f"      \033[32mCSV saved to {path}\033[0m")
