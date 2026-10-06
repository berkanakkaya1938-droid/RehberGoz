# Rehber Göz

AI-based wearable assistant prototype for visually impaired users.

## Prototype release structure

- `src/` : application source code
- `config/` : non-secret configuration
- `version.json` : current application version
- `.env.example` : example environment variables
- `.gitignore` : prevents secrets and local files from being committed
- `CHANGELOG.md` : release notes

## API key

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Then put the Gemini API key in `.env`:

```env
GEMINI_API_KEY=YOUR_KEY_HERE
```

**Do not commit `.env` to GitHub.**

## Release

Prototype versions should use tags such as:

- `v0.1.0`
- `v0.2.0`
- `v1.0.0`

For each GitHub Release, package the application files as a single archive. The Raspberry Pi update manager can later download that archive, verify its SHA-256 hash, install it into a new version directory, and switch to the new version.

## Suggested first release

`v0.1.0`

Title:

`Rehber Göz Prototype v0.1.0`

This first release should represent the first working camera + Gemini test.
