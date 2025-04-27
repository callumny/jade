# JADE - Java Analyzer for Detecting Effects

JADE analyzes Java code changes and identifies which tests are impacted, allowing you to run only the affected tests.

## Features

- Compare Git commits or branches to identify code changes
- Analyze Java test files to identify impacted tests
- Run only the impacted tests
- Support for Maven, Gradle, and plain Java projects

## Installation

JADE can be installed as a command-line executable that's automatically added to your PATH.

```bash
# Install from the current directory
pip install .

# Or, if you prefer using Poetry
poetry install
```

After installation, the `jade` command will be available in your terminal.

### Verifying Installation

To verify that jade is installed correctly and available in your PATH:

```bash
# Check if jade is available
jade --help
```

This should display the help message with all available options.

### Alternative Installation Methods

If you prefer not to install the package, you can also run jade directly using the scripts in the `scripts` directory:

> **Note:** The recommended approach is to install the package using pip or Poetry as described above, which automatically adds the `jade` command to your PATH.

#### Windows (Command Prompt)
```cmd
scripts\jade.bat [options]
```

#### Windows (PowerShell)
```powershell
scripts\jade.ps1 [options]
```

#### Linux/macOS/WSL
```bash
# Option 1: Run the script directly
./scripts/jade.sh [options]

# Option 2: Make the script executable and add the scripts directory to your PATH
chmod +x scripts/jade.sh
export PATH="$PATH:$(pwd)/scripts"  # Add to ~/.bashrc or ~/.zshrc to make permanent
```

## Usage

```bash
# Basic usage (compare HEAD to previous commit)
jade

# Compare with specific commits/branches
jade -c 3                                  # Compare to 3rd previous commit
jade --branch=feature-branch               # Compare to another branch
jade --branch=branch1 --branch=branch2     # Compare two branches
jade --commit=abc123                       # Compare to specific commit

# Additional options
jade --tests-only                          # Show only impacted tests
jade --run-tests                           # Run the impacted tests
jade --project-dir=/path/to/project        # Specify project directory
jade --test-dir=/path/to/tests             # Specify test directory
jade --build-tool=gradle                   # Specify build tool
jade --output-file=results.txt             # Save results to file
```

## How It Works

1. Uses Git to identify changed files between commits
2. Parses Java files to identify changed methods
3. Analyzes test files to map tests to the methods they invoke
4. Identifies tests impacted by the changed methods
5. Optionally runs the impacted tests

## Troubleshooting

### Command 'jade' not found in WSL

If you've added the jade script to your PATH in WSL but still get "Command 'jade' not found" when running `jade --help`, check your PATH configuration:

1. **Incorrect:** Adding the script file itself to PATH
   ```bash
   # This won't work
   export PATH="$PATH:~/bin/jade/scripts/jade.sh"
   ```

2. **Correct:** Add the directory containing the script to PATH
   ```bash
   # This will work
   export PATH="$PATH:~/bin/jade/scripts"
   ```

   Make sure the script is executable:
   ```bash
   chmod +x ~/bin/jade/scripts/jade.sh
   ```

3. **Recommended:** Install the package using pip
   ```bash
   cd ~/bin/jade
   pip install .
   ```
   This automatically adds the `jade` command to your PATH.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
