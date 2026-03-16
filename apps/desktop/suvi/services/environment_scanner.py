"""
SUVI Environment Awareness System
===================================
Scans the user's PC to discover installed applications, capabilities,
default browser, OS version, and running processes. This context is
injected into the Computer Use model's system prompt so it never
tries to open apps that don't exist.

Features:
  - Registry-based app scanning (Windows)
  - Start Menu / PATH scanning for portable apps
  - Capability mapping (apps → categories like "browsers", "music_players")
  - Adaptive: re-scans on startup and on-demand ("refresh environment")
  - Caches results to ~/.suvi/environment.json for fast startup
  - Running process snapshot for real-time awareness

Author: SUVI Project
"""

import json
import os
import sys
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


APP_CAPABILITY_MAP: Dict[str, List[str]] = {
    # ── Browsers ──
    "google chrome": ["browser"],
    "chrome": ["browser"],
    "mozilla firefox": ["browser"],
    "firefox": ["browser"],
    "microsoft edge": ["browser"],
    "opera": ["browser"],
    "opera gx": ["browser"],
    "brave": ["browser"],
    "vivaldi": ["browser"],
    "arc": ["browser"],
    
    # ── Music Players ──
    "spotify": ["music_player", "podcast_player"],
    "itunes": ["music_player"],
    "amazon music": ["music_player"],
    "musicbee": ["music_player"],
    "foobar2000": ["music_player"],
    "winamp": ["music_player"],
    "aimp": ["music_player"],
    
    # ── Video Players ──
    "vlc media player": ["video_player", "music_player"],
    "vlc": ["video_player", "music_player"],
    "mpv": ["video_player"],
    "potplayer": ["video_player"],
    "kmplayer": ["video_player"],
    "windows media player": ["video_player", "music_player"],
    "media player": ["video_player", "music_player"],
    "films & tv": ["video_player"],
    "movies & tv": ["video_player"],
    
    # ── Communication ──
    "discord": ["communication", "voice_chat"],
    "slack": ["communication"],
    "microsoft teams": ["communication", "video_call"],
    "zoom": ["video_call"],
    "telegram desktop": ["communication"],
    "whatsapp": ["communication"],
    "skype": ["communication", "video_call"],
    
    # ── IDEs / Code Editors ──
    "visual studio code": ["code_editor"],
    "vs code": ["code_editor"],
    "pycharm": ["code_editor"],
    "intellij idea": ["code_editor"],
    "sublime text": ["code_editor", "text_editor"],
    "atom": ["code_editor"],
    "notepad++": ["text_editor", "code_editor"],
    "cursor": ["code_editor"],
    
    # ── Office / Productivity ──
    "microsoft word": ["document_editor"],
    "word": ["document_editor"],
    "microsoft excel": ["spreadsheet"],
    "excel": ["spreadsheet"],
    "microsoft powerpoint": ["presentation"],
    "powerpoint": ["presentation"],
    "libreoffice": ["document_editor", "spreadsheet", "presentation"],
    "google docs": ["document_editor"],
    "notion": ["note_taking", "productivity"],
    "obsidian": ["note_taking"],
    "onenote": ["note_taking"],
    "evernote": ["note_taking"],
    
    # ── File Management ──
    "7-zip": ["file_archiver"],
    "winrar": ["file_archiver"],
    "everything": ["file_search"],
    
    # ── Graphics / Design ──
    "adobe photoshop": ["image_editor"],
    "gimp": ["image_editor"],
    "paint.net": ["image_editor"],
    "figma": ["design_tool"],
    "canva": ["design_tool"],
    "adobe illustrator": ["vector_editor"],
    "inkscape": ["vector_editor"],
    "blender": ["3d_modeling", "video_editor"],
    
    # ── Video Editing ──
    "adobe premiere pro": ["video_editor"],
    "davinci resolve": ["video_editor"],
    "capcut": ["video_editor"],
    "obs studio": ["screen_recorder", "streaming"],
    "clipchamp": ["video_editor"],
    
    # ── Terminal / Shell ──
    "windows terminal": ["terminal"],
    "powershell": ["terminal"],
    "git bash": ["terminal"],
    "cmd": ["terminal"],
    "hyper": ["terminal"],
    
    # ── System Utilities ──
    "task manager": ["system_monitor"],
    "calculator": ["calculator"],
    "notepad": ["text_editor"],
    "paint": ["image_editor"],
    "snipping tool": ["screenshot"],
    "screen sketch": ["screenshot"],
    
    # ── Gaming ──
    "steam": ["gaming_platform"],
    "epic games launcher": ["gaming_platform"],
    "riot client": ["gaming_platform"],
    
    # ── Cloud Storage ──
    "google drive": ["cloud_storage"],
    "onedrive": ["cloud_storage"],
    "dropbox": ["cloud_storage"],
}

