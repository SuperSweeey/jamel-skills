# Configuration Template

This file shows how to store your Cubox API URL for easy access.

## Method 1: Environment Variable (Recommended)

Set an environment variable in your shell:

```bash
# Linux/Mac
export CUBOX_API_URL="your_api_url_here"

# Windows PowerShell
$env:CUBOX_API_URL="your_api_url_here"
```

## Method 2: Config File

Create a `config.json` file in the skill directory:

```json
{
  "api_url": "your_api_url_here"
}
```

⚠️ **Important**: Never commit your actual API URL to version control. Add `config.json` to `.gitignore`.

## Getting Your API URL

See `references/api_reference.md` for detailed instructions on obtaining your Cubox API URL.
