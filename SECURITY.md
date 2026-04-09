# Security Policy & API Key Management

## ⚠️ CRITICAL SECURITY NOTICE

**API keys were previously exposed in git history** (commit d5db0b6). If you cloned this repository before April 9, 2026, the `.env` file with API keys may have been visible.

### Action Required (If Affected)
If you have access to the exposed API keys, **regenerate them immediately**:

1. **OpenAI**: https://platform.openai.com/api-keys → Delete old key → Create new key
2. **Claude**: https://console.anthropic.com/api-keys → Revoke old key → Create new key
3. **DeepSeek**: https://platform.deepseek.com/api-keys → Delete old key → Create new key

**Do NOT reuse exposed keys.**

---

## API Key Setup (Secure Way)

### Step 1: Get Your API Keys
1. **OpenAI**: Visit https://platform.openai.com/api-keys
2. **Claude**: Visit https://console.anthropic.com/api-keys
3. **DeepSeek**: Visit https://platform.deepseek.com/api-keys

### Step 2: Create `.env` File Locally (Never commit!)

```bash
cp .env.example .env
```

### Step 3: Edit `.env` and Add Your Real Keys

```bash
nano .env
```

Add your actual API keys:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
CLAUDE_API_KEY=sk-ant-your-actual-key-here
DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### Step 4: Verify It's Not Committed

```bash
git status
# Should show: nothing to commit
# .env should NOT appear in status
```

The `.env` file is already in `.gitignore`, so it will never be committed.

---

## Best Practices

### ✅ DO
- ✅ Keep `.env` file in root directory (git-ignored)
- ✅ Regenerate keys if they're ever exposed
- ✅ Use different keys for development vs production (if possible)
- ✅ Rotate keys periodically
- ✅ Check `.gitignore` contains `.env` before committing

### ❌ DON'T
- ❌ Commit `.env` file to git
- ❌ Share `.env` file with others
- ❌ Hardcode API keys in source code (.py files)
- ❌ Include environment files in version control
- ❌ Reuse compromised/exposed keys

---

## GitHub Security Scanning

GitHub has **Dependency Scanning** enabled to detect exposed secrets. If you see alerts:

1. Go to **Settings → Security → Secret scanning**
2. Review any detected secrets
3. Regenerate them immediately if exposed
4. No further action needed (git history remains, but keys are invalidated)

---

## Removing from Git History (Advanced)

If you want to completely remove `.env` from history, you can use:

### Option A: GitHub's Tool (Easiest)
GitHub automatically detects and alerts about exposed secrets. No action needed - invalidate the keys.

### Option B: Git Filter-Branch (Complex)
```bash
# WARNING: This rewrites history and requires force push
# Only do this if absolutely necessary

git filter-branch --tree-filter 'rm -f .env' -- --all
git push origin --force --all
```

⚠️ **Note**: This affects all collaborators and is only necessary if keys stayed exposed for public checkout.

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email: Contact via GitHub organization settings
3. Or use GitHub's **Security Advisory** feature

---

## Monitoring

The `.gitignore` file now includes:

```
# CRITICAL: Environment variables with API keys and credentials
.env
.env.local
.env.*.local
.env.production
.env.development
.env.test
```

This ensures `.env` and related files are never accidentally committed.

---

## For Public Repository Users

If you cloned this repository:

1. **Create your own `.env`** from `.env.example`
2. **Add your own API keys** (not the ones from history)
3. **Never commit `.env`** (git will prevent this automatically)
4. **Regenerate keys** if you mistakenly saw exposed ones

---

## Questions?

- **Security concern?** Use GitHub Security Advisory or contact maintainer
- **API key issues?** Check provider documentation
- **Setup help?** See README.md § Installation

---

**Last Updated**: April 9, 2026  
**Status**: ✅ Secured - `.env` removed from git tracking