# ═══════════════════════════════════════════════════════════════════
# ENVIRONMENT DATA DIRECTORY
# ═══════════════════════════════════════════════════════════════════
SUVI_DATA_DIR = Path.home() / ".suvi"
ENVIRONMENT_CACHE_PATH = SUVI_DATA_DIR / "environment.json"


class EnvironmentScanner:
    """
    Scans the user's system to build a capability-aware environment profile.
    
    Usage:
        scanner = EnvironmentScanner()
        env = scanner.scan()           # Full scan
        context = scanner.get_context_for_ai()   # AI-ready context string
    """

    def __init__(self):
        self._env_data: Optional[Dict] = None
        self._last_scan_time: float = 0
        self._scan_interval = 300  # Re-scan every 5 minutes max
        
        SUVI_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════
    
    def scan(self, force: bool = False) -> Dict:
        """
        Perform a full environment scan (or return cached if recent).
        
        Args:
            force: If True, always re-scan even if cache is fresh.
            
        Returns:
            Dict with all environment data.
        """
       
        if not force and self._env_data and (time.time() - self._last_scan_time) < self._scan_interval:
            return self._env_data
        
        
        if not force and ENVIRONMENT_CACHE_PATH.exists():
            try:
                cached = json.loads(ENVIRONMENT_CACHE_PATH.read_text(encoding="utf-8"))
                cache_age = time.time() - cached.get("scan_timestamp", 0)
                
                if cache_age < 3600:
                    self._env_data = cached
                    self._last_scan_time = cached.get("scan_timestamp", time.time())
                    print(f"📋 [EnvScanner] Loaded cached environment ({len(cached.get('installed_apps', []))} apps, {int(cache_age)}s old)")
                    return self._env_data
            except Exception as e:
                print(f"⚠️ [EnvScanner] Cache read failed: {e}")

        
        print("🔍 [EnvScanner] Scanning system environment...")
        start = time.time()
        
        env_data = {
            "scan_timestamp": time.time(),
            "os": self._get_os_info(),
            "default_browser": self._get_default_browser(),
            "installed_apps": [],
            "capabilities": {},
            "running_processes": [],
        }
        
        # Scan installed applications
        raw_apps = self._scan_installed_apps()
        env_data["installed_apps"] = sorted(raw_apps)
        
        # Build capability map
        env_data["capabilities"] = self._build_capability_map(raw_apps)
        
        # Snapshot running processes
        env_data["running_processes"] = self._get_running_processes()
        
        # Cache results
        self._env_data = env_data
        self._last_scan_time = time.time()
        self._save_cache(env_data)
        
        elapsed = time.time() - start
        print(f"✅ [EnvScanner] Scan complete in {elapsed:.1f}s — {len(raw_apps)} apps, {sum(len(v) for v in env_data['capabilities'].values())} capabilities")
        
        return env_data
    
    def refresh(self) -> Dict:
        """Force a full re-scan. Called when user says 'refresh environment'."""
        return self.scan(force=True)
    
    def get_installed_apps(self) -> List[str]:
        """Returns list of installed application names."""
        env = self.scan()
        return env.get("installed_apps", [])
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """Returns capability → [app names] mapping."""
        env = self.scan()
        return env.get("capabilities", {})
    
    def is_app_installed(self, app_name: str) -> bool:
        """Check if a specific app is installed (fuzzy match)."""
        env = self.scan()
        apps_lower = [a.lower() for a in env.get("installed_apps", [])]
        return app_name.lower() in apps_lower or any(app_name.lower() in a for a in apps_lower)
    
    def get_app_for_capability(self, capability: str) -> Optional[str]:
        """
        Get the best app for a given capability.
        Returns the first available app, or None.
        
        Example: get_app_for_capability("music_player") → "Spotify"
        """
        env = self.scan()
        caps = env.get("capabilities", {})
        apps = caps.get(capability, [])
        return apps[0] if apps else None
    
    def get_running_processes(self) -> List[str]:
        """Get currently running process names (refreshed each call)."""
        return self._get_running_processes()
    
    def get_context_for_ai(self) -> str:
        """
        Generate a concise environment context string for injection
        into the Computer Use model's system prompt.
        
        This is the KEY method — it tells the AI exactly what's available.
        """
        env = self.scan()
        
        lines = ["SYSTEM ENVIRONMENT:"]
        lines.append(f"OS: {env.get('os', 'Unknown')}")
        lines.append(f"Default Browser: {env.get('default_browser', 'Unknown')}")
        lines.append("")
        
        
        caps = env.get("capabilities", {})
        if caps:
            lines.append("AVAILABLE CAPABILITIES:")
            
            priority_caps = [
                "browser", "music_player", "video_player", "communication",
                "code_editor", "text_editor", "document_editor", "terminal",
                "file_archiver", "image_editor", "video_editor", "screenshot",
            ]
            for cap in priority_caps:
                if cap in caps:
                    apps_str = ", ".join(caps[cap])
                    lines.append(f"  {cap}: {apps_str}")
            
           
            for cap, apps in sorted(caps.items()):
                if cap not in priority_caps:
                    apps_str = ", ".join(apps)
                    lines.append(f"  {cap}: {apps_str}")
        
        lines.append("")
        lines.append("RULES:")
        lines.append("- ONLY use applications that are listed above.")
        lines.append("- If the user asks for an app NOT installed, use the best alternative.")
        lines.append(f"- For web tasks, ALWAYS use the default browser: {env.get('default_browser', 'Chrome')}.")
        lines.append("- For 'play music/video on YouTube', use the browser → youtube.com, NOT a YouTube app.")
        lines.append("- For 'play music', prefer installed music_player apps (e.g., Spotify) before browser.")
        
        return "\n".join(lines)
    
    # ═══════════════════════════════════════════════════════════════
    # PLATFORM-SPECIFIC SCANNING
    # ═══════════════════════════════════════════════════════════════
    
    def _scan_installed_apps(self) -> List[str]:
        """Detect installed applications based on the OS."""
        if sys.platform == "win32":
            return self._scan_windows_apps()
        elif sys.platform == "darwin":
            return self._scan_macos_apps()
        else:
            return self._scan_linux_apps()
    
    def _scan_windows_apps(self) -> List[str]:
        """
        Scan Windows for installed applications using:
        1. Registry (Uninstall keys)
        2. Start Menu shortcuts
        3. Known default apps
        """
        apps: Set[str] = set()
        
        # ── Source 1: Windows Registry ──
        try:
            import winreg
            
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            
            for hive, path in registry_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if name and len(name) > 1:
                                
                                    skip_keywords = [
                                        "update", "driver", "redistributable", "runtime",
                                        "sdk", ".net", "visual c++", "hotfix", "kb",
                                        "security", "windows", "microsoft visual",
                                        "vulkan", "physx"
                                    ]
                                    name_lower = name.lower()
                                    if not any(kw in name_lower for kw in skip_keywords):
                                        apps.add(name.strip())
                            except FileNotFoundError:
                                pass
                            finally:
                                winreg.CloseKey(subkey)
                        except (OSError, WindowsError):
                            continue
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    continue
        except ImportError:
            print("⚠️ [EnvScanner] winreg not available (not Windows?)")
        
        # ── Source 2: Start Menu Shortcuts ──
        start_menu_paths = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        
        for menu_path in start_menu_paths:
            if os.path.exists(menu_path):
                for root, dirs, files in os.walk(menu_path):
                    for f in files:
                        if f.endswith(".lnk"):
                            name = f.replace(".lnk", "").strip()
                            if not any(kw in name.lower() for kw in ["uninstall", "readme", "help", "license", "website"]):
                                apps.add(name)
        
        # ── Source 3: Built-in Windows Apps ──
        builtin_apps = [
            "Notepad", "Calculator", "Paint", "Snipping Tool",
            "Windows Terminal", "File Explorer", "Task Manager",
            "Microsoft Edge", "Media Player",
        ]
        for app in builtin_apps:
            apps.add(app)
        
        # ── Source 4: Check PATH for common CLI tools ──
        path_apps = {
            "code": "Visual Studio Code",
            "git": "Git",
            "python": "Python",
            "node": "Node.js",
            "npm": "Node.js",
        }
        for cmd, display_name in path_apps.items():
            if self._is_in_path(cmd):
                apps.add(display_name)
        
        return sorted(apps)
    
    def _scan_macos_apps(self) -> List[str]:
        """Scan macOS /Applications directory."""
        apps = set()
        app_dirs = ["/Applications", os.path.expanduser("~/Applications")]
        
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                for item in os.listdir(app_dir):
                    if item.endswith(".app"):
                        apps.add(item.replace(".app", ""))
        
        return sorted(apps)
    
    def _scan_linux_apps(self) -> List[str]:
        """Scan Linux .desktop files."""
        apps = set()
        desktop_dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
        ]
        
        for desktop_dir in desktop_dirs:
            if os.path.exists(desktop_dir):
                for f in os.listdir(desktop_dir):
                    if f.endswith(".desktop"):
                        try:
                            filepath = os.path.join(desktop_dir, f)
                            with open(filepath, "r") as df:
                                for line in df:
                                    if line.startswith("Name="):
                                        apps.add(line.split("=", 1)[1].strip())
                                        break
                        except Exception:
                            continue
        
        return sorted(apps)
    
    # ═══════════════════════════════════════════════════════════════
    # CAPABILITY MAPPING
    # ═══════════════════════════════════════════════════════════════
    
    def _build_capability_map(self, installed_apps: List[str]) -> Dict[str, List[str]]:
        """
        Maps installed apps to capability categories.
        
        Input: ["Google Chrome", "Spotify", "VLC Media Player"]
        
        Output: {
            "browser": ["Google Chrome"],
            "music_player": ["Spotify", "VLC Media Player"],
            "video_player": ["VLC Media Player"]
        }
        """
        import re
        capabilities: Dict[str, List[str]] = {}
        
        for app in installed_apps:
            app_lower = app.lower()
            
            
            matched_caps = []
            
            if app_lower in APP_CAPABILITY_MAP:
                matched_caps = APP_CAPABILITY_MAP[app_lower]
            else:
                
                for known_app, caps in APP_CAPABILITY_MAP.items():
                    
                    if app_lower.startswith(known_app) or known_app.startswith(app_lower):
                        matched_caps = caps
                        break
                    
                    if len(known_app) >= 4:  
                        pattern = r'(?:^|\b)' + re.escape(known_app) + r'(?:\b|$)'
                        if re.search(pattern, app_lower) and app_lower.startswith(known_app.split()[0]):
                            matched_caps = caps
                            break
            
            for cap in matched_caps:
                if cap not in capabilities:
                    capabilities[cap] = []
                if app not in capabilities[cap]:
                    capabilities[cap].append(app)
        
        
        for cap in capabilities:
            apps = capabilities[cap]
            if len(apps) > 1:
                deduped = []
                for app in sorted(apps, key=len):
                    is_variant = False
                    for existing in deduped:
                        
                        shorter = existing.lower() if len(existing) < len(app) else app.lower()
                        longer = app.lower() if len(existing) < len(app) else existing.lower()
                        if longer.startswith(shorter):
                            is_variant = True
                            break
                    if not is_variant:
                        deduped.append(app)
                capabilities[cap] = deduped
        
        return capabilities
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM INFO HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _get_os_info(self) -> str:
        """Get a human-readable OS string."""
        if sys.platform == "win32":
            ver = platform.version()
            release = platform.release()
            return f"Windows {release} (Build {ver})"
        elif sys.platform == "darwin":
            ver = platform.mac_ver()[0]
            return f"macOS {ver}"
        else:
            try:
                import distro
                return f"{distro.name()} {distro.version()}"
            except ImportError:
                return f"Linux {platform.release()}"
    
    def _get_default_browser(self) -> str:
        """Detect the system's default web browser."""
        if sys.platform == "win32":
            try:
                import winreg
                
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice"
                )
                prog_id = winreg.QueryValueEx(key, "ProgId")[0]
                winreg.CloseKey(key)
                
                browser_map = {
                    "ChromeHTML": "Google Chrome",
                    "MSEdgeHTM": "Microsoft Edge",
                    "FirefoxURL": "Mozilla Firefox",
                    "BraveHTML": "Brave",
                    "OperaStable": "Opera",
                    "VivaldiHTM": "Vivaldi",
                }
                
                for key_part, name in browser_map.items():
                    if key_part.lower() in prog_id.lower():
                        return name
                
                return prog_id  
            except Exception:
                return "Microsoft Edge"  
        
        elif sys.platform == "darwin":
            try:
                result = subprocess.run(
                    ["defaults", "read", "com.apple.LaunchServices/com.apple.launchservices.secure", "LSHandlers"],
                    capture_output=True, text=True
                )
                if "chrome" in result.stdout.lower():
                    return "Google Chrome"
                elif "firefox" in result.stdout.lower():
                    return "Mozilla Firefox"
                return "Safari"
            except Exception:
                return "Safari"
        
        else:
            try:
                result = subprocess.run(["xdg-settings", "get", "default-web-browser"],
                                       capture_output=True, text=True)
                browser = result.stdout.strip()
                if "chrome" in browser.lower():
                    return "Google Chrome"
                elif "firefox" in browser.lower():
                    return "Mozilla Firefox"
                return browser
            except Exception:
                return "Unknown"
    
    def _get_running_processes(self) -> List[str]:
        """Get a list of unique running process names."""
        processes = set()
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.strip().split("\n"):
                    if line:
                        
                        name = line.split(",")[0].strip('"').replace(".exe", "")
                        if name and len(name) > 2:
                            processes.add(name)
            else:
                result = subprocess.run(
                    ["ps", "-eo", "comm", "--no-headers"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.strip().split("\n"):
                    name = line.strip()
                    if name and len(name) > 2:
                        processes.add(name)
        except Exception as e:
            print(f"⚠️ [EnvScanner] Process scan failed: {e}")
        
        return sorted(processes)
    
    def _is_in_path(self, cmd: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["where", cmd], capture_output=True, text=True, timeout=3
                )
            else:
                result = subprocess.run(
                    ["which", cmd], capture_output=True, text=True, timeout=3
                )
            return result.returncode == 0
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # CACHE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def _save_cache(self, env_data: Dict):
        """Save environment data to disk."""
        try:
            ENVIRONMENT_CACHE_PATH.write_text(
                json.dumps(env_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"💾 [EnvScanner] Cache saved to {ENVIRONMENT_CACHE_PATH}")
        except Exception as e:
            print(f"⚠️ [EnvScanner] Failed to save cache: {e}")
    
    def clear_cache(self):
        """Delete the cached environment data."""
        try:
            if ENVIRONMENT_CACHE_PATH.exists():
                ENVIRONMENT_CACHE_PATH.unlink()
                print("🗑️ [EnvScanner] Cache cleared.")
        except Exception as e:
            print(f"⚠️ [EnvScanner] Failed to clear cache: {e}")
        self._env_data = None
        self._last_scan_time = 0


# ═══════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    scanner = EnvironmentScanner()
    env = scanner.scan(force=True)
    
    print("\n" + "=" * 60)
    print("SUVI ENVIRONMENT SCAN RESULTS")
    print("=" * 60)
    
    print(f"\nOS: {env['os']}")
    print(f"Default Browser: {env['default_browser']}")
    
    print(f"\n📦 Installed Apps ({len(env['installed_apps'])}):")
    for app in env['installed_apps']:
        print(f"  - {app}")
    
    print("\n🧠 Capabilities:")
    for cap, apps in sorted(env['capabilities'].items()):
        print(f"  {cap}: {', '.join(apps)}")
    
    print(f"\n🔄 Running Processes ({len(env['running_processes'])}):")
    for proc in env['running_processes'][:20]:
        print(f"  - {proc}")
    
    print("\n" + "=" * 60)
    print("AI CONTEXT STRING:")
    print("=" * 60)
    print(scanner.get_context_for_ai())
