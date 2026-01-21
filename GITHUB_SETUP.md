# GitHub Authentication Steps for Flux Project

## Step-by-Step Instructions

### 1️⃣ Create Personal Access Token

Visit: https://github.com/settings/tokens

Then:
- Click "Generate new token" → "Generate new token (classic)"
- **Token name:** Flux Project
- **Expiration:** 90 days
- **Scope:** Check ✅ `repo` (Full control of private repositories)
- Click "Generate token"
- **COPY the entire token** (It looks like: `ghp_1234567890abcdefghijklmnopqrst`)

⚠️ **Important:** This is the only time you'll see it. Save it!

---

### 2️⃣ Configure Git (macOS)

In your terminal:
```bash
git config --global credential.helper osxkeychain
```

This stores your credentials securely in macOS Keychain.

---

### 3️⃣ Push to GitHub

```bash
cd /Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper
git push -u origin main
```

When prompted:
```
Username: arifpras
Password: <paste your token here (Ctrl+V on Mac)>
```

---

### 4️⃣ Success!

If successful, you'll see:
```
Enumerating objects: 194, done.
...
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

Your Flux project is now live at: https://github.com/arifpras/flux

---

## Troubleshooting

**"Repository not found"?**
- Make sure you created the repo at https://github.com/new with name "flux"
- Repo should be empty (no README, .gitignore, or LICENSE)

**"Authentication failed"?**
- Check your token hasn't expired
- Token must have `repo` scope
- Make sure you copied the entire token (all characters)

**"Permission denied"?**
- Token might not have push permissions
- Create a new token with full `repo` scope

---

**Ready? Create the token at the link above, then run the push command!**
