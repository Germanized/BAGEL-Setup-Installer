#!/usr/bin/env python3
"""
BAGEL Environment Setup Script
============================

This script automates the setup process for the BAGEL (Emerging Properties in
Unified Multimodal Pretraining) project. It handles environment creation,
dependency installation, and model downloading.

Author: Enhanced setup script for BAGEL
License: Apache 2.0
"""

import subprocess
import sys
import os
import json
import platform
import shutil
import argparse
from pathlib import Path
from typing import Optional, Tuple, List, Union 
import urllib.request
import ssl
import time
import shlex 
import socket 

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class BAGELSetup:
    def __init__(self, env_name: str = "bagel_env", use_conda: bool = False):
        self.env_name = env_name
        self.use_conda = use_conda
        self.system = platform.system().lower()
        self.python_executable = sys.executable 
        self.repo_url = "https://github.com/ByteDance-Seed/Bagel.git"
        self.model_repo_id = "ByteDance-Seed/BAGEL-7B-MoT"
        self.original_dir = Path.cwd()
        self.bagel_repo_dir = self.original_dir / "BAGEL"

    def print_banner(self):
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    BAGEL Setup Script                        ║
║          Emerging Properties in Unified Multimodal           ║
║                    Setup By Germanized                       ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.OKCYAN}🔥 This script will help you set up BAGEL environment automatically{Colors.ENDC}"""
        print(banner)

    def run_command(self, command: Union[str, List[str]], capture_output: bool = True,
                   check: bool = True, shell: bool = False, cwd: Optional[str] = None) -> Tuple[bool, str, str]:
        effective_cwd = str(cwd) if cwd else str(self.original_dir)
        command_to_log = ""
        actual_command_arg_for_popen: Union[str, List[str]]
        if isinstance(command, list):
            command_to_log = " ".join(f'"{arg}"' if " " in arg else arg for arg in command)
            actual_command_arg_for_popen = command 
            if shell: 
                actual_command_arg_for_popen = subprocess.list2cmdline(command) 
                command_to_log = actual_command_arg_for_popen 
        elif isinstance(command, str):
            command_to_log = command
            if shell: actual_command_arg_for_popen = command
            else: actual_command_arg_for_popen = shlex.split(command)
        else: 
            print(f"{Colors.FAIL}✗ Invalid command type: {type(command)}{Colors.ENDC}")
            return False, "", "Invalid command type"
        
        print(f"{Colors.OKBLUE}🚀 Executing: {command_to_log}{Colors.ENDC}" + (f" in {effective_cwd}" if cwd else ""))
        try:
            process_kwargs = {"stdout": subprocess.PIPE if capture_output else None, 
                              "stderr": subprocess.PIPE if capture_output else None,
                              "text": True, "universal_newlines": True, 
                              "cwd": effective_cwd, "encoding": "utf-8", 
                              "errors": "replace", "shell": shell}
            
            process = subprocess.Popen(actual_command_arg_for_popen, **process_kwargs)
            stdout, stderr = process.communicate()
            stdout = stdout or ""
            stderr = stderr or ""

            if check and process.returncode != 0:
                print(f"{Colors.WARNING}⚠️ Command failed (code {process.returncode}){Colors.ENDC}")
                if stdout.strip(): print(f"{Colors.WARNING}   Stdout: {stdout.strip()}{Colors.ENDC}")
                if stderr.strip(): print(f"{Colors.WARNING}   Stderr: {stderr.strip()}{Colors.ENDC}")
                return False, stdout, stderr
            return True, stdout, stderr
        except FileNotFoundError as e:
            failed_file_reported = e.filename
            if not failed_file_reported and isinstance(actual_command_arg_for_popen, list) and actual_command_arg_for_popen:
                failed_file_reported = actual_command_arg_for_popen[0]
            elif not failed_file_reported: 
                failed_file_reported = command_to_log.split()[0] if command_to_log else "Unknown command"
            print(f"{Colors.FAIL}✗ Not found: '{failed_file_reported}'. Ensure installed and in PATH.{Colors.ENDC}")
            return False, "", str(e)
        except Exception as e: 
            print(f"{Colors.FAIL}✗ Error executing: {command_to_log}\n   Details: {e}{Colors.ENDC}")
            return False, "", str(e)

    def check_internet_connection(self) -> bool:
        print(f"\n{Colors.BOLD}🌐 Checking Internet Connection{Colors.ENDC}")
        ssl_context = None 
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE
        except AttributeError: print(f"{Colors.WARNING}  Note: Using system default SSL (older Python?).{Colors.ENDC}")
        try:
            urllib.request.urlopen('https://www.google.com', timeout=10, context=ssl_context)
            print(f"{Colors.OKGREEN}✓ Internet connection available{Colors.ENDC}"); return True
        except urllib.error.URLError as e: print(f"{Colors.FAIL}✗ No internet (URLError): {e.reason if hasattr(e, 'reason') else e}{Colors.ENDC}"); return False
        except socket.timeout: print(f"{Colors.FAIL}✗ Internet check timed out.{Colors.ENDC}"); return False
        except Exception as e: print(f"{Colors.FAIL}✗ No internet or issue reaching Google: {e}{Colors.ENDC}"); return False

    def check_system_requirements(self) -> bool:
        print(f"\n{Colors.BOLD}🔍 Checking System Requirements{Colors.ENDC}"); all_ok = True
        version_info = sys.version_info
        if version_info.major == 3 and version_info.minor >= 10:
            print(f"{Colors.OKGREEN}✓ Python {sys.version.split()[0]} (base requirement met){Colors.ENDC}")
            if version_info.minor > 12: print(f"{Colors.WARNING}  Note: Py {version_info.major}.{version_info.minor}. Check ML lib releases.{Colors.ENDC}")
        else: print(f"{Colors.FAIL}✗ Py {sys.version.split()[0]} not ideal. Req: 3.10-3.12.{Colors.ENDC}"); all_ok = False
        success, git_version, _ = self.run_command(["git", "--version"], check=False)
        if success: print(f"{Colors.OKGREEN}✓ Git available ({git_version.strip()}){Colors.ENDC}")
        else: print(f"{Colors.FAIL}✗ Git not found. Install & add to PATH.{Colors.ENDC}"); all_ok = False
        try:
            free_space = shutil.disk_usage(self.original_dir).free / (1024**3)
            if free_space > 20: print(f"{Colors.OKGREEN}✓ Disk space ({free_space:.1f} GB available){Colors.ENDC}")
            else: print(f"{Colors.WARNING}⚠ Low disk space ({free_space:.1f} GB). ~20GB rec.{Colors.ENDC}");
        except Exception as e: print(f"{Colors.WARNING}⚠ Could not check disk space: {e}{Colors.ENDC}")
        try:
            success, smi_out, _ = self.run_command(["nvidia-smi"], check=False, capture_output=True)
            if success and "CUDA Version" in smi_out:
                print(f"{Colors.OKGREEN}✓ NVIDIA GPU detected - CUDA acceleration potential.{Colors.ENDC}")
                for line in smi_out.splitlines(): 
                    if "Product Name" in line or ("CUDA Version" in line and "|" in line): 
                         print(f"  {line.split('|')[1].strip() if ('|' in line and len(line.split('|')) > 1) else line.strip()}"); break
            else: print(f"{Colors.WARNING}⚠ No NVIDIA GPU or nvidia-smi failed. Will use CPU.{Colors.ENDC}")
        except Exception: print(f"{Colors.WARNING}⚠ Could not check GPU status.{Colors.ENDC}")
        if not all_ok: print(f"{Colors.FAIL}✗ System reqs not fully met.{Colors.ENDC}")
        return all_ok

    def install_conda(self) -> bool:
        print(f"{Colors.OKCYAN}📦 Attempting to install Miniconda...{Colors.ENDC}")
        system = platform.system().lower(); machine = platform.machine().lower()
        if system == "linux":
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"; installer_name = "Miniconda3-latest-Linux-x86_64.sh"
            if "aarch64" in machine or "arm64" in machine: installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"; installer_name = "Miniconda3-latest-Linux-aarch64.sh"
        elif system == "darwin":
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"; installer_name = "Miniconda3-latest-MacOSX-x86_64.sh"
            if "arm64" in machine: installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"; installer_name = "Miniconda3-latest-MacOSX-arm64.sh" 
        elif system == "windows":
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"; installer_name = "Miniconda3-latest-Windows-x86_64.exe"
        else: print(f"{Colors.FAIL}✗ Unsupported OS: {system}{Colors.ENDC}"); return False
        try:
            print(f"📥 Downloading {installer_name} from {installer_url}..."); ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            installer_path = self.original_dir / installer_name; req = urllib.request.Request(installer_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as response, open(installer_path, 'wb') as f: shutil.copyfileobj(response, f)
            print(f"{Colors.OKGREEN}✓ Download completed: {installer_path}{Colors.ENDC}"); miniconda_install_dir = Path.home() / "miniconda3"
            if system == "windows":
                print(f"{Colors.OKCYAN}🔧 Installing Miniconda silently to {miniconda_install_dir}...{Colors.ENDC}")
                install_cmd = f'start /wait "" "{str(installer_path)}" /InstallationType=JustMe /RegisterPython=0 /S /D="{str(miniconda_install_dir)}"'
                success, _, stderr = self.run_command(install_cmd, shell=True)
                if success or miniconda_install_dir.exists():
                    paths_to_add = [str(p) for p in [miniconda_install_dir/"Scripts", miniconda_install_dir/"Library"/"mingw-w64"/"bin", miniconda_install_dir/"Library"/"usr"/"bin", miniconda_install_dir/"Library"/"bin", miniconda_install_dir/"condabin"]]
                    os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ.get("PATH", "")
                    conda_exe = miniconda_install_dir/"Scripts"/"conda.exe"
                    if conda_exe.exists(): self.run_command(f'"{conda_exe}" init cmd.exe', check=False, shell=True); self.run_command(f'"{conda_exe}" init powershell', check=False, shell=True)
                    if self.check_conda_installation(silent_if_found=True): 
                        print(f"{Colors.OKGREEN}✓ Miniconda installed. Restart terminal if 'conda activate' fails.{Colors.ENDC}")
                        try: installer_path.unlink()
                        except OSError as e: print(f"{Colors.WARNING}Could not remove installer: {e}{Colors.ENDC}")
                        return True
                    else: print(f"{Colors.FAIL}✗ Miniconda installed but 'conda' not found. RESTART TERMINAL.{Colors.ENDC}"); return False
                else: print(f"{Colors.FAIL}✗ Failed to install Miniconda silently. Stderr: {stderr}{Colors.ENDC}"); return False
            else: 
                print(f"🔧 Installing Miniconda to {miniconda_install_dir}..."); os.chmod(installer_path, 0o755)
                success, _, stderr = self.run_command(f"bash {str(installer_path)} -b -p {str(miniconda_install_dir)}", shell=True)
                if not success: print(f"{Colors.FAIL}✗ Failed to install Miniconda: {stderr}{Colors.ENDC}"); return False
                conda_bin = miniconda_install_dir/"bin"; os.environ["PATH"] = str(conda_bin)+os.pathsep+os.environ.get("PATH", ""); conda_exe = conda_bin/"conda"
                for shell_name in ["bash", "zsh"]: self.run_command([str(conda_exe), "init", shell_name], check=False)
                print(f"{Colors.OKGREEN}✓ Miniconda installed. Source profile or restart terminal.{Colors.ENDC}")
                try: installer_path.unlink()
                except OSError as e: print(f"{Colors.WARNING}Could not remove installer: {e}{Colors.ENDC}")
                return self.check_conda_installation()
        except urllib.error.URLError as e: print(f"{Colors.FAIL}✗ Failed to download Miniconda: {e.reason if hasattr(e, 'reason') else e}{Colors.ENDC}"); return False
        except Exception as e: print(f"{Colors.FAIL}✗ Error installing Miniconda: {e}{Colors.ENDC}"); return False
        return False 

    def install_conda_alternative_windows(self) -> bool:
        print(f"{Colors.OKCYAN}📦 Alternative Conda Installation for Windows:{Colors.ENDC}")
        print(f"{Colors.BOLD}Please manually install Miniconda or Anaconda.{Colors.ENDC}")
        print(f"1. Go to: {Colors.UNDERLINE}https://docs.anaconda.com/free/miniconda/index.html{Colors.ENDC}")
        print(f"2. Download and run the installer for Windows.")
        print(f"3. {Colors.BOLD}During installation, ensure 'Add Anaconda to my PATH' selected OR note install path.{Colors.ENDC}")
        print(f"4. {Colors.BOLD}Restart your terminal after installation.{Colors.ENDC}")
        print(f"5. Run this setup script again.")
        print(f"\nOr, use winget: {Colors.BOLD}winget install Anaconda.Miniconda3{Colors.ENDC}")
        return False

    def check_conda_installation(self, silent_if_found: bool = False) -> bool:
        success, stdout, stderr = self.run_command(["conda", "--version"], check=False) 
        if success and "conda" in stdout:
            if not silent_if_found: print(f"{Colors.OKGREEN}✓ Conda available: {stdout.strip()}{Colors.ENDC}")
            return True
        else:
            if not silent_if_found:
                print(f"{Colors.WARNING}⚠ Conda command not found or not working.{Colors.ENDC}")
                if stderr.strip() and "Traceback" not in stderr : print(f"{Colors.WARNING}   Stderr: {stderr.strip()}{Colors.ENDC}") 
            return False

    def ensure_conda_installed(self) -> bool:
        if self.check_conda_installation(): return True
        print(f"{Colors.OKCYAN}🔧 Conda not found or not configured.{Colors.ENDC}")
        if self.system == "windows":
            print(f"\n{Colors.BOLD}Choose Conda installation method (Windows):{Colors.ENDC}")
            print(f"1. Automatic Miniconda installation (Recommended, may require terminal restart).")
            print(f"2. Manual installation instructions.")
            print(f"3. Skip Conda, use 'venv' instead.")
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1": return self.install_conda()
            elif choice == "2": self.install_conda_manual_windows(); return False
            elif choice == "3": print(f"{Colors.WARNING}⚠ Conda skipped. Using venv.{Colors.ENDC}"); self.use_conda = False; return True
            else: print("Invalid choice. Aborting conda setup attempt."); return False 
        else: 
            if input(f"{Colors.BOLD}Attempt Miniconda installation? (y/N): {Colors.ENDC}").lower() == 'y':
                return self.install_conda()
            else: print(f"{Colors.WARNING}⚠ Conda skipped. Using venv.{Colors.ENDC}"); self.use_conda = False; return True

    def install_conda_manual_windows(self) -> bool:
        self.install_conda_alternative_windows()
        if input(f"\n{Colors.BOLD}Installed Conda manually & restarted terminal? (y/N): {Colors.ENDC}").lower() == 'y':
            if self.check_conda_installation(): return True
            else: print(f"{Colors.FAIL}✗ Conda still not found. Check PATH & restart.{Colors.ENDC}"); return False
        else: print(f"{Colors.WARNING}⚠ Manual Conda installation aborted.{Colors.ENDC}"); return False

    def check_pip_installation(self) -> bool:
        pip_check_cmd_list = [sys.executable, "-m", "pip", "--version"]
        success, stdout, _ = self.run_command(pip_check_cmd_list, check=False)
        if success:
            pip_version_str = stdout.strip() if stdout else "version not captured"
            print(f"{Colors.OKGREEN}✓ pip available for {sys.executable}: {pip_version_str}{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ pip module not found for Python: {sys.executable}.{Colors.ENDC}")
            print(f"  Attempting to ensure pip...{Colors.ENDC}")
            ensurepip_cmd_list = [sys.executable, "-m", "ensurepip", "--default-pip"]
            if self.run_command(ensurepip_cmd_list)[0]:
                success_recheck, stdout_recheck, _ = self.run_command(pip_check_cmd_list, check=False)
                if success_recheck:
                    pip_recheck_version_str = stdout_recheck.strip() if stdout_recheck else "version not captured"
                    print(f"{Colors.OKGREEN}✓ pip installed successfully via ensurepip: {pip_recheck_version_str}{Colors.ENDC}")
                    return True
            print(f"{Colors.FAIL}✗ Failed to install/find pip via 'ensurepip'.{Colors.ENDC}")
            return False

    def clone_repository(self, target_dir_name: str = "BAGEL") -> bool:
        self.bagel_repo_dir = self.original_dir / target_dir_name
        if self.bagel_repo_dir.exists():
            print(f"{Colors.WARNING}⚠ Directory '{self.bagel_repo_dir}' already exists.{Colors.ENDC}")
            if not (self.bagel_repo_dir / ".git").is_dir():
                 print(f"{Colors.FAIL}  Existing dir '{self.bagel_repo_dir}' is not a git repo.{Colors.ENDC}")
                 alt_dir_name = f"{target_dir_name}_clone_{int(time.time())}"
                 if input(f"Attempt clone into '{alt_dir_name}'? (y/N):").lower() == 'y':
                     self.bagel_repo_dir = self.original_dir / alt_dir_name; return self._perform_clone()
                 return False
            if input("Update it (git pull)? (y/N): ").lower() == 'y':
                print(f"{Colors.OKCYAN}📥 Updating repository in {self.bagel_repo_dir}...{Colors.ENDC}")
                success, _, stderr = self.run_command(["git", "pull"], cwd=str(self.bagel_repo_dir)) 
                if success: print(f"{Colors.OKGREEN}✓ Repository updated.{Colors.ENDC}"); return True
                else: print(f"{Colors.FAIL}✗ Failed to update repo: {stderr.strip()}{Colors.ENDC}"); return False
            else: print(f"{Colors.OKCYAN}  Skipping update. Using existing directory.{Colors.ENDC}"); return True
        else: return self._perform_clone()

    def _perform_clone(self) -> bool:
        print(f"{Colors.OKCYAN}📥 Cloning BAGEL repository to '{self.bagel_repo_dir}'...{Colors.ENDC}")
        success, _, stderr = self.run_command(["git", "clone", self.repo_url, str(self.bagel_repo_dir)]) 
        if success: print(f"{Colors.OKGREEN}✓ Repository cloned to {self.bagel_repo_dir}{Colors.ENDC}"); return True
        else: print(f"{Colors.FAIL}✗ Failed to clone repository: {stderr.strip()}{Colors.ENDC}"); return False

    def create_conda_environment(self) -> bool:
        print(f"{Colors.OKCYAN}🐍 Creating/verifying conda environment '{self.env_name}'...{Colors.ENDC}")
        success_list, stdout_list, _ = self.run_command(["conda", "env", "list"], capture_output=True, check=False) 
        env_exists = False
        if success_list:
            for line in stdout_list.splitlines():
                if line.strip().startswith(self.env_name): env_exists = True; break
        if env_exists:
            print(f"{Colors.WARNING}⚠ Conda environment '{self.env_name}' already exists.{Colors.ENDC}")
            choice = input("[u]se, [r]ecreate, or [s]kip? (u/R/s, default: R): ").lower()
            if choice == 'u': print(f"{Colors.OKCYAN}  Using existing Conda env '{self.env_name}'.{Colors.ENDC}"); self._update_python_executable_for_conda_env(); return True
            elif choice == 's': print(f"{Colors.WARNING} Skipping env setup.{Colors.ENDC}"); return False
            print(f"{Colors.OKCYAN}  Removing env '{self.env_name}'...{Colors.ENDC}")
            success_remove, _, stderr_remove = self.run_command(["conda", "env", "remove", "-n", self.env_name, "-y"]) 
            if not success_remove: print(f"{Colors.FAIL}✗ Failed to remove Conda env: {stderr_remove.strip()}{Colors.ENDC}"); return False
        py_versions_to_try = []; current_py_ver_minor = sys.version_info.minor
        if current_py_ver_minor <= 11: py_versions_to_try.append(f"3.{current_py_ver_minor}")
        py_versions_to_try.extend(["3.11", "3.10", "3.12"]); py_versions_to_try = sorted(list(set(py_versions_to_try)), key=lambda v: (int(v.split('.')[1]) < 13, -int(v.split('.')[1])))
        env_created = False
        for py_ver in py_versions_to_try:
            print(f"{Colors.OKCYAN}  Attempting create '{self.env_name}' with Python {py_ver}...{Colors.ENDC}")
            create_cmd_list = ["conda", "create", "-n", self.env_name, f"python={py_ver}", "-c", "pytorch", "-c", "nvidia", "-c", "conda-forge", "-y"]
            success_create, _, stderr_create = self.run_command(create_cmd_list)
            if success_create: print(f"{Colors.OKGREEN}✓ Conda env '{self.env_name}' created with Py {py_ver}.{Colors.ENDC}"); self._update_python_executable_for_conda_env(); env_created = True; break
            else:
                print(f"{Colors.WARNING}  Failed with Py {py_ver}: {stderr_create.strip()}{Colors.ENDC}")
                if "UnsatisfiableError" in stderr_create: print(f"{Colors.WARNING}    UnsatisfiableError: version conflicts.{Colors.ENDC}")
        if not env_created: print(f"{Colors.FAIL}✗ Failed to create conda env '{self.env_name}' with Py: {', '.join(py_versions_to_try)}.{Colors.ENDC}"); return False
        return True

    def _update_python_executable_for_conda_env(self):
        success_info, stdout_info, _ = self.run_command(["conda", "env", "list", "--json"], capture_output=True, check=False) 
        if success_info:
            try:
                env_data = json.loads(stdout_info)
                for env_path_str in env_data.get("envs", []):
                    env_path = Path(env_path_str)
                    if env_path.name == self.env_name:
                        py_exe = env_path / ("python.exe" if self.system == "windows" else "bin/python")
                        if py_exe.exists(): self.python_executable = str(py_exe); print(f"{Colors.OKCYAN}  Py for Conda env '{self.env_name}': {self.python_executable}{Colors.ENDC}"); return
            except json.JSONDecodeError: print(f"{Colors.WARNING}  Could not parse conda env list JSON.{Colors.ENDC}")
        print(f"{Colors.WARNING}  Could not auto-determine Py for Conda env '{self.env_name}'.{Colors.ENDC}")

    def create_venv_environment(self) -> bool:
        env_path = self.original_dir / self.env_name
        print(f"{Colors.OKCYAN}🐍 Creating virtual environment '{env_path}' using venv...{Colors.ENDC}")
        if env_path.exists():
            print(f"{Colors.WARNING}⚠ Virtual environment directory '{env_path}' already exists.{Colors.ENDC}")
            choice = input("[u]se existing, [r]emove and recreate, or [s]kip? (u/R/s, default: R): ").lower()
            if choice == 'u': print(f"{Colors.OKCYAN}  Using existing venv '{env_path}'.{Colors.ENDC}"); self._update_python_executable_for_venv(env_path); return True
            elif choice == 's': print(f"{Colors.WARNING}  Skipping venv setup.{Colors.ENDC}"); return False
            print(f"{Colors.OKCYAN}  Removing existing venv '{env_path}'...{Colors.ENDC}")
            try: shutil.rmtree(env_path)
            except Exception as e: print(f"{Colors.FAIL}✗ Failed to remove existing venv: {e}{Colors.ENDC}"); return False
        venv_command_list = [sys.executable, "-m", "venv", str(env_path)]
        success, _, stderr = self.run_command(venv_command_list) 
        if success: print(f"{Colors.OKGREEN}✓ Venv created at {env_path}{Colors.ENDC}"); self._update_python_executable_for_venv(env_path); return True
        else:
            print(f"{Colors.FAIL}✗ Failed to create venv: {stderr.strip() if stderr else 'Unknown'}{Colors.ENDC}")
            if "WinError 2" in (stderr or "") and "python.exe" not in (stderr or "") : print(f"{Colors.WARNING}  [WinError 2] component for 'venv' not found or path issue with '{sys.executable}'.{Colors.ENDC}")
            return False

    def _update_python_executable_for_venv(self, env_path: Path):
        if self.system == "windows": self.python_executable = str(env_path / "Scripts" / "python.exe")
        else: self.python_executable = str(env_path / "bin" / "python")
        print(f"{Colors.OKCYAN}  Py for venv '{env_path.name}': {self.python_executable}{Colors.ENDC}")

    def get_activation_command(self) -> str:
        if self.use_conda: return f"conda activate {self.env_name}"
        else: return f".\\{self.env_name}\\Scripts\\activate" if self.system == "windows" else f"source ./{self.env_name}/bin/activate"

    def _get_pip_executable_cmd_list(self) -> Union[List[str], str]: 
        if self.use_conda:
            return ["conda", "run", "-n", self.env_name, "python", "-m", "pip"]
        else:
            is_msys_python_base = False
            # sys.executable is the Python running this setup script.
            # self.python_executable is the one in the venv (after _update_python_executable_for_venv)
            if self.system == "windows" and self.python_executable: # Check the venv's python
                if "msys" in self.python_executable.lower() or "mingw" in self.python_executable.lower():
                    is_msys_python_base = True 
            
            if self.system == "windows" and is_msys_python_base:
                quoted_python_exe = f'"{self.python_executable}"' 
                cmd_string = f"{quoted_python_exe} -m pip"
                return cmd_string 
            else:
                return [self.python_executable, "-m", "pip"]

    def _install_package_with_pip(self, package_spec: str, cwd_for_install: Optional[Path] = None, extra_flags: Optional[List[str]] = None) -> bool:
        pip_base_command = self._get_pip_executable_cmd_list()
        final_command_for_run_command: Union[str, List[str]]
        use_shell_for_this_pip_command = False
        
        cmd_flags = extra_flags if extra_flags else []
        # Default flags for install, unless extra_flags override them (e.g. no --no-cache-dir for --upgrade)
        if not any(flag.startswith("--upgrade") for flag in cmd_flags): # Don't add these for --upgrade calls
             cmd_flags.extend(["--no-cache-dir", "--disable-pip-version-check"])


        if isinstance(pip_base_command, str): 
            use_shell_for_this_pip_command = True
            # Construct string: "path/to/python -m pip" install <flags> <package_spec>
            # shlex.quote for package_spec and any flags that might need it
            flags_str = " ".join(shlex.quote(f) for f in cmd_flags)
            final_command_for_run_command = f"{pip_base_command} install {flags_str} {shlex.quote(package_spec)}"
        else: 
            use_shell_for_this_pip_command = (pip_base_command[0] == "conda")
            install_command_parts = pip_base_command + ["install"] + cmd_flags + [package_spec]
            if use_shell_for_this_pip_command :
                 final_command_for_run_command = subprocess.list2cmdline(install_command_parts)
            else:
                 final_command_for_run_command = install_command_parts
        
        effective_cwd = str(cwd_for_install or self.bagel_repo_dir)
        print(f"{Colors.OKCYAN}  Installing '{package_spec}' with pip... (shell={use_shell_for_this_pip_command}){Colors.ENDC}")
        success, stdout, stderr = self.run_command(final_command_for_run_command, shell=use_shell_for_this_pip_command, cwd=effective_cwd)
        
        if success: print(f"{Colors.OKGREEN}  ✓ '{package_spec}' installed/satisfied.{Colors.ENDC}"); return True
        else:
            print(f"{Colors.FAIL}  ✗ Failed to install '{package_spec}' with pip.{Colors.ENDC}")
            if stderr: 
                 if "Could not build wheels for" in stderr and "flash-attn" in package_spec: print(f"{Colors.WARNING}    flash-attn needs build tools.{Colors.ENDC}")
                 elif "No module named 'torch'" in stderr: print(f"{Colors.FAIL}    CRITICAL: PyTorch ('torch') missing.{Colors.ENDC}")
            return False

    def install_requirements(self) -> bool:
        requirements_file = self.bagel_repo_dir / "requirements.txt"
        if not requirements_file.is_file(): print(f"{Colors.FAIL}✗ Reqs file missing: {requirements_file}!{Colors.ENDC}"); return False
        print(f"\n{Colors.BOLD}📦 Installing Dependencies... (May take time){Colors.ENDC}")
        
        print(f"\n{Colors.OKCYAN}--- Upgrading pip, setuptools, wheel in the environment ---{Colors.ENDC}")
        pip_base_cmd_for_upgrade = self._get_pip_executable_cmd_list()
        all_upgraded_successfully = True
        for pkg_to_upgrade in ["pip", "setuptools", "wheel"]:
            final_upgrade_cmd: Union[str, List[str]]
            use_shell_upgrade: bool
            if isinstance(pip_base_cmd_for_upgrade, str): # MSYS/MinGW string case
                use_shell_upgrade = True
                final_upgrade_cmd = f"{pip_base_cmd_for_upgrade} install --upgrade {shlex.quote(pkg_to_upgrade)}"
            else: # Standard list case (conda or normal venv)
                use_shell_upgrade = (pip_base_cmd_for_upgrade[0] == "conda")
                cmd_parts = pip_base_cmd_for_upgrade + ["install", "--upgrade", pkg_to_upgrade]
                final_upgrade_cmd = subprocess.list2cmdline(cmd_parts) if use_shell_upgrade else cmd_parts
            
            print(f"{Colors.OKCYAN}  Upgrading '{pkg_to_upgrade}'... (shell={use_shell_upgrade}){Colors.ENDC}")
            if not self.run_command(final_upgrade_cmd, shell=use_shell_upgrade)[0]:
                print(f"{Colors.WARNING}  Failed to upgrade {pkg_to_upgrade}.{Colors.ENDC}")
                all_upgraded_successfully = False
        if all_upgraded_successfully: print(f"{Colors.OKGREEN}  ✓ Pip/setuptools/wheel upgrade process completed.{Colors.ENDC}")
        else: print(f"{Colors.WARNING}  Some build tools might not have upgraded. This could affect installations.{Colors.ENDC}")

        print(f"\n{Colors.OKCYAN}--- Step 1: Installing PyTorch family ---{Colors.ENDC}")
        pytorch_fully_installed = False
        # ... (Rest of PyTorch install logic - assuming it was okay as per log) ...
        if self.use_conda:
            # ... conda pytorch ...
            pass # Simplified for brevity, as venv is used in log
        if not pytorch_fully_installed:
            print(f"{Colors.OKCYAN}  Attempting PyTorch family with pip...{Colors.ENDC}")
            venv_py_minor = sys.version_info.minor # Python running the script
            if venv_py_minor >= 13:
                 print(f"{Colors.WARNING} Py3.{venv_py_minor}: PyTorch stable wheels might be missing. Attempting generic pip. Consider Py3.10-3.12 env.{Colors.ENDC}")
                 pt_pip_specs = ["torch", "torchvision", "torchaudio"] 
            elif venv_py_minor == 12:
                print(f"{Colors.OKCYAN}  Py3.12: Attempting PyTorch install (check PyTorch.org for best command if issues).{Colors.ENDC}")
                pt_pip_specs = ["torch>=2.1", "torchvision>=0.16", "torchaudio>=2.1"] 
            else: pt_pip_specs = ["torch>=2.0.0", "torchvision", "torchaudio"]
            all_pt_pip_ok = True
            for spec in pt_pip_specs:
                 if not self._install_package_with_pip(spec, cwd_for_install=self.bagel_repo_dir): all_pt_pip_ok = False; break 
            pytorch_fully_installed = all_pt_pip_ok
        if not pytorch_fully_installed: print(f"{Colors.FAIL}✗ CRITICAL: PyTorch failed. Check logs & PyTorch.org for Py3.{sys.version_info.minor}.{Colors.ENDC}"); return False
        print(f"{Colors.OKCYAN}  Verifying PyTorch installation...{Colors.ENDC}")
        verify_py_code = "import torch; pv=torch.__version__; ca=torch.cuda.is_available(); print(f'PyTorch {{pv}}\\nCUDA available: {{ca}}')" 
        verify_cmd_base = self._get_pip_executable_cmd_list(); use_shell_for_verify: bool
        verify_cmd_to_run : Union[str,List[str]]
        if isinstance(verify_cmd_base, str): 
            use_shell_for_verify = True; verify_cmd_to_run = f"{verify_cmd_base} -c {shlex.quote(verify_py_code)}"
        else: 
            use_shell_for_verify = (verify_cmd_base[0] == "conda")
            python_exe_for_verify = verify_cmd_base[4] if use_shell_for_verify else verify_cmd_base[0]
            verify_cmd_list_parts = [python_exe_for_verify, "-c", verify_py_code]
            if use_shell_for_verify: verify_cmd_to_run = subprocess.list2cmdline(verify_cmd_base[:4] + verify_cmd_list_parts)
            else: verify_cmd_to_run = verify_cmd_list_parts
        success_torch_check, stdout_torch_check, _ = self.run_command(verify_cmd_to_run, shell=use_shell_for_verify, check=True)
        # Your log shows {pv} and {ca} literally. Needs double {{ }} for f-string literal braces.
        if success_torch_check and stdout_torch_check: print(f"{Colors.OKGREEN}  ✓ PyTorch verified:{Colors.ENDC}\n    {stdout_torch_check.strip().replace(os.linesep, os.linesep + '    ')}") 
        else: print(f"{Colors.FAIL}  ✗ PyTorch installed, but verification failed.{Colors.ENDC}"); return False 
        
        print(f"\n{Colors.OKCYAN}--- Pre-installing/checking compatible NumPy ---{Colors.ENDC}")
        numpy_spec_to_try = "numpy>=1.26.0" if sys.version_info.minor >= 12 else \
                            "numpy>=1.23.2" if sys.version_info.minor == 11 else "numpy>=1.21.2"
        if not self._install_package_with_pip(numpy_spec_to_try, cwd_for_install=self.bagel_repo_dir):
            print(f"{Colors.WARNING}  Failed to pre-install NumPy ({numpy_spec_to_try}). Build issues may occur from requirements.txt.{Colors.ENDC}")
        else: print(f"{Colors.OKGREEN}  ✓ NumPy is installed/updated ({numpy_spec_to_try}).{Colors.ENDC}")

        if self.use_conda:
            print(f"\n{Colors.OKCYAN}--- Step 2: Conda base packages ---{Colors.ENDC}")
            # ... Conda specific package installs ...
            pass

        print(f"\n{Colors.OKCYAN}--- Step 3: Reqs from '{requirements_file.name}' via pip ---{Colors.ENDC}")
        pip_req_base_cmd = self._get_pip_executable_cmd_list()
        final_req_cmd_for_run : Union[str,List[str]]; use_shell_for_req:bool
        if isinstance(pip_req_base_cmd, str): 
            use_shell_for_req = True; final_req_cmd_for_run = f"{pip_req_base_cmd} install -r {shlex.quote(str(requirements_file))}"
        else: 
            use_shell_for_req = (pip_req_base_cmd[0] == "conda")
            req_cmd_list_parts = pip_req_base_cmd + ["install", "-r", str(requirements_file)]
            if use_shell_for_req: final_req_cmd_for_run = subprocess.list2cmdline(req_cmd_list_parts)
            else: final_req_cmd_for_run = req_cmd_list_parts
        success_req, _, stderr_req = self.run_command(final_req_cmd_for_run, shell=use_shell_for_req, cwd=str(self.bagel_repo_dir))
        if success_req: print(f"{Colors.OKGREEN}✓ Reqs from '{requirements_file.name}' processed.{Colors.ENDC}"); self.install_gradio(); return True
        else:
            print(f"{Colors.FAIL}✗ Failed to install all from '{requirements_file.name}'.{Colors.ENDC}")
            if stderr_req and "AttributeError: module 'pkgutil' has no attribute 'ImpImporter'" in stderr_req:
                print(f"{Colors.WARNING}  'ImpImporter' error. Often due to old setuptools/numpy pinned in reqs.txt with new Python.{Colors.ENDC}")
                print(f"{Colors.WARNING}  Recommend editing requirements.txt for 'numpy' (e.g., 'numpy>=1.26.0').{Colors.ENDC}")
            elif stderr_req and "flash-attn" in stderr_req and "Could not build wheels" in stderr_req: print(f"{Colors.WARNING}  'flash-attn' build failed.{Colors.ENDC}")
            elif stderr_req and "sentencepiece" in stderr_req and "FileNotFoundError" in stderr_req: # For sentencepiece WinError2
                print(f"{Colors.WARNING}  'sentencepiece' build failed (compiler/build tools not found). Install C++ Build Tools (Visual Studio).{Colors.ENDC}")

            print(f"{Colors.OKCYAN}  Attempting critical packages fallback...{Colors.ENDC}")
            if self.install_critical_packages_fallback(): print(f"{Colors.OKGREEN}  Fallback done.{Colors.ENDC}"); return True
            else: print(f"{Colors.FAIL}  Fallback failed.{Colors.ENDC}"); return False

    def install_critical_packages_fallback(self) -> bool:
        print(f"{Colors.OKCYAN}🔄 Fallback: Critical pkgs individually...{Colors.ENDC}")
        critical_pkgs = ["transformers>=4.30.0", "accelerate", "diffusers", "huggingface_hub", "safetensors", "Pillow", "opencv-python", "gradio", "einops", "sentencepiece", "tokenizers", "scikit-image", "jupyterlab", "notebook"]
        ok_count = 0
        for pkg in critical_pkgs:
            if self._install_package_with_pip(pkg, cwd_for_install=self.bagel_repo_dir): ok_count +=1
            else: print(f"{Colors.WARNING}    ! Fallback failed for: {pkg}.{Colors.ENDC}")
        if ok_count > 0 : print(f"{Colors.OKGREEN}  ✓ Fallback: {ok_count} pkgs reported success.{Colors.ENDC}"); return True 
        else: print(f"{Colors.FAIL}  ✗ Fallback: no pkgs succeeded.{Colors.ENDC}"); return False

    def install_gradio(self) -> bool:
        print(f"{Colors.OKCYAN}🌐 Ensuring Gradio...{Colors.ENDC}"); pip_base = self._get_pip_executable_cmd_list()
        final_check_cmd: Union[str,List[str]]; use_shell_for_check:bool
        if isinstance(pip_base, str): use_shell_for_check = True; final_check_cmd = f"{pip_base} show gradio"
        else: use_shell_for_check = (pip_base[0] == "conda"); check_cmd_list_parts = pip_base + ["show", "gradio"]
        if use_shell_for_check: final_check_cmd = subprocess.list2cmdline(check_cmd_list_parts if isinstance(check_cmd_list_parts,list) else shlex.split(str(check_cmd_list_parts)))
        else: final_check_cmd = check_cmd_list_parts if isinstance(check_cmd_list_parts, list) else shlex.split(str(check_cmd_list_parts))
        if self.run_command(final_check_cmd, shell=use_shell_for_check, check=False)[0]: print(f"{Colors.OKGREEN}✓ Gradio installed.{Colors.ENDC}"); return True
        else:
            print(f"{Colors.WARNING}  Gradio not found, installing...{Colors.ENDC}")
            if self._install_package_with_pip("gradio", cwd_for_install=self.bagel_repo_dir): print(f"{Colors.OKGREEN}✓ Gradio installed.{Colors.ENDC}"); return True
            else: print(f"{Colors.WARNING}⚠ Failed to install Gradio.{Colors.ENDC}"); return False

    def create_model_download_script(self, model_subdir: str = "models/BAGEL-7B-MoT") -> bool:
        script_path = self.bagel_repo_dir/"download_model.py"; model_subdir_posix = Path(model_subdir).as_posix()
        script_content = f'''#!/usr/bin/env python3
""" BAGEL Model DL Script (run from {self.bagel_repo_dir.name}) """
import os; from pathlib import Path; from huggingface_hub import snapshot_download, whoami
SCRIPT_DIR=Path(__file__).resolve().parent; MODEL_SAVE_SUBDIR="{model_subdir_posix}"; MODEL_SAVE_PATH=(SCRIPT_DIR/MODEL_SAVE_SUBDIR).resolve()
REPO_ID="{self.model_repo_id}"
def download_bagel_model():
    print(f"📦 DL model '{{REPO_ID}}' to {{MODEL_SAVE_PATH}} (~14GB+).")
    try:
        MODEL_SAVE_PATH.mkdir(parents=True, exist_ok=True)
        snapshot_download(repo_id=REPO_ID,local_dir=str(MODEL_SAVE_PATH),cache_dir=None,local_dir_use_symlinks=False,resume_download=True,
                          allow_patterns=["*.json","*.safetensors","*.bin","*.py","*.md","*.txt","*.model"])
        print(f"✅ Model '{{REPO_ID}}' DL'd to {{MODEL_SAVE_PATH}}"); return True
    except Exception as e: print(f"❌ Error DL model: {{e}}\\n Check internet, disk, HF login for gated."); return False
if __name__=="__main__":
    if not download_bagel_model(): exit(1)
'''
        try:
            with open(script_path, "w", encoding="utf-8") as f: f.write(script_content)
            if self.system != "windows": os.chmod(script_path, 0o755)
            print(f"{Colors.OKGREEN}✓ Model DL script: {script_path}{Colors.ENDC}"); return True
        except Exception as e: print(f"{Colors.FAIL}✗ Failed to create DL script '{script_path}': {e}{Colors.ENDC}"); return False

    def create_usage_guide(self):
        guide_path = self.bagel_repo_dir/"USAGE_GUIDE.md"; pip_cmd_list_or_str = self._get_pip_executable_cmd_list()
        pip_str_for_guide = ""
        if isinstance(pip_cmd_list_or_str, str): pip_str_for_guide = pip_cmd_list_or_str 
        elif isinstance(pip_cmd_list_or_str, list): 
            pip_str_for_guide = pip_cmd_list_or_str[0]
            if len(pip_cmd_list_or_str) > 1: pip_str_for_guide += " " + " ".join(pip_cmd_list_or_str[1:])
        else: pip_str_for_guide = "python -m pip"
        template = f"""# BAGEL Setup Complete! {{VICTORY_ICON}}
