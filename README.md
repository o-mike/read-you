# read-you

A README generator that analyzes your codebase and creates clear documentation.

## Features

- Detects and analyzes project's primary languages
- Generates comprehensive README files using OpenAI's language models
- Identifies key files like entry points and core modules
- Supports multiple languages: Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, PHP, C#
- Offers both concise and detailed README formats
- Provides dry-run mode to preview without file creation

## Installation

Choose your preferred installation method:

### Option 1: Run Directly (using uvx)
```bash
# From the repository root:
uvx --with-editable . read-you . [options]
```
This creates a temporary environment and runs the latest version without installing.

### Option 2: Isolated Installation (using pipx)
```bash
pipx install read-you
```

### Option 3: Quick Install (using uv)
```bash
uv pip install read-you
```

### Option 4: Development Installation
```bash
git clone https://github.com/yourusername/read-you.git
cd read-you
pip install -e .
```

After installation, set up your configuration:
1. Copy `config/secrets.yaml.template` to `config/secrets.yaml`
2. Add your OpenAI API key to `secrets.yaml`:
   ```yaml
   openai:
     api_key: "your-api-key-here"
   ```

## Usage

Generate a README for any repository:

```bash
# If installed via pip/pipx
read-you <repo_path> [options]

# Or run directly with uvx (recommended for development)
uvx --with-editable . read-you <repo_path> [options]
```

### Options

- `repo_path`: Path to the repository (required)
- `--model <model_name>`: OpenAI model to use (default: gpt-4o-mini)
- `--verbose`, `-v`: Generate detailed README
- `--dry-run`, `-d`: Preview without creating file

### Examples

Basic usage:
```bash
uvx --with-editable . read-you /path/to/repo
```

Detailed README:
```bash
uvx --with-editable . read-you /path/to/repo --verbose
```

Preview mode:
```bash
uvx --with-editable . read-you /path/to/repo --dry-run
```

### Development Mode

The `--with-editable` flag configures UV to:
- Use the local version of the package
- Reflect code changes immediately
- Ideal for development

When actively developing, use `--with-editable` to test changes without reinstalling.

## Example Output

See what read-you generates:

1. [Self-Generated README](examples/self-generated/README.md) - Output when run on its own codebase
   ```bash
   # Generate the example
   python examples/generate_examples.py
   ```

## Contributing

Areas that need work:
- Language detection improvements
- File analysis enhancements
- Custom README templates
- Test coverage

## License

MIT License - See LICENSE file for details