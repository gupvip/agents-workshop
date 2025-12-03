#!/usr/bin/env python3
"""
Agentic AI Workshop - One-Click Setup Script
============================================

This script automatically sets up the complete development environment for the
Agentic AI Workshop. It works on Windows, macOS, and Linux.

Prerequisites:
    - Python 3.10 or higher installed
    - .env file with DIAL_API_KEY (copy from .env.example)

Usage:
    python setup.py

What this script does:
    1. Checks Python version (requires 3.10+)
    2. Creates a virtual environment (.venv)
    3. Installs all required dependencies
    4. Installs Jupyter kernel for the virtual environment
    5. Verifies the DIAL/Azure OpenAI configuration
    6. Runs a quick test to ensure everything works

Author: Agentic AI Workshop Team
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Disable colors on Windows if not supported
if platform.system() == 'Windows':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        # Fallback: disable colors
        Colors.HEADER = Colors.BLUE = Colors.CYAN = Colors.GREEN = ''
        Colors.YELLOW = Colors.RED = Colors.ENDC = Colors.BOLD = ''


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_step(step_num, text):
    """Print a step indicator."""
    print(f"{Colors.CYAN}[Step {step_num}]{Colors.ENDC} {text}")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")


def print_info(text):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.absolute()


def check_python_version():
    """Check if Python version is 3.10 or higher."""
    print_step(1, "Checking Python version...")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ is required. Found: Python {version_str}")
        print_info("Please install Python 3.10 or higher from https://www.python.org/downloads/")
        return False
    
    print_success(f"Python {version_str} detected")
    return True


def check_env_file():
    """Check if .env file exists and has an API key configured."""
    print_step(2, "Checking .env configuration...")
    
    project_root = get_project_root()
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print_warning(".env file not found. Creating from .env.example...")
            shutil.copy(env_example, env_file)
            print_info(f"Created .env file at: {env_file}")
            print_warning("Please edit .env and add your API key (DIAL_API_KEY or OPENAI_API_KEY), then run setup again.")
            return False
        else:
            print_error(".env file not found and no .env.example to copy from.")
            print_info("Please create a .env file with DIAL_API_KEY or OPENAI_API_KEY")
            return False
    
    # Check if at least one API key is set
    with open(env_file, 'r') as f:
        content = f.read()
    
    has_dial = 'DIAL_API_KEY=' in content and 'your-dial-api-key-here' not in content
    has_openai = 'OPENAI_API_KEY=' in content and 'your-openai-api-key-here' not in content
    
    # Check for uncommented keys with actual values
    dial_configured = False
    openai_configured = False
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('DIAL_API_KEY=') and not line.startswith('#'):
            value = line.split('=', 1)[1].strip()
            if value and value != 'your-dial-api-key-here' and not value.startswith('$'):
                dial_configured = True
        if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
            value = line.split('=', 1)[1].strip()
            if value and value != 'your-openai-api-key-here':
                openai_configured = True
    
    if dial_configured:
        print_success(".env file configured with DIAL API key")
        return True
    elif openai_configured:
        print_success(".env file configured with OpenAI API key")
        return True
    else:
        print_warning("No API key configured in .env file")
        print_info("Please set either DIAL_API_KEY or OPENAI_API_KEY in your .env file")
        return False


def get_venv_python():
    """Get the path to the Python executable in the virtual environment."""
    project_root = get_project_root()
    venv_path = project_root / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip():
    """Get the path to pip in the virtual environment."""
    project_root = get_project_root()
    venv_path = project_root / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def create_virtual_environment():
    """Create a virtual environment."""
    print_step(3, "Creating virtual environment...")
    
    project_root = get_project_root()
    venv_path = project_root / ".venv"
    
    if venv_path.exists():
        print_info("Virtual environment already exists. Checking if it's valid...")
        venv_python = get_venv_python()
        if venv_python.exists():
            print_success("Existing virtual environment is valid")
            return True
        else:
            print_warning("Invalid virtual environment. Recreating...")
            shutil.rmtree(venv_path)
    
    try:
        print_info("Creating new virtual environment at .venv...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e.stderr}")
        return False


def upgrade_pip():
    """Upgrade pip to the latest version."""
    print_step(4, "Upgrading pip...")
    
    venv_python = get_venv_python()
    
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"pip upgrade warning: {e.stderr}")
        return True  # Continue anyway


def install_dependencies():
    """Install required dependencies from requirements.txt."""
    print_step(5, "Installing dependencies (this may take a few minutes)...")
    
    project_root = get_project_root()
    requirements_file = project_root / "requirements.txt"
    venv_pip = get_venv_pip()
    
    if not requirements_file.exists():
        print_error("requirements.txt not found")
        return False
    
    try:
        print_info("Installing packages from requirements.txt...")
        result = subprocess.run(
            [str(venv_pip), "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies")
        print_info(f"Error details: {e.stderr[-500:] if len(e.stderr) > 500 else e.stderr}")
        return False


def install_jupyter_kernel():
    """Install Jupyter kernel for the virtual environment."""
    print_step(6, "Setting up Jupyter kernel...")
    
    venv_python = get_venv_python()
    
    try:
        # Install ipykernel in the venv
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "ipykernel"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Register the kernel
        subprocess.run(
            [str(venv_python), "-m", "ipykernel", "install", 
             "--user", "--name", "agentic-ai-workshop", 
             "--display-name", "Agentic AI Workshop (Python 3)"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Jupyter kernel 'Agentic AI Workshop' installed")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Jupyter kernel setup warning: {e.stderr}")
        print_info("You may need to manually select the .venv kernel in VS Code")
        return True  # Continue anyway


def verify_installation():
    """Verify that key packages are installed correctly."""
    print_step(7, "Verifying installation...")
    
    venv_python = get_venv_python()
    
    packages_to_check = [
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("langchain_openai", "LangChain OpenAI"),
        ("openai", "OpenAI SDK"),
        ("dotenv", "python-dotenv"),
        ("jupyter", "Jupyter"),
    ]
    
    all_ok = True
    for package, name in packages_to_check:
        try:
            result = subprocess.run(
                [str(venv_python), "-c", f"import {package}; print({package}.__version__ if hasattr({package}, '__version__') else 'OK')"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            print(f"   {Colors.GREEN}✓{Colors.ENDC} {name}: {version}")
        except subprocess.CalledProcessError:
            print(f"   {Colors.RED}✗{Colors.ENDC} {name}: NOT INSTALLED")
            all_ok = False
    
    if all_ok:
        print_success("All packages verified")
    else:
        print_warning("Some packages may not be installed correctly")
    
    return all_ok


def test_dial_connection():
    """Test the LLM connection (DIAL or OpenAI)."""
    print_step(8, "Testing LLM connection...")
    
    venv_python = get_venv_python()
    project_root = get_project_root()
    
    test_script = '''
import os
import sys
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

# Check which provider is configured
dial_key = os.getenv("DIAL_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

use_dial = dial_key and dial_key != "your-dial-api-key-here"
use_openai = openai_key and openai_key != "your-openai-api-key-here"

if not use_dial and not use_openai:
    print("ERROR: No API key configured")
    sys.exit(1)

try:
    if use_dial:
        from langchain_openai import AzureChatOpenAI
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ai-proxy.lab.epam.com")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        model = AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=endpoint,
            api_key=dial_key,
            api_version=api_version,
            temperature=0
        )
        provider = "DIAL"
    else:
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        
        model = ChatOpenAI(
            model=model_name,
            api_key=openai_key,
            temperature=0
        )
        provider = "OpenAI"
    
    response = model.invoke("Say OK")
    print(f"SUCCESS ({provider}): {response.content[:50]}")
except Exception as e:
    print(f"ERROR: {str(e)[:200]}")
    sys.exit(1)
'''
    
    try:
        result = subprocess.run(
            [str(venv_python), "-c", test_script],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30
        )
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            print_success("LLM connection successful!")
            print(f"   Response: {result.stdout.strip()}")
            return True
        else:
            error_msg = result.stderr or result.stdout
            print_warning(f"LLM connection test failed: {error_msg[:200]}")
            print_info("This might be due to network issues or invalid API key")
            print_info("You can still proceed and test manually later")
            return True  # Don't fail setup for connection issues
            
    except subprocess.TimeoutExpired:
        print_warning("Connection test timed out")
        print_info("This might be due to network issues")
        return True
    except Exception as e:
        print_warning(f"Connection test error: {str(e)}")
        return True


def launch_jupyter():
    """Ask user if they want to launch Jupyter and do so."""
    print_step(9, "Launch Jupyter...")
    
    venv_python = get_venv_python()
    project_root = get_project_root()
    
    print(f"\n{Colors.BOLD}Would you like to launch Jupyter Lab now?{Colors.ENDC}")
    print(f"   {Colors.CYAN}[Y]{Colors.ENDC} Yes, launch Jupyter Lab (recommended)")
    print(f"   {Colors.CYAN}[N]{Colors.ENDC} No, I'll use VS Code or launch later")
    
    try:
        response = input(f"\n{Colors.YELLOW}Your choice [Y/n]: {Colors.ENDC}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = 'n'
    
    if response in ['', 'y', 'yes']:
        print_info("Launching Jupyter Lab...")
        print_info("Opening browser at http://localhost:8888")
        print_info("Press Ctrl+C in terminal to stop Jupyter when done")
        print(f"\n{Colors.GREEN}Starting Jupyter Lab...{Colors.ENDC}\n")
        
        # Get the jupyter executable from venv
        if platform.system() == "Windows":
            jupyter_path = project_root / ".venv" / "Scripts" / "jupyter.exe"
        else:
            jupyter_path = project_root / ".venv" / "bin" / "jupyter"
        
        try:
            # Launch Jupyter Lab - this will block
            subprocess.run(
                [str(jupyter_path), "lab"],
                cwd=str(project_root)
            )
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}Jupyter Lab stopped.{Colors.ENDC}")
        except Exception as e:
            print_warning(f"Could not launch Jupyter: {e}")
            print_info("You can launch it manually with: jupyter lab")
    else:
        print_info("Skipping Jupyter launch. You can start it anytime with:")
        print(f"   {Colors.CYAN}jupyter lab{Colors.ENDC}")
        print_next_steps()


def print_next_steps():
    """Print instructions for next steps."""
    print_header("🎉 Setup Complete!")
    
    print(f"""
{Colors.GREEN}Your environment is ready!{Colors.ENDC}

