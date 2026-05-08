import sys
import os

from ai.ai_agent import AIAgent
from exporters.exporter import Exporter

def printBanner():
	print("\033[36m")
	print("██████╗ ██████╗ ██╗██╗   ██╗███████╗██████╗     ███████╗ ██████╗ ██████╗ ███████╗███╗   ██╗███████╗██╗ ██████╗███████╗")
	print("██╔══██╗██╔══██╗██║██║   ██║██╔════╝██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██║██╔════╝██╔════╝")
	print("██║  ██║██████╔╝██║██║   ██║█████╗  ██████╔╝    █████╗  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████╗██║██║     ███████╗")
	print("██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ██╔══██╗    ██╔══╝  ██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║╚════██║██║██║     ╚════██║")
	print("██████╔╝██║  ██║██║ ╚████╔╝ ███████╗██║  ██║    ██║     ╚██████╔╝██║  ██║███████╗██║ ╚████║███████║██║╚██████╗███████║")
	print("╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝╚══════╝")
	print("\033[0m")
	print("\033[33mDriver Forensics Tool — Windows 11 & Linux\033[0m")
	print("\033[33mDetects corrupted, tampered, and outdated drivers\033[0m\n")

def getComponents():
	"""Return the correct scanner and analyzer for the current OS."""
	platform = sys.platform

	if platform == "win32":
		print("\033[32mPlatform detected: Windows\033[0m\n")
		from core.scanner import DriverScanner
		from core.analyzer import DriverAnalyzer
		return DriverScanner(), DriverAnalyzer

	elif platform == "linux":
		print("\033[32mPlatform detected: Linux\033[0m\n")
		from core.linux_scanner import LinuxDriverScanner
		from core.linux_analyzer import LinuxDriverAnalyzer
		return LinuxDriverScanner(), LinuxDriverAnalyzer

	else:
		print(f"\033[31mUnsupported platform: {platform}\033[0m")
		sys.exit(1)

def main():
	printBanner()

	scanner, AnalyzerClass = getComponents()

	print("\033[32m[1/4] Scanning installed drivers...\033[0m")
	drivers = scanner.scanAll()
	print(f"      Found {len(drivers)} drivers.\n")

	print("\033[32m[2/4] Analyzing drivers for corruption and tampering...\033[0m")
	analyzer = AnalyzerClass(drivers)
	results = analyzer.analyzeAll()
	print(f"      Analysis complete.\n")

	print("\033[32m[3/4] Running AI checks (version, corruption, priority ranking)...\033[0m")
	agent = AIAgent(results)
	rankedResults = agent.run()
	print(f"      AI analysis complete.\n")

	print("\033[32m[4/4] Exporting results...\033[0m")
	os.makedirs("logs", exist_ok=True)
	exporter = Exporter(rankedResults)
	exporter.toJSON("logs/results.json")
	exporter.toCSV("logs/results.csv")
	print("      Exported to logs/results.json and logs/results.csv\n")

	print("\033[36m===== RESULTS (Highest Priority First) =====\033[0m\n")
	for driver in rankedResults:
		priority = driver.get("priority", 0)
		name = driver.get("name", "Unknown")
		issues = driver.get("issues", [])
		if not issues:
			continue  # Skip clean drivers to keep output readable
		color = "\033[31m" if priority >= 7 else "\033[33m" if priority >= 4 else "\033[32m"
		print(f"{color}[Priority {priority}/10] {name}\033[0m")
		for issue in issues:
			print(f"  \033[31m[-]\033[0m {issue}")
		print()

if __name__ == "__main__":
	main()
