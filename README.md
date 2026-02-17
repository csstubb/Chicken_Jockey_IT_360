# IT_360_Final_Project

## Team Members
- Cale Stubblefield
- Satya Yalamanchili
- Lucas Racine

## Project Idea
- Corrupted drivers are often the cause for system instability on Windows 11, and are also very useful forensic indicators when investigated unauthorized changes or tampering. This project is a Windows 11 digital forensics utility tool that scans the systems installed drivers and flags indicators of corruption or suspicious modification.
- The tool will collect driver metadata from Windows-native sources (driver packages, signature status, system logs, etc.). It will then use a rule-based model to identify the drivers that are most likely to be corrupted, or inconsistent with the systems expected status.
- The tool will also work with CPU and GPU driver detection tools to determine if drivers are outdated, missing, or corrupted.
- Exports the results to JSON/CSV.

## AI Usage Informatin
- AI will scan for the current device driver version, scan the internet for the current most up-to-date driver version, compare the two, and inform the user what currently installed drivers are not updated.
- AI will scan currently installed drivers for any corrupted code and will offer reinstallation solutions to the user to resolve the discovered issues.