{Colors.BOLD}Quick Start Options:{Colors.ENDC}

   {Colors.YELLOW}Option 1 - Jupyter Lab (recommended for workshops):{Colors.ENDC}
   source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
   jupyter lab
   
   {Colors.YELLOW}Option 2 - VS Code:{Colors.ENDC}
   code .
   Then select ".venv" or "Agentic AI Workshop" kernel

{Colors.BOLD}Start Learning:{Colors.ENDC}
   Open: session-1/module-0-introduction-to-agents.ipynb

{Colors.BOLD}Useful Commands:{Colors.ENDC}

   {Colors.CYAN}# Activate virtual environment:{Colors.ENDC}
   source .venv/bin/activate  # macOS/Linux
   .venv\\Scripts\\activate     # Windows

   {Colors.CYAN}# Launch Jupyter Lab:{Colors.ENDC}
   jupyter lab

   {Colors.CYAN}# Verify setup:{Colors.ENDC}
   python verify_setup.py

{Colors.BOLD}Need Help?{Colors.ENDC}
   - Check the README.md file
   - Ensure your .env file has DIAL_API_KEY or OPENAI_API_KEY

{Colors.GREEN}Happy Learning! 🚀{Colors.ENDC}
""")


def main():
    """Main setup function."""
    print_header("🤖 Agentic AI Workshop - Setup")
    
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {get_project_root()}")
    
    # Run setup steps
    steps = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Virtual Environment", create_virtual_environment),
        ("Pip Upgrade", upgrade_pip),
        ("Dependencies", install_dependencies),
        ("Jupyter Kernel", install_jupyter_kernel),
        ("Verification", verify_installation),
        ("DIAL Connection", test_dial_connection),
    ]
    
    failed_steps = []
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
                if step_name in ["Python Version", "Environment File", "Virtual Environment", "Dependencies"]:
                    print_error(f"Critical step '{step_name}' failed. Setup cannot continue.")
                    sys.exit(1)
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {str(e)}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print_warning(f"Setup completed with warnings in: {', '.join(failed_steps)}")
    
    # Ask to launch Jupyter
    launch_jupyter()


if __name__ == "__main__":
    main()
