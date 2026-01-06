#!/usr/bin/env python3
"""
Python wrapper for Panako audio fingerprinting
Handles all Java configuration and provides clean Python interface
"""

import os
import subprocess
import sys
from pathlib import Path

# Check Python version at import time
if sys.version_info < (3, 7):
    print("Error: Python 3.7 or higher is required", file=sys.stderr)
    print(f"Current version: {sys.version}", file=sys.stderr)
    sys.exit(1)

class Panako:
    # Supported audio formats (when ffmpeg is available)
    AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma']

    def __init__(self, panako_dir=None, skip_validation=False, defer_build=False):
        """
        Initialize Panako wrapper

        Args:
            panako_dir: Path to Panako installation directory
                        If not provided, looks for PANAKO_DIR environment variable
                        or defaults to ~/Panako
            skip_validation: If True, skip dependency validation (for testing)
            defer_build: If True, don't build Java command (for verify command)
        """
        if panako_dir is None:
            panako_dir = os.environ.get('PANAKO_DIR', os.path.expanduser('~/Panako'))
        else:
            # Expand ~ in user-provided paths
            panako_dir = os.path.expanduser(panako_dir)

        self.panako_dir = Path(panako_dir).resolve()  # Resolve to absolute path
        self.jar_path = self.panako_dir / "build/libs"

        # Detect platform
        self.platform = sys.platform  # 'darwin', 'linux', 'win32'

        # Setup environment
        self._setup_environment()

        # Validate dependencies
        if not skip_validation:
            self._validate_dependencies()

        # Build Java command base
        self.java_cmd = None
        if not defer_build:
            self.java_cmd = self._build_java_command()

    def _setup_environment(self):
        """Setup required environment variables"""
        if self.platform == 'darwin':
            # LMDB library path for macOS
            # Try Apple Silicon path first, then Intel
            lib_paths = ['/opt/homebrew/lib', '/usr/local/lib']
            existing_paths = [p for p in lib_paths if os.path.exists(p)]
            if existing_paths:
                current_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
                os.environ['DYLD_LIBRARY_PATH'] = ':'.join(existing_paths) + (':' + current_dyld if current_dyld else '')

            # Ensure JAVA_HOME is set (for Macs with Homebrew Java)
            if 'JAVA_HOME' not in os.environ:
                java_homes = [
                    # Apple Silicon paths
                    '/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home',
                    '/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home',
                    # Intel Mac paths
                    '/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home',
                    '/usr/local/opt/openjdk/libexec/openjdk.jdk/Contents/Home',
                    # System Java
                    '/Library/Java/JavaVirtualMachines',
                ]
                for java_home in java_homes:
                    if os.path.exists(java_home):
                        if java_home.endswith('JavaVirtualMachines'):
                            # Find the actual JDK path
                            try:
                                for item in os.listdir(java_home):
                                    full_path = os.path.join(java_home, item, 'Contents/Home')
                                    if os.path.isdir(full_path):
                                        os.environ['JAVA_HOME'] = full_path
                                        break
                            except PermissionError:
                                continue
                        else:
                            os.environ['JAVA_HOME'] = java_home
                        if 'JAVA_HOME' in os.environ:
                            break

        elif self.platform == 'linux':
            # LMDB library path for Linux
            lib_paths = ['/usr/lib', '/usr/local/lib', '/usr/lib/x86_64-linux-gnu', '/usr/lib/aarch64-linux-gnu']
            existing_paths = [p for p in lib_paths if os.path.exists(p)]
            if existing_paths:
                current_ld = os.environ.get('LD_LIBRARY_PATH', '')
                os.environ['LD_LIBRARY_PATH'] = ':'.join(existing_paths) + (':' + current_ld if current_ld else '')

            # Ensure JAVA_HOME is set for Linux
            if 'JAVA_HOME' not in os.environ:
                java_homes = [
                    '/usr/lib/jvm/java-17-openjdk-amd64',
                    '/usr/lib/jvm/java-17-openjdk-arm64',
                    '/usr/lib/jvm/java-17-openjdk',
                    '/usr/lib/jvm/default-java',
                ]
                for java_home in java_homes:
                    if os.path.exists(java_home):
                        os.environ['JAVA_HOME'] = java_home
                        break

    def _validate_dependencies(self):
        """Validate that all dependencies are available"""
        errors = []
        warnings = []

        # Check Java
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
            # Java outputs version to stderr, so check stderr
            version_output = result.stderr if result.stderr else result.stdout
            if result.returncode != 0:
                errors.append("Java not found or not working properly")
                if self.platform == 'darwin':
                    errors.append("  Install: brew install openjdk@17")
                else:
                    errors.append("  Install: sudo apt install openjdk-17-jdk")
            else:
                # Check Java version
                version_output = result.stdout
                if '17' not in version_output and 'version "17' not in version_output:
                    warnings.append("Java 17 is recommended. Current Java:")
                    warnings.append(f"  {version_output.split()[0] if version_output else 'unknown'}")
        except FileNotFoundError:
            errors.append("Java not found")
            if self.platform == 'darwin':
                errors.append("  Install: brew install openjdk@17")
                errors.append("  Then add to ~/.zshrc:")
                errors.append('  export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"')
            else:
                errors.append("  Install: sudo apt install openjdk-17-jdk")
        except subprocess.TimeoutExpired:
            errors.append("Java command timed out")

        # Check LMDB (platform-specific)
        if self.platform == 'darwin':
            lmdb_paths = ['/opt/homebrew/lib/liblmdb.dylib', '/usr/local/lib/liblmdb.dylib']
            if not any(os.path.exists(p) for p in lmdb_paths):
                errors.append("LMDB library not found")
                errors.append("  Install: brew install lmdb")
        elif self.platform == 'linux':
            lmdb_paths = [
                '/usr/lib/liblmdb.so',
                '/usr/lib/x86_64-linux-gnu/liblmdb.so',
                '/usr/lib/aarch64-linux-gnu/liblmdb.so',
                '/usr/local/lib/liblmdb.so'
            ]
            if not any(os.path.exists(p) for p in lmdb_paths):
                errors.append("LMDB library not found")
                errors.append("  Install: sudo apt install liblmdb-dev")

        # Check ffmpeg (optional but recommended)
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                warnings.append("ffmpeg not found (optional, but recommended for non-WAV formats)")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            warnings.append("ffmpeg not found (optional, enables MP3/FLAC/etc support)")
            if self.platform == 'darwin':
                warnings.append("  Install: brew install ffmpeg")
            else:
                warnings.append("  Install: sudo apt install ffmpeg")

        # Check database directory permissions
        db_path = Path.home() / ".panako"
        if db_path.exists():
            if not os.access(db_path, os.W_OK):
                errors.append(f"No write permission for {db_path}")
                errors.append(f"  Run: chmod u+w {db_path}")

        # Print errors and warnings
        if errors:
            print("\n" + "="*80, file=sys.stderr)
            print("ERROR: Missing required dependencies", file=sys.stderr)
            print("="*80, file=sys.stderr)
            for error in errors:
                print(error, file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)

        if warnings:
            print("\nWarnings:", file=sys.stderr)
            for warning in warnings:
                print(f"  {warning}", file=sys.stderr)
            print()

    def _build_java_command(self):
        """Build the base Java command with all required options"""
        # Find the Panako JAR file
        jar_files = list(self.jar_path.glob("panako-*-all.jar"))
        if not jar_files:
            error_msg = f"""
Panako JAR not found in {self.jar_path}

Possible solutions:
1. Build Panako (requires internet connection for first build):
   cd {self.panako_dir}
   chmod +x gradlew
   ./gradlew shadowJar

2. If Panako is installed elsewhere, set PANAKO_DIR:
   export PANAKO_DIR="{Path.home()}/Panako"

3. Or specify path when creating Panako instance:
   panako = Panako(panako_dir="/path/to/your/Panako")

Current Panako directory: {self.panako_dir}

Note: First build downloads dependencies (~50-100MB) and takes 2-5 minutes.
"""
            raise FileNotFoundError(error_msg)

        jar_file = jar_files[0]

        # Determine library path based on platform
        if self.platform == 'darwin':
            # macOS: try Apple Silicon first, then Intel
            lib_paths = ['/opt/homebrew/lib', '/usr/local/lib']
        else:
            # Linux
            lib_paths = ['/usr/lib', '/usr/local/lib', '/usr/lib/x86_64-linux-gnu', '/usr/lib/aarch64-linux-gnu']

        existing_lib_paths = [p for p in lib_paths if os.path.exists(p)]
        java_library_path = ':'.join(existing_lib_paths) if existing_lib_paths else '/usr/lib'

        # Build Java command with all required flags
        java_opts = [
            'java',
            '--add-opens', 'java.base/java.nio=ALL-UNNAMED',
            '--add-opens', 'java.base/sun.nio.ch=ALL-UNNAMED',
            f'-Djava.library.path={java_library_path}',
            '-jar', str(jar_file)
        ]

        return java_opts

    def _run_command(self, *args, capture_output=False):
        """
        Run Panako command

        Args:
            *args: Command arguments (e.g., 'query', '/path/to/file.wav')
            capture_output: If True, return output; if False, print to console

        Returns:
            subprocess.CompletedProcess or None
        """
        if self.java_cmd is None:
            print("Error: Panako not properly initialized", file=sys.stderr)
            return None

        cmd = self.java_cmd + list(args)

        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result
            else:
                subprocess.run(cmd, check=True)
                return None
        except subprocess.CalledProcessError as e:
            print(f"Error running Panako command: {e}", file=sys.stderr)
            if capture_output and e.stderr:
                print(e.stderr, file=sys.stderr)
            return None
        except FileNotFoundError:
            print(f"Error: Java executable not found. Please install Java 17+", file=sys.stderr)
            return None

    def store(self, path):
        """
        Add audio file(s) to database

        Args:
            path: Path to audio file or directory
        """
        # Expand ~ in paths
        path = Path(os.path.expanduser(str(path))).resolve()

        if path.is_file():
            print(f"Storing: {path.name}")
            self._run_command('store', str(path))
        elif path.is_dir():
            print(f"Storing audio files from: {path}")
            # Find all audio files
            audio_files = []
            for ext in self.AUDIO_EXTENSIONS:
                audio_files.extend(path.rglob(f"*{ext}"))

            if not audio_files:
                print(f"No audio files found in {path}")
                print(f"Supported formats: {', '.join(self.AUDIO_EXTENSIONS)}")
                return

            print(f"Found {len(audio_files)} audio files")

            # Store all files with progress indication
            for i, audio_file in enumerate(sorted(audio_files), 1):
                print(f"  [{i}/{len(audio_files)}] {audio_file.name[:60]}...", end=" ", flush=True)
                result = self._run_command('store', str(audio_file), capture_output=True)
                print("✓" if result else "✗")
        else:
            print(f"Error: {path} not found", file=sys.stderr)

    def list_cache_files(self):
        """
        List files currently in Panako cache (simple, read-only)
        """
        cache_path = Path.home() / ".panako/dbs/olaf_cache"

        print(f"\n{'='*80}")
        print("Panako Database Cache Files")
        print(f"{'='*80}\n")

        if not cache_path.exists():
            print("Cache directory not found. Database might be empty.")
            print("Run 'store' command to add audio files to the database.")
            print(f"\nExpected location: {cache_path}")
            return

        # Get all .tdb cache files
        cache_files = sorted(cache_path.glob("*.tdb"))

        print(f"Total cached fingerprints: {len(cache_files)}")
        print(f"Cache location: {cache_path}\n")

        if cache_files:
            print("Cache file IDs (one per audio file):\n")
            for i, cache_file in enumerate(cache_files, 1):
                # Show file ID and modification time
                mtime = cache_file.stat().st_mtime
                from datetime import datetime
                mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                print(f"  {i:4d}. {cache_file.stem} (modified: {mod_time})")

        print(f"\n{'='*80}\n")

    def query(self, query_file, show_output=True):
        """
        Query database with audio file

        Args:
            query_file: Path to query audio file
            show_output: If True, print results; if False, return them

        Returns:
            Query results if show_output=False
        """
        # Expand ~ in paths
        query_file = Path(os.path.expanduser(str(query_file))).resolve()

        if not query_file.exists():
            print(f"Error: Query file not found: {query_file}", file=sys.stderr)
            return None

        print(f"\n{'='*80}")
        print(f"Query: {query_file.name}")
        print(f"{'='*80}\n")

        if show_output:
            self._run_command('query', str(query_file))
            return None
        else:
            result = self._run_command('query', str(query_file), capture_output=True)
            return result.stdout if result else None

    def delete(self, path):
        """
        Delete audio file(s) from database

        Args:
            path: Path to audio file or directory to remove
        """
        # Expand ~ in paths
        path = Path(os.path.expanduser(str(path))).resolve()

        if path.is_file():
            print(f"Deleting: {path.name}")
            self._run_command('delete', str(path))
        elif path.is_dir():
            print(f"Deleting audio files from: {path}")
            # Find all audio files
            audio_files = []
            for ext in self.AUDIO_EXTENSIONS:
                audio_files.extend(path.rglob(f"*{ext}"))

            if not audio_files:
                print(f"No audio files found in {path}")
                return

            print(f"Found {len(audio_files)} audio files to delete")

            for audio_file in sorted(audio_files):
                self._run_command('delete', str(audio_file))
        else:
            print(f"Error: {path} not found", file=sys.stderr)

    def clear(self, confirm=True):
        """
        Clear entire database

        Args:
            confirm: If True, ask for confirmation
        """
        if confirm:
            response = input("Clear entire database? This cannot be undone! (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return

        print("Clearing database...")
        self._run_command('clear')
        print("Database cleared.")

    def stats(self):
        """Show database statistics"""
        print("\n" + "="*80)
        print("Database Statistics")
        print("="*80 + "\n")
        self._run_command('stats')

    def batch_query(self, query_dir, threshold=None):
        """
        Query all audio files in a directory

        Args:
            query_dir: Directory containing query files
            threshold: Optional matching threshold
        """
        # Expand ~ in paths
        query_dir = Path(os.path.expanduser(str(query_dir))).resolve()

        if not query_dir.exists():
            print(f"Error: Directory not found: {query_dir}", file=sys.stderr)
            return

        # Find all audio files
        audio_files = []
        for ext in self.AUDIO_EXTENSIONS:
            audio_files.extend(query_dir.rglob(f"*{ext}"))

        audio_files = sorted(audio_files)

        if not audio_files:
            print(f"No audio files found in {query_dir}")
            print(f"Supported formats: {', '.join(self.AUDIO_EXTENSIONS)}")
            return

        print(f"\n{'='*80}")
        print(f"Batch Query: {len(audio_files)} files from {query_dir}")
        print(f"{'='*80}\n")

        for i, audio_file in enumerate(audio_files, 1):
            print(f"[{i}/{len(audio_files)}] ", end="")
            self.query(audio_file, show_output=True)

    def verify_setup(self):
        """Verify that Panako is properly configured"""
        print("\n" + "="*80)
        print("Panako Setup Verification")
        print("="*80 + "\n")

        all_checks = []

        # Detect system info
        print("System Information:")
        print(f"  Platform: {self.platform}")
        if self.platform == 'darwin':
            try:
                result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
                arch = result.stdout.strip()
                print(f"  Architecture: {arch} ({'Apple Silicon' if arch == 'arm64' else 'Intel'})")
            except:
                pass
        print()

        # Check Python version
        print(f"Python: {sys.version.split()[0]}")
        python_ok = sys.version_info >= (3, 7)
        print(f"  Status: {'✓ OK' if python_ok else '✗ Too old (need 3.7+)'}")
        all_checks.append(python_ok)
        print()

        # Check Panako directory
        print(f"Panako directory: {self.panako_dir}")
        panako_exists = self.panako_dir.exists()
        print(f"  Status: {'✓ Exists' if panako_exists else '✗ Not found'}")
        if not panako_exists:
            print(f"  Run: git clone https://github.com/JorenSix/Panako.git {self.panako_dir}")
        all_checks.append(panako_exists)
        print()

        # Check JAR file
        jar_files = list(self.jar_path.glob("panako-*-all.jar"))
        jar_exists = len(jar_files) > 0
        print(f"Panako JAR: {'✓ Found' if jar_exists else '✗ Not found'}")
        if jar_files:
            print(f"  Location: {jar_files[0]}")
        else:
            print(f"  Expected in: {self.jar_path}")
            print(f"  Run: cd {self.panako_dir} && chmod +x gradlew && ./gradlew shadowJar")
            print(f"  Note: First build requires internet and takes 2-5 minutes")
        all_checks.append(jar_exists)
        print()

        # Check Java
        print(f"Java:")
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
            # Java outputs version to stderr, so check stderr
            version_output = result.stderr if result.stderr else result.stdout
            java_version = version_output.split('\n')[0] if version_output else "Unknown"
            print(f"  Status: ✓ {java_version}")
            if 'version "17' in java_version or ' 17.' in java_version:
                print(f"  Version: ✓ Java 17 (recommended)")
            all_checks.append(True)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  Status: ✗ Not found")
            if self.platform == 'darwin':
                print("  Install: brew install openjdk@17")
                print('  Add to ~/.zshrc: export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"')
            else:
                print("  Install: sudo apt install openjdk-17-jdk")
            all_checks.append(False)
        print()

        # Check LMDB
        print(f"LMDB library:")
        if self.platform == 'darwin':
            lmdb_paths = ['/opt/homebrew/lib/liblmdb.dylib', '/usr/local/lib/liblmdb.dylib']
        else:
            lmdb_paths = ['/usr/lib/liblmdb.so', '/usr/lib/x86_64-linux-gnu/liblmdb.so', '/usr/lib/aarch64-linux-gnu/liblmdb.so']

        lmdb_found = any(os.path.exists(p) for p in lmdb_paths)
        lmdb_location = next((p for p in lmdb_paths if os.path.exists(p)), None)

        if lmdb_found:
            print(f"  Status: ✓ Found at {lmdb_location}")
        else:
            print("  Status: ✗ Not found")
            if self.platform == 'darwin':
                print("  Install: brew install lmdb")
            else:
                print("  Install: sudo apt install liblmdb-dev")
        all_checks.append(lmdb_found)
        print()

        # Check ffmpeg (optional)
        print(f"ffmpeg (optional):")
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ffmpeg_version = result.stdout.split('\n')[0]
                print(f"  Status: ✓ {ffmpeg_version[:60]}")
            else:
                print("  Status: ⚠ Not working properly")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  Status: ⚠ Not found (WAV files only)")
            if self.platform == 'darwin':
                print("  Install: brew install ffmpeg")
            else:
                print("  Install: sudo apt install ffmpeg")
        print()

        # Check database
        print(f"Database:")
        db_path = Path.home() / ".panako/dbs"
        db_exists = db_path.exists()
        if db_exists:
            cache_files = list((db_path / "olaf_cache").glob("*.tdb")) if (db_path / "olaf_cache").exists() else []
            print(f"  Status: ✓ Initialized ({len(cache_files)} files indexed)")
            print(f"  Location: {db_path}")

            # Check permissions
            if os.access(db_path, os.W_OK):
                print(f"  Permissions: ✓ Writable")
            else:
                print(f"  Permissions: ✗ Not writable")
                print(f"  Run: chmod u+w {db_path}")
                all_checks.append(False)
        else:
            print("  Status: ℹ Not initialized (will be created on first use)")

        print("\n" + "="*80)

        all_good = all(all_checks)

        if all_good:
            print("✓ Setup complete! Ready to use Panako.")
            print("\nQuick start:")
            print("  python3 panako.py store ~/Music          # Index your music")
            print("  python3 panako.py query ~/test.wav       # Find a match")
        else:
            print("✗ Setup incomplete. Please fix the issues above.")
            print("\nQuick fix:")
            print("  1. Install missing dependencies (see above)")
            print("  2. Build Panako: cd ~/Panako && chmod +x gradlew && ./gradlew shadowJar")
            print("  3. Run 'python3 panako.py verify' again")

        print("="*80 + "\n")

        return all_good


def print_help():
    """Print detailed help message"""
    print("Panako Python Wrapper - Audio Fingerprinting")
    print("\nUsage:")
    print("  python3 panako.py <command> [arguments]")
    print("\nCommands:")
    print("  verify                      Check if Panako is properly installed")
    print("  store <path>                Add audio file(s) to database")
    print("  query <file>                Search for a match in database")
    print("  batch <directory>           Query all files in a directory")
    print("  stats                       Show database statistics")
    print("  list                        List all fingerprints in database")
    print("  delete <path>               Remove file(s) from database")
    print("  clear                       Clear entire database (with confirmation)")
    print("\nExamples:")
    print("  python3 panako.py verify")
    print("  python3 panako.py store ~/Music")
    print("  python3 panako.py query ~/unknown_song.wav")
    print("  python3 panako.py batch ~/test_files")
    print("  python3 panako.py stats")
    print("\nSupported formats: WAV, MP3, FLAC, OGG, M4A, AAC, WMA")
    print("(MP3/FLAC/etc require ffmpeg to be installed)")
    print("\nFor more help: https://github.com/SynthAether/panako-python-wrapper")


def main():
    """Command-line interface"""

    # Handle help flags
    if len(sys.argv) >= 2 and sys.argv[1].lower() in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Special case: verify command doesn't need full initialization
    if len(sys.argv) >= 2 and sys.argv[1].lower() == 'verify':
        try:
            panako = Panako(skip_validation=True)
            panako.verify_setup()
        except Exception as e:
            print(f"Error during verification: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        sys.exit(0)

    # Initialize Panako
    try:
        panako = Panako()
    except Exception as e:
        print(f"Error initializing Panako: {e}", file=sys.stderr)
        print("\nTry running: python3 panako.py verify", file=sys.stderr)
        sys.exit(1)

    # Parse command
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'store':
        if len(sys.argv) < 3:
            print("Error: Provide path to store", file=sys.stderr)
            print("Usage: python3 panako.py store <file_or_directory>", file=sys.stderr)
            sys.exit(1)
        panako.store(sys.argv[2])

    elif command == 'query':
        if len(sys.argv) < 3:
            print("Error: Provide query file", file=sys.stderr)
            print("Usage: python3 panako.py query <query_file>", file=sys.stderr)
            sys.exit(1)
        panako.query(sys.argv[2])

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Error: Provide path to delete", file=sys.stderr)
            print("Usage: python3 panako.py delete <file_or_directory>", file=sys.stderr)
            sys.exit(1)
        panako.delete(sys.argv[2])

    elif command == 'clear':
        panako.clear()

    elif command == 'stats':
        panako.stats()

    elif command == 'batch':
        if len(sys.argv) < 3:
            print("Error: Provide query directory", file=sys.stderr)
            print("Usage: python3 panako.py batch <query_directory>", file=sys.stderr)
            sys.exit(1)
        panako.batch_query(sys.argv[2])

    elif command == 'list':
        panako.list_cache_files()

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Run 'python3 panako.py --help' for usage information", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()