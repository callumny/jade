# JADE - Java Analyzer for Detecting Effects

JADE analyzes Java code changes and identifies which tests are impacted, allowing you to run only the affected tests.

## Features

- Compare Git commits or branches to identify code changes
- Analyze Java test files to identify impacted tests
- Run only the impacted tests
- Support for Maven, Gradle, and plain Java projects

## Installation

```bash
# Using pip
pip install .

# Using Poetry
poetry install
poetry shell  # or: poetry run jade
```

### Adding to Windows PATH

To run jade commands from anywhere in your Windows command prompt or PowerShell:

1. Make sure you've installed the package using one of the methods above
2. Add the `scripts` directory to your PATH:
   - Open the Start menu and search for "Environment Variables"
   - Click "Edit the system environment variables"
   - Click the "Environment Variables" button
   - Under "System variables" or "User variables", find the "Path" variable and click "Edit"
   - Click "New" and add the full path to the `scripts` directory (e.g., `C:\Users\YourUsername\IdeaProjects\jade\scripts`)
   - Click "OK" on all dialogs to save changes

Alternatively, you can create a symbolic link to the scripts in a directory that's already in your PATH:

```powershell
# In PowerShell (run as Administrator)
New-Item -ItemType SymbolicLink -Path "C:\Windows\System32\jade.bat" -Target "C:\path\to\jade\scripts\jade.bat"
New-Item -ItemType SymbolicLink -Path "C:\Windows\System32\jade.ps1" -Target "C:\path\to\jade\scripts\jade.ps1"
```

### Adding to WSL PATH

To run jade commands from anywhere in your WSL (Windows Subsystem for Linux) terminal:

1. Make sure you've installed the package in your WSL environment using one of the methods above
2. Open your shell configuration file in a text editor:
   ```bash
   # For Bash (default)
   nano ~/.bashrc

   # For Zsh
   nano ~/.zshrc
   ```
3. Add the following line at the end of the file:
   ```bash
   export PATH="$PATH:/path/to/jade/scripts"
   ```
   Replace `/path/to/jade/scripts` with the actual path to the scripts directory in your WSL filesystem
4. Save the file and exit the editor (in nano: Ctrl+O, Enter, Ctrl+X)
5. Apply the changes:
   ```bash
   # For Bash
   source ~/.bashrc

   # For Zsh
   source ~/.zshrc
   ```

Alternatively, you can create a symbolic link to the scripts in a directory that's already in your PATH:

```bash
# Create a symbolic link in /usr/local/bin (may require sudo)
sudo ln -s /path/to/jade/scripts/jade.sh /usr/local/bin/jade
sudo chmod +x /usr/local/bin/jade

# Make sure the script is executable
chmod +x /path/to/jade/scripts/jade.sh
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
