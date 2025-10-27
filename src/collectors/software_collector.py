"""
Software Collector Module

This module collects information about installed software on the system.
Supports Windows, Linux, and macOS platforms.
"""

import platform
import subprocess
import logging
from typing import Dict, Any, List
from datetime import datetime
from .base_collector import BaseCollector


class SoftwareCollector(BaseCollector):
    """
    Collector for installed software information.

    Collects data about:
    - Installed applications
    - Application versions
    - Publishers/Vendors
    - Installation dates
    - Install locations
    """

    def __init__(self):
        """Initialize the software collector."""
        super().__init__()
        self.system = platform.system()
        self.logger.info(f"Initialized SoftwareCollector for {self.system}")

    def collect(self) -> Dict[str, Any]:
        """
        Collect installed software information.

        Returns:
            Dict containing installed software information
        """
        self.logger.info("Starting software collection")

        info = {
            'installed_software': [],
            'total_installed': 0,
            'collection_timestamp': datetime.now().isoformat(),
            'platform': self.system
        }

        try:
            if self.system == "Windows":
                software_list = self.get_windows_software()
            elif self.system == "Linux":
                software_list = self.get_linux_software()
            elif self.system == "Darwin":
                software_list = self.get_macos_software()
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                software_list = []

            info['installed_software'] = software_list
            info['total_installed'] = len(software_list)

            self.logger.info(f"Collected {info['total_installed']} software entries")

        except Exception as e:
            self.logger.error(f"Error collecting software information: {e}")
            info['error'] = str(e)

        return info

    def get_windows_software(self) -> List[Dict[str, Any]]:
        """
        Get installed software on Windows.

        Uses WMI and PowerShell to query installed programs from:
        - Registry (Uninstall keys)
        - Win32_Product (slower but more comprehensive)

        Returns:
            List of dictionaries containing software information
        """
        software_list = []

        try:
            # Method 1: Using PowerShell to query registry (faster)
            self.logger.info("Querying Windows Registry for installed software")

            # PowerShell command to get installed software from registry
            ps_command = """
            Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate, InstallLocation, EstimatedSize |
            Where-Object {$_.DisplayName -ne $null} |
            ConvertTo-Json
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                import json
                try:
                    software_data = json.loads(result.stdout)

                    # Handle single item (not a list)
                    if isinstance(software_data, dict):
                        software_data = [software_data]

                    for item in software_data:
                        if item.get('DisplayName'):
                            software_list.append({
                                'name': item.get('DisplayName', 'Unknown'),
                                'version': item.get('DisplayVersion', 'Unknown'),
                                'publisher': item.get('Publisher', 'Unknown'),
                                'install_date': item.get('InstallDate', 'Unknown'),
                                'install_location': item.get('InstallLocation', 'Unknown'),
                                'size_kb': item.get('EstimatedSize', 0)
                            })

                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing PowerShell JSON output: {e}")

            # Also check 32-bit registry on 64-bit systems
            ps_command_32 = """
            Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate, InstallLocation, EstimatedSize |
            Where-Object {$_.DisplayName -ne $null} |
            ConvertTo-Json
            """

            result_32 = subprocess.run(
                ["powershell", "-Command", ps_command_32],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result_32.returncode == 0 and result_32.stdout:
                import json
                try:
                    software_data_32 = json.loads(result_32.stdout)

                    if isinstance(software_data_32, dict):
                        software_data_32 = [software_data_32]

                    for item in software_data_32:
                        if item.get('DisplayName'):
                            # Avoid duplicates
                            if not any(s['name'] == item.get('DisplayName') for s in software_list):
                                software_list.append({
                                    'name': item.get('DisplayName', 'Unknown'),
                                    'version': item.get('DisplayVersion', 'Unknown'),
                                    'publisher': item.get('Publisher', 'Unknown'),
                                    'install_date': item.get('InstallDate', 'Unknown'),
                                    'install_location': item.get('InstallLocation', 'Unknown'),
                                    'size_kb': item.get('EstimatedSize', 0)
                                })

                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing 32-bit PowerShell JSON output: {e}")

        except subprocess.TimeoutExpired:
            self.logger.error("PowerShell command timed out")
        except Exception as e:
            self.logger.error(f"Error querying Windows software: {e}")

            # Fallback: Try using wmic (legacy method)
            try:
                self.logger.info("Trying fallback method with WMIC")
                result = subprocess.run(
                    ["wmic", "product", "get", "name,version,vendor"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                software_list.append({
                                    'name': ' '.join(parts[:-2]) if len(parts) > 2 else parts[0],
                                    'version': parts[-2] if len(parts) > 2 else 'Unknown',
                                    'publisher': parts[-1] if len(parts) > 2 else 'Unknown',
                                    'install_date': 'Unknown',
                                    'install_location': 'Unknown',
                                    'size_kb': 0
                                })

            except Exception as fallback_error:
                self.logger.error(f"Fallback method also failed: {fallback_error}")

        return software_list

    def get_linux_software(self) -> List[Dict[str, Any]]:
        """
        Get installed software on Linux.

        Tries multiple package managers:
        - dpkg (Debian/Ubuntu)
        - rpm (RedHat/CentOS/Fedora)
        - pacman (Arch Linux)
        - snap (Universal)
        - flatpak (Universal)

        Returns:
            List of dictionaries containing software information
        """
        software_list = []

        # Try dpkg (Debian/Ubuntu)
        try:
            self.logger.info("Trying dpkg package manager")
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('ii'):  # Installed package
                        parts = line.split()
                        if len(parts) >= 3:
                            software_list.append({
                                'name': parts[1],
                                'version': parts[2],
                                'publisher': 'Unknown',
                                'install_date': 'Unknown',
                                'install_location': 'Unknown',
                                'package_manager': 'dpkg'
                            })

        except FileNotFoundError:
            self.logger.debug("dpkg not found, trying other package managers")
        except Exception as e:
            self.logger.error(f"Error querying dpkg: {e}")

        # Try rpm (RedHat/CentOS/Fedora)
        if not software_list:
            try:
                self.logger.info("Trying rpm package manager")
                result = subprocess.run(
                    ["rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}|%{VENDOR}\n"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            software_list.append({
                                'name': parts[0],
                                'version': parts[1],
                                'publisher': parts[2] if len(parts) > 2 else 'Unknown',
                                'install_date': 'Unknown',
                                'install_location': 'Unknown',
                                'package_manager': 'rpm'
                            })

            except FileNotFoundError:
                self.logger.debug("rpm not found, trying other package managers")
            except Exception as e:
                self.logger.error(f"Error querying rpm: {e}")

        # Try pacman (Arch Linux)
        if not software_list:
            try:
                self.logger.info("Trying pacman package manager")
                result = subprocess.run(
                    ["pacman", "-Q"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            software_list.append({
                                'name': parts[0],
                                'version': parts[1],
                                'publisher': 'Unknown',
                                'install_date': 'Unknown',
                                'install_location': 'Unknown',
                                'package_manager': 'pacman'
                            })

            except FileNotFoundError:
                self.logger.debug("pacman not found")
            except Exception as e:
                self.logger.error(f"Error querying pacman: {e}")

        # Try snap packages (universal)
        try:
            self.logger.info("Checking for snap packages")
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        software_list.append({
                            'name': parts[0],
                            'version': parts[1],
                            'publisher': parts[3] if len(parts) > 3 else 'Unknown',
                            'install_date': 'Unknown',
                            'install_location': 'Unknown',
                            'package_manager': 'snap'
                        })

        except FileNotFoundError:
            self.logger.debug("snap not found")
        except Exception as e:
            self.logger.error(f"Error querying snap: {e}")

        # Try flatpak packages (universal)
        try:
            self.logger.info("Checking for flatpak packages")
            result = subprocess.run(
                ["flatpak", "list", "--app"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        software_list.append({
                            'name': parts[0],
                            'version': parts[2] if len(parts) > 2 else 'Unknown',
                            'publisher': 'Unknown',
                            'install_date': 'Unknown',
                            'install_location': 'Unknown',
                            'package_manager': 'flatpak'
                        })

        except FileNotFoundError:
            self.logger.debug("flatpak not found")
        except Exception as e:
            self.logger.error(f"Error querying flatpak: {e}")

        return software_list

    def get_macos_software(self) -> List[Dict[str, Any]]:
        """
        Get installed software on macOS.

        Queries:
        - Applications folder (/Applications)
        - Homebrew packages
        - Mac App Store apps

        Returns:
            List of dictionaries containing software information
        """
        software_list = []

        # Method 1: Get applications from /Applications folder
        try:
            self.logger.info("Scanning /Applications folder")
            result = subprocess.run(
                ["system_profiler", "SPApplicationsDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                import json
                try:
                    data = json.loads(result.stdout)
                    apps = data.get('SPApplicationsDataType', [])

                    for app in apps:
                        software_list.append({
                            'name': app.get('_name', 'Unknown'),
                            'version': app.get('version', 'Unknown'),
                            'publisher': app.get('obtained_from', 'Unknown'),
                            'install_date': app.get('lastModified', 'Unknown'),
                            'install_location': app.get('path', 'Unknown'),
                            'size_kb': 0
                        })

                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing system_profiler JSON: {e}")

        except subprocess.TimeoutExpired:
            self.logger.error("system_profiler command timed out")
        except Exception as e:
            self.logger.error(f"Error querying macOS applications: {e}")

        # Method 2: Get Homebrew packages
        try:
            self.logger.info("Checking Homebrew packages")
            result = subprocess.run(
                ["brew", "list", "--versions"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        software_list.append({
                            'name': parts[0],
                            'version': parts[1],
                            'publisher': 'Homebrew',
                            'install_date': 'Unknown',
                            'install_location': 'Unknown',
                            'package_manager': 'brew'
                        })

        except FileNotFoundError:
            self.logger.debug("Homebrew not found")
        except Exception as e:
            self.logger.error(f"Error querying Homebrew: {e}")

        return software_list
