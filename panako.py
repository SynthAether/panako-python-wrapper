#!/usr/bin/env python3
"""
Python wrapper for Panako audio fingerprinting
Handles all Java configuration and provides clean Python interface
"""

import os
import subprocess
import sys
from pathlib import Path

class Panako:
    # Supported audio formats (when ffmpeg is available)
    AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma']

    def __init__(self, panako_dir=None, skip_validation=False):
        """
        Initialize Panako wrapper

        Args:
            panako_dir: Path to Panako installation directory
                        If not provided, looks for PANAKO_DIR environment variable
                        or defaults to ~/Panako
            skip_validation: If True, skip dependency validation (for testing)
        """
        if panako_dir is None:
            panako_dir = os.environ.get('PANAKO_DIR', os.path.expanduser('~/Panako'))

        self.panako_dir = Path(panako_dir)
        self.jar_path = self.panako_dir / "build/libs"

        # Detect platform
        self.platform = sys.platform  # 'darwin', 'linux', 'win32'

        # Setup environment
        self._setup_environment()

        # Validate dependencies
        if not skip_validation:
            self._validate_dependencies()

        # Build Java command base
        self.java_cmd = self._build_java_command()

    def _setup_environment(self):
        """Setup required environment variables"""
        if self.platform == 'darwin':
            # LMDB library path for macOS
            # Try Apple Silicon path first, then Intel
            lib_paths = ['/opt/homebrew/lib', '/usr/local/lib']
            existing_paths = [p for p in lib_paths if os.path.exists(p)]
            if existing_paths:
                os.environ['DYLD_LIBRARY_PATH'] = ':'.join(existing_paths) + ':' + os.environ.get('DYLD_LIBRARY_PATH', '')

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
                            for item in os.listdir(java_home):
                                full_path = os.path.join(java_home, item, 'Contents/Home')
                                if os.path.isdir(full_path):
                                    os.environ['JAVA_HOME'] = full_path
                                    break
                        else:
                            os.environ['JAVA_HOME'] = java_home
                        if 'JAVA_HOME' in os.environ:
                            break

        elif self.platform == 'linux':
            # LMDB library path for Linux
            lib_paths = ['/usr/lib', '/usr/local/lib', '/usr/lib/x86_64-linux-gnu', '/usr/lib/aarch64-linux-gnu']
            existing_paths = [p for p in lib_paths if os.path.exists(p)]
            if existing_paths:
                os.environ['LD_LIBRARY_PATH'] = ':'.join(existing_paths) + ':' + os.environ.get('LD_LIBRARY_PATH', '')

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
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                errors.append("Java not found or not working properly")
                if self.platform == 'darwin':
                    errors.append("  Install: brew install openjdk@17")
                else:
                    errors.append("  Install: sudo apt install openjdk-17-jdk")
        except FileNotFoundError:
            errors.append("Java not found")
            if self.platform == 'darwin':
                errors.append("  Install: brew install openjdk@17")
                errors.append("  Then: export JAVA_HOME=\"/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home\"")
            else:
                errors.append("  Install: sudo apt install openjdk-17-jdk")
                errors.append("  Then: export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64")

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
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode != 0:
                warnings.append("ffmpeg not found (optional, but recommended for non-WAV formats)")
        except FileNotFoundError:
            warnings.append("ffmpeg not found (optional, but recommended for non-WAV formats)")
            if self.platform == 'darwin':
                warnings.append("  Install: brew install ffmpeg")
            else:
                warnings.append("  Install: sudo apt install ffmpeg")

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
1. Build Panako:
   cd {self.panako_dir}
   ./gradlew shadowJar

2. If Panako is installed elsewhere, set PANAKO_DIR:
   export PANAKO_DIR="/path/to/your/Panako"

3. Or specify path when creating Panako instance:
   panako = Panako(panako_dir="/path/to/your/Panako")

