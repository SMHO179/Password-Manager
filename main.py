# 🔐 Password Manager

<p align="center">

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python\&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite\&logoColor=white)
![Encryption](https://img.shields.io/badge/Encryption-Fernet-orange)
![CLI](https://img.shields.io/badge/Interface-CLI-purple)
![License](https://img.shields.io/github/license/SMHO179/Password-Manager)
![Last Commit](https://img.shields.io/github/last-commit/SMHO179/Password-Manager)

</p>

A secure and lightweight **CLI password manager** written in Python.

Passwords are encrypted using **Fernet symmetric encryption** and stored locally in an **SQLite database**.

No cloud. No external services. Your credentials stay on your machine.

---

## ✨ Features

* 🔒 Secure password encryption with Fernet
* 💾 Local SQLite database storage
* 🖥️ Interactive terminal UI powered by Rich
* 🔑 Automatic encryption key generation
* 🙈 Hidden password input
* ✅ Input validation
* 🔄 Safe database transactions with rollback on errors
* 🛑 Graceful `Ctrl+C` handling
* ↩️ Return to menu with `b`
* ➕ Add passwords
* 📋 List saved accounts
* ✏️ Edit credentials
* 🗑️ Delete credentials
* 🌐 Fully offline operation

---

## 🛠 Technologies

| Technology   | Purpose            |
| ------------ | ------------------ |
| Python 3.14+ | Main application   |
| SQLite3      | Local database     |
| cryptography | Fernet encryption  |
| Rich         | Terminal interface |

---

## 📂 Project Structure

```text
.
├── main.py              # Main application
├── generate_key.py      # Encryption key generator
├── requirements.txt     # Python dependencies
├── README.md            # English documentation
├── README-FA.md         # Persian documentation
├── CONTRIBUTING.md      # Contribution guide
├── LICENSE              # License file
├── .gitignore           # Git ignore rules
│
├── secret.key           # Generated encryption key
└── vault.db             # Local password database
```

> ⚠️ `secret.key` and `vault.db` should never be shared publicly.

---

## 🚀 Installation

### Clone repository

```bash
git clone https://github.com/SMHO179/Password-Manager.git

cd Password-Manager
```

### Create virtual environment

```bash
python -m venv .venv
```

Activate environment:

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the application:

```bash
python main.py
```

Application menu:

```text
1. Add password
2. List passwords
3. Delete password
4. Edit password
5. Exit
```

During input:

```text
b
```

returns to the previous menu.

---

## 🔐 Security

* Passwords are encrypted before being stored
* Plain text passwords are never written to the database
* Every installation has its own encryption key
* The key file is required for decryption
* Password input is hidden in terminal
* Database operations use transactions with rollback support

⚠️ **Important:**

If you lose `secret.key`, your encrypted passwords cannot be recovered.

Make a secure backup of your key file.

---

## 🗄 Database Schema

| Column     | Type      | Description             |
| ---------- | --------- | ----------------------- |
| id         | INTEGER   | Primary key             |
| site       | TEXT      | Website or service name |
| username   | TEXT      | Account username        |
| password   | TEXT      | Encrypted password      |
| created_at | TIMESTAMP | Creation timestamp      |

---

## 🤝 Contributing

Contributions are welcome.

Before contributing, please read:

```text
CONTRIBUTING.md
```

Suggested workflow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Commit your work
5. Open a Pull Request

---

## 📜 License

This project is licensed under the terms of the [LICENSE](LICENSE).
