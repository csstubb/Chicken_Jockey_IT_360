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

## AI Usage Information
- AI will scan for the current device driver version, scan the internet for the current most up-to-date driver version, compare the two, and inform the user what currently installed drivers are not updated.
- AI will scan currently installed drivers for any corrupted code and will offer reinstallation solutions to the user to resolve the discovered issues.
- AI will give a priority numbering to each issue discovered, displaying the highest priority issues at the top and the lowest priority issues at the bottom.

## Features

- Scans all installed PnP drivers using `pnputil` and WMI
- Checks driver signatures — unsigned drivers are flagged as tamper indicators
- Cross-references Windows Event Log for driver-related errors
- Detects outdated CPU and GPU drivers
- AI-powered version checking (compares installed vs latest known version)
- AI corruption risk scoring with forensic notes
- Priority ranking (1–10) with highest priority issues shown first
- Exports results to JSON and CSV

## Requirements

- Windows 11
- Linux
- Python 3.10+
- Administrator privileges (required for full Event Log and DriverStore access)

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USER/Chicken_Jockey_IT_360
cd Chicken_Jockey_IT_360
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Install Ollama** (optional but recommended for full AI features)

```powershell
ollama pull llama3
ollama pull tinyllama
ollama serve
```

**4. Run as Administrator**

Right-click PowerShell → "Run as Administrator", then:
```bash
cd C:\Users\YOUR_USER\Chicken_Jockey_IT_360
python main.py
```

## Project Structure

```
driver-forensics/
├── main.py                  # Entry point
├── core/
│   ├── scanner.py           # Collects raw driver metadata from Windows
│   └── analyzer.py          # Rule-based corruption/tamper detection
├── ai/
│   └── ai_agent.py          # AI version checking, corruption scoring, priority ranking
├── exporters/
│   └── exporter.py          # JSON and CSV export
├── logs/                    # Scan outputs saved here (gitignored)
├── requirements.txt
└── .gitignore
```

## Output

Results are printed to the console ranked by priority and saved to:
- `logs/results.json` — full detailed output
- `logs/results.csv` — summary suitable for importing into forensic tools

## Security Note

Never commit your `ANTHROPIC_API_KEY` to GitHub. The `.gitignore` is already configured to exclude `.env` files, but always double-check before pushing.

## License

MIT
