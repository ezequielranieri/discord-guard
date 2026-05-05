# discord-guard 🛡️

**Discord Security Scanner & Real-time Protector**

`discord-guard` is a professional CLI tool designed to help users detect and protect against session token hijacking, unauthorized application access, and suspicious account activity. Built with a security-first mindset and a focus on non-technical users.

---

## 💡 Why This Tool Exists

This project was inspired by a real-world incident. A close friend lost his Discord account to a token hijacking attack while he was offline. His account spent hours spamming malicious giveaway links to his entire friend list. 

Discord provides very little visibility into active sessions or authorized app permissions for average users. `discord-guard` was built to bridge that gap, giving users the power to audit their own account security with a single command and react to anomalies in real time.

---

## 🛡️ Security Features

- **Risk Analysis Engine:** Calculates a 0-100 security score based on 2FA status, dangerous app permissions, and active sessions.
- **Interactive Remediation:** Identify and revoke suspicious OAuth2 applications directly from the terminal.
- **Real-time Monitoring:** Detects anomalies like sudden mass unfriending, server join spikes, or new unauthorized apps.
- **Professional Auditing:** Generate PDF and JSON security reports for archival or sharing.
- **Privacy by Design:** 
    - Your Discord token is **never** stored on disk.
    - Tokens are masked in all logs to prevent accidental exposure.
    - All communication is performed over encrypted HTTPS via Discord's official API.

---

## ⚠️ Important Warning
This tool requires your **Discord User Token** to function. 
1. **Never** share your token with anyone.
2. Use this tool **only** on your own account.
3. Your token is used in-memory only and is never sent to any server other than `discord.com`.

---

## 🚀 Installation

Ensure you have **Python 3.12+** installed.

```bash
# Clone the repository
git clone https://github.com/ezequielranieri/discord-guard
cd discord-guard

# Install in editable mode
pip install -e .
```

---

## 📖 Usage

### 1. Scan your account
Perform a full security audit and interactively revoke dangerous apps.
```bash
discord-guard scan
```

**Expected Output:**
```
┌─────────────────────────────────────────────────────┐
│              SECURITY REPORT                        │
│  Overall Risk Score: 72/100  🔴 CRITICAL            │
└─────────────────────────────────────────────────────┘

🔴 CRITICAL — Two-Factor Authentication (2FA) is not enabled.
   → Enable 2FA in User Settings -> My Account -> Two-Factor Auth.

🟡 WARNING — App 'Unknown Bot' has dangerous permissions: bot, rpc
   → Review and consider revoking 'Unknown Bot' if you don't recognize it.

Would you like to revoke access for these suspicious apps? [y/n]:
```

### 2. Monitor for attacks
Keep the tool running to detect hijacking attempts in real time.
```bash
discord-guard monitor --interval 30
```

### 3. Generate a PDF Audit
```bash
discord-guard report --format pdf --output my_security_audit.pdf
```

---

## 🏗️ Architecture

- **Frontend:** Built with `Typer` and `Rich` for a professional, interactive CLI experience.
- **API Client:** Async `httpx` client for high-performance interaction with Discord's REST API.
- **Validation:** `Pydantic V2` for strict data modeling and safety.
- **Core Logic:** Decoupled `Scanner`, `Analyzer`, and `Monitor` modules for high maintainability.
- **Testing:** Comprehensive test suite with over 20 tests covering unit and integration scenarios.

---

## 👨‍💻 About the Author

**Ezequiel Ranieri**

I am a self-taught Python developer with a passion for cybersecurity and backend engineering. This project demonstrates my ability to take a real-world problem and build a robust, secure, and user-centric solution from scratch. I focus on writing clean, idiomatic code and implementing professional engineering standards like asynchronous programming, strict type hinting, and automated testing.

- **Email:** [ez.ranieri@gmail.com](mailto:ez.ranieri@gmail.com)
- **Portfolio:** https://github.com/ezequielranieri

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
