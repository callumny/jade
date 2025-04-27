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
./scripts/jade.sh [options]
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
