import json
import re
import os
import urllib.request


OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "tinyllama"   # change to "tinyllama" if RAM is limited

# Anthropic (optional, used only if ANTHROPIC_API_KEY is set)
ANTHROPIC_URL   = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


class AIAgent:
	"""
	AI analysis for driver forensics.
	Priority order:
	  1. Ollama  — free, local, no key required (default)
	  2. Anthropic — cloud, requires ANTHROPIC_API_KEY env var
	  3. Rule-based fallback — no AI at all
	"""

	def __init__(self, drivers):
		self.drivers = drivers
		self.anthropicKey = os.environ.get("ANTHROPIC_API_KEY", "")
		self.ollamaAvailable = self._checkOllama()

	def _checkOllama(self):
		"""Check whether Ollama is running and the model is available."""
		try:
			req = urllib.request.Request(
				"http://localhost:11434/api/tags",
				method="GET"
			)
			with urllib.request.urlopen(req, timeout=3) as resp:
				data = json.loads(resp.read().decode())
				models = [m["name"].split(":")[0] for m in data.get("models", [])]
				if OLLAMA_MODEL in models:
					print(f"      \033[32mOllama detected — using local {OLLAMA_MODEL} model (free)\033[0m")
					return True
				else:
					print(f"      \033[33mOllama is running but '{OLLAMA_MODEL}' model not found.\033[0m")
					print(f"      \033[33mRun:  ollama pull {OLLAMA_MODEL}  then retry.\033[0m")
					return False
		except Exception:
			return False

	def run(self):
		"""Run AI checks using the best available backend."""
		if self.ollamaAvailable:
			print("      Running driver analysis via Ollama (local AI)...")
			return self._runAnalysis(self._analyzeWithOllama)
		elif self.anthropicKey:
			print("      Ollama not available — using Anthropic API...")
			return self._runAnalysis(self._analyzeWithAnthropic)
		else:
			print("\033[33m      No AI backend available. Using rule-based scoring.\033[0m")
			print("\033[33m      To enable free AI: install Ollama and run 'ollama pull llama3'\033[0m")
			return self._fallbackPriority()

	def _runAnalysis(self, analyzeFunc):
		"""Run analyzeFunc on every driver and return sorted results."""
		enriched = []
		total = len(self.drivers)
		for i, driver in enumerate(self.drivers, 1):
			name = driver.get("name", "Unknown")
			print(f"      [{i}/{total}] Analyzing: {name[:60]}", end="\r")
			result = analyzeFunc(driver)
			driver.update(result)
			enriched.append(driver)
		print()  # newline after progress
		enriched.sort(key=lambda d: d.get("priority", 0), reverse=True)
		return enriched

	def _buildPrompt(self, driver):
		"""Build the shared prompt used by both backends."""
		return f"""You are a driver forensics expert. Analyze this driver and respond ONLY with a JSON object — no explanation, no markdown, no code fences.

Driver Name: {driver.get("name", "Unknown")}
Driver Version: {driver.get("version", "Unknown")}
Manufacturer: {driver.get("manufacturer", "Unknown")}
Known Issues Found: {json.dumps(driver.get("issues", []))}
Issue Count: {driver.get("issueCount", 0)}

Respond with this exact JSON structure:
{{
  "latestVersion": "<latest known stable version, or 'Unknown'>",
  "versionOutdated": <true or false>,
  "corruptionRisk": "<Low|Medium|High>",
  "aiNotes": "<1-2 sentences of forensic insight>",
  "reinstallCommand": "<command to reinstall this driver, or empty string>",
  "priority": <integer 1-10, where 10 is most critical>
}}"""

	def _parseJSON(self, text):
		"""Strip markdown fences and parse JSON from model response."""
		text = re.sub(r"```json|```", "", text).strip()
		match = re.search(r"\{.*\}", text, re.DOTALL)
		if match:
			return json.loads(match.group())
		return json.loads(text)

	def _analyzeWithOllama(self, driver):
		"""Send driver metadata to local Ollama instance."""
		try:
			payload = json.dumps({
				"model": OLLAMA_MODEL,
				"prompt": self._buildPrompt(driver),
				"stream": False
			}).encode("utf-8")

			req = urllib.request.Request(
				OLLAMA_URL,
				data=payload,
				headers={"Content-Type": "application/json"},
				method="POST"
			)
			with urllib.request.urlopen(req, timeout=60) as resp:
				data = json.loads(resp.read().decode())
				text = data.get("response", "")
				return self._parseJSON(text)

		except Exception as e:
			return self._basicPriorityScore(driver)

	def _analyzeWithAnthropic(self, driver):
		"""Send driver metadata to Anthropic API."""
		try:
			payload = json.dumps({
				"model": ANTHROPIC_MODEL,
				"max_tokens": 500,
				"messages": [{"role": "user", "content": self._buildPrompt(driver)}]
			}).encode("utf-8")

			req = urllib.request.Request(
				ANTHROPIC_URL,
				data=payload,
				headers={
					"Content-Type": "application/json",
					"x-api-key": self.anthropicKey,
					"anthropic-version": "2023-06-01"
				},
				method="POST"
			)
			with urllib.request.urlopen(req, timeout=30) as resp:
				data = json.loads(resp.read().decode())
				text = ""
				for block in data.get("content", []):
					if block.get("type") == "text":
						text += block.get("text", "")
				return self._parseJSON(text)

		except Exception as e:
			return self._basicPriorityScore(driver)

	def _basicPriorityScore(self, driver):
		"""Rule-based priority score used when no AI backend is available."""
		issueCount = driver.get("issueCount", 0)
		signed = driver.get("signed", True)
		priority = min(issueCount * 2, 8)
		if not signed:
			priority = min(priority + 3, 10)
		return {
			"latestVersion": "Unknown",
			"versionOutdated": False,
			"corruptionRisk": "High" if priority >= 7 else "Medium" if priority >= 4 else "Low",
			"aiNotes": "AI analysis unavailable — scored by rule count only.",
			"reinstallCommand": "",
			"priority": priority
		}

	def _fallbackPriority(self):
		"""Apply rule-based scoring to all drivers."""
		results = []
		for driver in self.drivers:
			driver.update(self._basicPriorityScore(driver))
			results.append(driver)
		results.sort(key=lambda d: d.get("priority", 0), reverse=True)
		return results