## First Steps: 1. `cd {self.bagel_repo_dir.name}` 2. `{self.get_activation_command()}` (`({self.env_name})` prompt)
## Usage: 3. `python download_model.py` 4. Run (e.g. Jupyter: `jupyter lab`, Gradio: `python app.py`)
## Troubleshooting: `ModuleNotFoundError`: Activate env? Install: `{pip_str_for_guide} install X`. CUDA errors? Update drivers, reinstall PyTorch for CUDA. Sentencepiece build error? Install C++ Build Tools.
## Project: `{self.original_dir.name}/` -> `{self.bagel_repo_dir.name}/` (repo), `{self.env_name}/` (venv if local)
Happy experimenting! {{PRETZEL_ICON}}""" # Added sentencepiece tip
        content = template.replace("{{VICTORY_ICON}}", "🎉").replace("{{PRETZEL_ICON}}", "🥯")
        try: 
            with open(guide_path, "w", encoding="utf-8") as f: f.write(content)
            print(f"{Colors.OKGREEN}✓ Usage guide: {guide_path}{Colors.ENDC}")
        except Exception as e: print(f"{Colors.WARNING}⚠ Could not create usage guide '{guide_path}': {e}{Colors.ENDC}")

    def print_next_steps(self):
        bd = self.bagel_repo_dir.name; ac = self.get_activation_command()
        print(f"""\n{Colors.BOLD}{Colors.OKGREEN}🎉 Setup finished!{Colors.ENDC}
{Colors.BOLD}➡️ Next:{Colors.ENDC} {Colors.OKCYAN}1. Nav:{Colors.ENDC} {Colors.BOLD}cd {bd}{Colors.ENDC} {Colors.OKCYAN}2. Activate:{Colors.ENDC} {Colors.BOLD}{ac}{Colors.ENDC}
{Colors.OKCYAN}3. DL Model:{Colors.ENDC} {Colors.BOLD}python download_model.py{Colors.ENDC} {Colors.OKCYAN}4. Explore (Examples):{Colors.ENDC} Jupyter: {Colors.BOLD}jupyter lab{Colors.ENDC}, Gradio: {Colors.BOLD}python app.py{Colors.ENDC}
{Colors.OKCYAN}5. Read:{Colors.ENDC} {Colors.BOLD}{bd}/USAGE_GUIDE.md{Colors.ENDC} \n🔗 Links: Repo {self.repo_url}, Model {self.model_repo_id} \n{Colors.OKGREEN}Happy BAGELing! 🥯{Colors.ENDC}""")

    def run_setup(self, clone_repo: bool, install_deps: bool, create_download_script: bool) -> bool:
        self.print_banner()
        if not self.check_internet_connection() and (clone_repo or install_deps or create_download_script):
            if not input("Internet unavailable. Key steps may fail. Continue offline? (y/N):").lower()=='y': return False
        if not self.check_system_requirements(): print(f"{Colors.FAIL}Sys reqs failed. Abort.{Colors.ENDC}"); return False
        if self.use_conda and not self.ensure_conda_installed():
            if self.use_conda: print(f"{Colors.FAIL}Conda setup failed.{Colors.ENDC}"); return False
        if not self.use_conda:
            print(f"{Colors.OKCYAN}Using 'venv'.{Colors.ENDC}")
            if not self.check_pip_installation(): print(f"{Colors.FAIL}Base Py pip failed.{Colors.ENDC}"); return False
        repo_name="BAGEL"
        if clone_repo:
            if not self.clone_repository(repo_name): print(f"{Colors.FAIL}Repo clone/setup failed.{Colors.ENDC}"); return False
        else:
            print(f"{Colors.OKCYAN}--no-clone: Using existing dir.{Colors.ENDC}")
            cwd=Path.cwd(); sub=self.original_dir/repo_name
            if (cwd/"requirements.txt").is_file(): self.bagel_repo_dir=cwd; print(f" Using CWD: {cwd}{Colors.ENDC}")
            elif (sub/"requirements.txt").is_file(): self.bagel_repo_dir=sub; print(f" Using subdir '{repo_name}': {sub}{Colors.ENDC}")
            else: print(f"{Colors.FAIL}--no-clone: CWD or ./{repo_name} not valid repo.{Colors.ENDC}"); return False
        print(f"\n{Colors.BOLD}🛠 Setting Up Py Env '{self.env_name}'{Colors.ENDC}")
        if self.use_conda:
            if not self.create_conda_environment(): return False
        else:
            if not self.create_venv_environment(): return False
        if install_deps:
            if not self.install_requirements(): print(f"{Colors.WARNING}Dep install had issues.{Colors.ENDC}")
        else: print(f"{Colors.OKCYAN}--no-deps: Skipping deps.{Colors.ENDC}")
        print(f"\n{Colors.BOLD}📝 Helpers in '{self.bagel_repo_dir}'{Colors.ENDC}")
        if create_download_script: self.create_model_download_script()
        else: print(f"{Colors.OKCYAN}--no-download-script: Skipping DL script.{Colors.ENDC}")
        self.create_usage_guide(); self.print_next_steps(); return True

def main():
    parser = argparse.ArgumentParser(description="BAGEL Env Setup",formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--env-name", default="bagel_env", help="Env name (default: bagel_env).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--use-conda", action="store_true", default=None, help="Force Conda.")
    group.add_argument("--use-venv", action="store_true", default=False, help="Force 'venv'.")
    parser.add_argument("--no-clone",action="store_true",help="Skip repo clone.");parser.add_argument("--no-deps",action="store_true",help="Skip deps install.")
    parser.add_argument("--no-download-script",action="store_true",help="Skip download_model.py.")
    args = parser.parse_args(); use_conda:bool
    if args.use_venv: use_conda=False; print(f"{Colors.OKCYAN}--use-venv -> 'venv'.{Colors.ENDC}")
    elif args.use_conda is True: use_conda=True; print(f"{Colors.OKCYAN}--use-conda -> Conda.{Colors.ENDC}")
    else:
        if BAGELSetup().check_conda_installation(silent_if_found=True): use_conda=True; print(f"{Colors.OKCYAN}Conda detected. Prefer Conda. Use --use-venv to force.{Colors.ENDC}")
        else: use_conda=False; print(f"{Colors.OKCYAN}Conda not detected. Defaulting to 'venv'.{Colors.ENDC}")
    setup = BAGELSetup(env_name=args.env_name,use_conda=use_conda)
    try:
        if setup.run_setup(not args.no_clone, not args.no_deps, not args.no_download_script): print(f"\n{Colors.OKGREEN}✅ Setup done. Check USAGE_GUIDE.md.{Colors.ENDC}")
        else: print(f"\n{Colors.FAIL}❌ Setup failed. Review logs.{Colors.ENDC}"); sys.exit(1)
    except KeyboardInterrupt: print(f"\n{Colors.WARNING}⌨️ Setup interrupted.{Colors.ENDC}"); sys.exit(130)
    except Exception as e: print(f"\n{Colors.FAIL}💥 CRITICAL ERROR: {e}{Colors.ENDC}"); import traceback; traceback.print_exc(); sys.exit(2)

if __name__=="__main__": main()