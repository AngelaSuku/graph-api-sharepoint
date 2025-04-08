# 📂 Graph API SharePoint Automation

Automate file and folder interactions with SharePoint using the Microsoft Graph API and Python. This repo includes three standalone scripts for:

- 🔽 Downloading a specific file by name
- 📁 Downloading the contents of a SharePoint folder
- 🔼 Uploading a file to a SharePoint folder (with optional backup)

---

## 📦 Prerequisites

- Python 3.7+
- Microsoft 365 account with Graph API access
- Registered Azure AD app with the following delegated permissions:
  - `Sites.ReadWrite.All`
- `token.json` containing a valid access token
- A config `.ini` file for client credentials

### Example `token.json`

```json
{
  "access_token": "your_token_here"
}

