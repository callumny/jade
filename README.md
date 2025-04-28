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
- Git (required for analyzing code changes)
- One of the following:
  - [Poetry](https://python-poetry.org/docs/#installation) (recommended)
  - pip (with virtual environment)
  - pipx

### Installation Methods

Choose one of the following installation methods:

#### Method 1: Using Poetry (Recommended)

Poetry is the recommended way to install JADE as it handles dependencies and virtual environments automatically:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/jade.git
cd jade

# Install using Poetry
poetry install

# Run JADE using Poetry
poetry run jade --help

# Or, activate the virtual environment and run JADE directly
poetry shell
jade --help
```

#### Method 2: Using a Virtual Environment

If you encounter the "externally-managed-environment" error with pip, create a virtual environment:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/jade.git
cd jade

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install JADE in development mode
pip install -e .

# Now you can run JADE
jade --help
```

#### Method 3: Using pipx

pipx is designed for installing Python applications in isolated environments:

```bash
# Install pipx if you don't have it
python -m pip install --user pipx
python -m pipx ensurepath

# Install JADE using pipx
pipx install -e /path/to/jade

# Run JADE
jade --help
```

#### Method 4: Global Installation (Not Recommended for System Python)

This method may fail with an "externally-managed-environment" error on some systems:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/jade.git
cd jade

# Install globally using pip
pip install -e .

# If you get an "externally-managed-environment" error, use one of the methods above instead
# Or, if you understand the risks, you can override with:
# pip install -e . --break-system-packages
```

This will install the `jade` command in your system PATH, making it available from any directory.

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

1. Ensure the installation directory is in your PATH:
   ```bash
   # Find where pip installed the package
   pip show jade

   # Check if the installation directory is in your PATH
   echo $PATH  # On Linux/macOS
   echo %PATH%  # On Windows
   ```

2. You may need to add the pip installation directory to your PATH:
   ```bash
   # On Linux/macOS (add to your .bashrc or .zshrc)
   export PATH="$HOME/.local/bin:$PATH"

   # On Windows (PowerShell)
   $env:PATH += ";$env:APPDATA\Python\Python312\Scripts"
   ```

#### Python Version Error

If you get errors related to Python version requirements:

1. Check your Python version:
   ```bash
   python --version
   ```

2. Ensure you have Python 3.12 or later installed, as required by JADE.

### Platform Compatibility

JADE is designed to be cross-platform and can be run on:

- Windows
- macOS
- Linux
- Windows Subsystem for Linux (WSL)

#### WSL Notes

When running in WSL:

1. Make sure you have Python 3.12 or later installed in your WSL environment:
   ```bash
   # Install Python 3.12 in WSL (Ubuntu/Debian)
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3.12-dev python3-pip

   # Create a symbolic link to make 'python' point to 'python3.12'
   sudo ln -sf /usr/bin/python3.12 /usr/bin/python

   # Verify the installation
   python --version  # Should show Python 3.12.x
   ```

2. Install JADE in WSL using one of the methods below:

   **Method 1: Using Poetry (Recommended)**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -

   # Navigate to the JADE repository in WSL
   cd /path/to/jade

   # Install using Poetry
   poetry install

   # Run JADE using Poetry
   poetry run jade --help
   ```

   **Method 2: Using a Virtual Environment (Recommended for Debian/Ubuntu)**
   ```bash
   # Navigate to the JADE repository in WSL
   cd /path/to/jade

   # Create a virtual environment
   python -m venv .venv

   # Activate the virtual environment
   source .venv/bin/activate

   # Install JADE in development mode
   pip install -e .
   ```

   **Method 3: Using pipx**
   ```bash
   # Install pipx if you don't have it
   python -m pip install --user pipx
   python -m pipx ensurepath

   # Install JADE using pipx
   pipx install -e /path/to/jade
   ```

   **Note:** Direct pip installation (`pip install -e .`) will likely fail with an "externally-managed-environment" error in Debian/Ubuntu WSL environments due to PEP 668 restrictions. Use one of the methods above instead.

## Usage

### Running JADE from Any Directory

Depending on your installation method, you can run JADE from any Java repository:

#### If installed with Poetry:

```bash
# Navigate to your Java repository
cd /path/to/your/java/repo

# Option 1: Run JADE using Poetry from the JADE directory
cd /path/to/jade
poetry run jade --project-dir=/path/to/your/java/repo

# Option 2: If you're in a Poetry shell
cd /path/to/jade
poetry shell
cd /path/to/your/java/repo
jade
```

#### If installed in a virtual environment:

```bash
# Activate the virtual environment
# On Windows:
\path\to\jade\.venv\Scripts\activate
# On Linux/macOS:
source /path/to/jade/.venv/bin/activate

# Navigate to your Java repository
cd /path/to/your/java/repo

# Run JADE
jade
```

#### If installed with pipx:

```bash
# Navigate to your Java repository
cd /path/to/your/java/repo

# Run JADE (it will analyze the current directory by default)
jade

# Or explicitly specify the project directory
jade --project-dir=.
```

#### If installed globally:

```bash
# Navigate to your Java repository
cd /path/to/your/java/repo

# Run JADE (it will analyze the current directory by default)
jade

# Or explicitly specify the project directory
jade --project-dir=.
```

### Command Options

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
