# JADE - Java Analyzer for Detecting Effects

JADE analyzes Java code changes and identifies which tests are impacted, allowing you to run only the affected tests.

## Features

- Compare Git commits or branches to identify code changes
- Analyze Java test files to identify impacted tests
- Run only the impacted tests
- Support for Maven, Gradle, and plain Java projects

## Installation

### Prerequisites

- Python 3.12 or later
- pip or Poetry (2.0.0 or later recommended)
- Git (required for analyzing code changes)

### Installing with pip

```bash
# Install from the current directory
pip install .
```

### Installing with Poetry

```bash
# If you're using Poetry for the first time with this project
poetry lock --no-update  # Regenerate the lock file for your Poetry version
poetry install           # Install the package and its dependencies
```

After installation, the `jade` command will be available in your terminal.

### Verifying Installation

To verify that jade is installed correctly and available in your PATH:

```bash
# Check if jade is available
jade --help
```

This should display the help message with all available options.

### Troubleshooting

#### Command Not Found

If you get a "Command not found" error after installation:

1. **Using Poetry**: Make sure you're in the Poetry virtual environment:
   ```bash
   # Activate the virtual environment
   poetry shell

   # Then try running jade
   jade --help
   ```

2. **Using pip**: Ensure the installation directory is in your PATH:
   ```bash
   # Find where pip installed the package
   pip show jade

   # Check if the installation directory is in your PATH
   echo $PATH  # On Linux/macOS
   echo %PATH%  # On Windows
   ```

#### Lock File Compatibility Warning

If you see warnings about the lock file not being compatible with your version of Poetry:

```bash
# Regenerate the lock file for your Poetry version
poetry lock --no-update
```

#### Python Version Error

If you get errors related to Python version requirements:

1. Check your Python version:
   ```bash
   python --version
   ```

2. Ensure you have Python 3.12 or later installed, as required by JADE.

#### WSL Python Not Found Error

If you encounter the error `[Errno 2] No such file or directory: 'python'` when running `poetry install` in WSL:

1. Use the included `poetry-wsl` wrapper script which automatically detects and uses either `python` or `python3`:
   ```bash
   # Make the script executable (only needed once)
   chmod +x poetry-wsl

   # Use the wrapper script instead of calling poetry directly
   ./poetry-wsl install
   ```

2. Alternatively, you can:
   - Create a symbolic link to make "python" point to your Python 3.12 installation:
     ```bash
     sudo ln -sf /usr/bin/python3.12 /usr/bin/python
     ```
   - Or tell Poetry which Python executable to use:
     ```bash
     poetry env use python3.12
     poetry install
     ```

See the [WSL Notes](#wsl-notes) section for more detailed instructions.

### Platform Compatibility

JADE is designed to be cross-platform and can be run on:

- Windows
- macOS
- Linux
- Windows Subsystem for Linux (WSL)

#### Windows-Specific Notes

On Windows, you might need to:

1. Use PowerShell or Command Prompt with appropriate permissions
2. Use `%PATH%` instead of `$PATH` when checking environment variables
3. If using WSL, remember that Poetry environments in WSL are separate from Windows environments

#### WSL Notes

When running in WSL:

1. Make sure you have Python 3.12 or later installed in your WSL environment:
   ```bash
   # Install Python 3.12 in WSL (Ubuntu/Debian)
   sudo apt update
   sudo apt install python3.12

   # Create a symbolic link to make 'python' point to 'python3.12'
   sudo ln -sf /usr/bin/python3.12 /usr/bin/python

   # Verify the installation
   python --version  # Should show Python 3.12.x
   ```

2. You may need to run `poetry config virtualenvs.in-project true` to ensure virtual environments are created in the project directory

3. If you encounter the error `[Errno 2] No such file or directory: 'python'` when running `poetry install`:
   - This occurs because Poetry is looking for an executable named exactly "python" but can't find it
   - WSL often has Python installed as "python3" rather than "python"
   - Use the included `poetry-wsl` wrapper script which automatically detects and uses either `python` or `python3`:
     ```bash
     # Make the script executable (only needed once)
     chmod +x poetry-wsl

     # Use the wrapper script instead of calling poetry directly
     ./poetry-wsl install
     ```
   - Alternatively, you can:
     - Use the symbolic link command above to create a "python" executable
     - Or tell Poetry which Python executable to use:
       ```bash
       # Tell Poetry to use python3.12 specifically
       poetry env use python3.12

       # Then install dependencies
       poetry install
       ```

4. You can run JADE in WSL in two ways:

   a. Using `poetry shell` (traditional method):
   ```bash
   # Activate the virtual environment
   poetry shell

   # Then run jade commands
   jade --help
   ```

   b. Using the `jade-wsl` wrapper script (recommended):
   ```bash
   # Make the script executable (only needed once after cloning the repository)
   chmod +x jade-wsl

   # Run jade commands directly without poetry shell
   ./jade-wsl --help
   ```

   The wrapper script automatically activates the virtual environment and runs the jade command, eliminating the need for `poetry shell`.

   > **Note**: The `chmod +x` command needs to be run in WSL, not in Windows PowerShell or Command Prompt.

## Usage

### Standard Usage (after activating virtual environment)

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

### WSL Usage with Wrapper Script

In WSL, you can use the `jade-wsl` wrapper script to run commands without activating the virtual environment first:

```bash
# Basic usage (compare HEAD to previous commit)
./jade-wsl

# Compare with specific commits/branches
./jade-wsl -c 3                                  # Compare to 3rd previous commit
./jade-wsl --branch=feature-branch               # Compare to another branch
./jade-wsl --branch=branch1 --branch=branch2     # Compare two branches
./jade-wsl --commit=abc123                       # Compare to specific commit

# Additional options
./jade-wsl --tests-only                          # Show only impacted tests
./jade-wsl --run-tests                           # Run the impacted tests
./jade-wsl --project-dir=/path/to/project        # Specify project directory
./jade-wsl --test-dir=/path/to/tests             # Specify test directory
./jade-wsl --build-tool=gradle                   # Specify build tool
./jade-wsl --output-file=results.txt             # Save results to file
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