Current Panako directory: {self.panako_dir}
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
        except FileNotFoundError as e:
            print(f"Error: Java executable not found. Please install Java 17+", file=sys.stderr)
            return None

    def store(self, path):
        """
        Add audio file(s) to database

        Args:
            path: Path to audio file or directory
        """
        path = Path(path)

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

            # Store all files
            for audio_file in sorted(audio_files):
                self._run_command('store', str(audio_file))
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
        query_file = Path(query_file)

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
        path = Path(path)

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
        query_dir = Path(query_dir)

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

        # Check Panako directory
        print(f"Panako directory: {self.panako_dir}")
        panako_exists = self.panako_dir.exists()
        print(f"  Status: {'✓ Exists' if panako_exists else '✗ Not found'}")
        all_checks.append(panako_exists)

        # Check JAR file
        jar_files = list(self.jar_path.glob("panako-*-all.jar"))
        jar_exists = len(jar_files) > 0
        print(f"\nPanako JAR: {'✓ Found' if jar_exists else '✗ Not found'}")
        if jar_files:
            print(f"  Location: {jar_files[0]}")
        else:
            print(f"  Expected in: {self.jar_path}")
            print(f"  Run: cd {self.panako_dir} && ./gradlew shadowJar")
        all_checks.append(jar_exists)

        # Check Java
        print(f"\nJava:")
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, stderr=subprocess.STDOUT)
            java_version = result.stdout.split('\n')[0]
            print(f"  Status: ✓ {java_version}")
            all_checks.append(True)
        except:
            print("  Status: ✗ Not found")
            if self.platform == 'darwin':
                print("  Install: brew install openjdk@17")
            else:
                print("  Install: sudo apt install openjdk-17-jdk")
            all_checks.append(False)

        # Check LMDB
        print(f"\nLMDB library:")
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

        # Check ffmpeg (optional)
        print(f"\nffmpeg (optional):")
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                ffmpeg_version = result.stdout.split('\n')[0]
                print(f"  Status: ✓ {ffmpeg_version}")
            else:
                print("  Status: ⚠ Not working properly")
        except:
            print("  Status: ⚠ Not found (WAV files only)")
            if self.platform == 'darwin':
                print("  Install: brew install ffmpeg")
            else:
                print("  Install: sudo apt install ffmpeg")

        # Check database
        print(f"\nDatabase:")
        db_path = Path.home() / ".panako/dbs"
        db_exists = db_path.exists()
        if db_exists:
            cache_files = list((db_path / "olaf_cache").glob("*.tdb")) if (db_path / "olaf_cache").exists() else []
            print(f"  Status: ✓ Initialized ({len(cache_files)} files indexed)")
            print(f"  Location: {db_path}")
        else:
            print("  Status: ℹ Not initialized (will be created on first use)")

        print("\n" + "="*80)

        all_good = all(all_checks)

        if all_good:
            print("✓ Setup complete! Ready to use Panako.")
        else:
            print("✗ Setup incomplete. Please fix the issues above.")
            print("\nQuick fix:")
            print("  1. Install missing dependencies")
            print("  2. Build Panako: cd ~/Panako && ./gradlew shadowJar")
            print("  3. Run 'python3 panako.py verify' again")

        print("="*80 + "\n")

        return all_good


def main():
    """Command-line interface"""

    # Special case: verify command doesn't need full initialization
    if len(sys.argv) >= 2 and sys.argv[1].lower() == 'verify':
        try:
            panako = Panako(skip_validation=True)
            panako.verify_setup()
        except Exception as e:
            print(f"Error during verification: {e}", file=sys.stderr)
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
        print("Panako Python Wrapper")
        print("\nUsage:")
        print("  python3 panako.py verify")
        print("  python3 panako.py store <file_or_directory>")
        print("  python3 panako.py query <query_file>")
        print("  python3 panako.py batch <query_directory>")
        print("  python3 panako.py stats")
        print("  python3 panako.py list")
        print("  python3 panako.py delete <file_or_directory>")
        print("  python3 panako.py clear")
        print("\nExamples:")
        print("  python3 panako.py verify                          # Check setup")
        print("  python3 panako.py store /path/to/audio/library    # Build database")
        print("  python3 panako.py query '/path/to/query.wav'      # Find matches")
        print("  python3 panako.py stats                           # Show database info")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'store':
        if len(sys.argv) < 3:
            print("Error: Provide path to store", file=sys.stderr)
            sys.exit(1)
        panako.store(sys.argv[2])

    elif command == 'query':
        if len(sys.argv) < 3:
            print("Error: Provide query file", file=sys.stderr)
            sys.exit(1)
        panako.query(sys.argv[2])

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Error: Provide path to delete", file=sys.stderr)
            sys.exit(1)
        panako.delete(sys.argv[2])

    elif command == 'clear':
        panako.clear()

    elif command == 'stats':
        panako.stats()

    elif command == 'batch':
        if len(sys.argv) < 3:
            print("Error: Provide query directory", file=sys.stderr)
            sys.exit(1)
        panako.batch_query(sys.argv[2])

    elif command == 'list':
        panako.list_cache_files()

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Run 'python3 panako.py' for usage information", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()