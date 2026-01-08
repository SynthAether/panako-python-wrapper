#!/usr/bin/env python3
"""
Python wrapper for Panako audio fingerprinting
Handles all Java configuration and provides clean Python interface
"""

import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# Check Python version at import time
if sys.version_info < (3, 7):
    print("Error: Python 3.7 or higher is required", file=sys.stderr)
    print(f"Current version: {sys.version}", file=sys.stderr)
    sys.exit(1)

class Panako:
    # Supported audio formats (when ffmpeg is available)
    AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma']

    # Manifest file to track indexed files
    MANIFEST_FILE = Path.home() / ".panako" / "indexed_files.txt"

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
                # Check Java version (version_output already set from stderr above)
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

    def _load_manifest(self):
        """Load set of already-indexed file paths from manifest"""
        if self.MANIFEST_FILE.exists():
            with open(self.MANIFEST_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_to_manifest(self, file_path):
        """Append a file path to the manifest"""
        # Ensure directory exists
        self.MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.MANIFEST_FILE, 'a') as f:
            f.write(str(file_path) + '\n')

    def _remove_from_manifest(self, file_path):
        """Remove a file path from the manifest"""
        if not self.MANIFEST_FILE.exists():
            return
        indexed = self._load_manifest()
        indexed.discard(str(file_path))
        with open(self.MANIFEST_FILE, 'w') as f:
            for path in sorted(indexed):
                f.write(path + '\n')

    def store(self, path, force=False):
        """
        Add audio file(s) to database

        Args:
            path: Path to audio file or directory
            force: If True, re-index even if already in manifest
        """
        # Expand ~ in paths
        path = Path(os.path.expanduser(str(path))).resolve()

        # Load manifest of already-indexed files
        indexed = self._load_manifest()

        if path.is_file():
            if str(path) in indexed and not force:
                print(f"Skipping (already indexed): {path.name}")
                print("  Use --force to re-index")
                return
            print(f"Storing: {path.name}")
            result = self._run_command('store', str(path), capture_output=True)
            if result:
                self._save_to_manifest(path)
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

            # Filter out already-indexed files unless force is True
            if not force:
                new_files = [f for f in audio_files if str(f.resolve()) not in indexed]
                skipped = len(audio_files) - len(new_files)
                if skipped > 0:
                    print(f"Skipping {skipped} already-indexed files (use --force to re-index)")
                audio_files = new_files

            if not audio_files:
                print("No new files to index.")
                return

            print(f"Found {len(audio_files)} audio files to index")

            # Store all files with progress indication
            for i, audio_file in enumerate(sorted(audio_files), 1):
                print(f"  [{i}/{len(audio_files)}] {audio_file.name[:60]}...", end=" ", flush=True)
                result = self._run_command('store', str(audio_file), capture_output=True)
                if result:
                    self._save_to_manifest(audio_file.resolve())
                    print("✓")
                else:
                    print("✗")
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
            self._remove_from_manifest(path)
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
                self._remove_from_manifest(audio_file.resolve())
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
        # Also clear the manifest
        if self.MANIFEST_FILE.exists():
            self.MANIFEST_FILE.unlink()
            print("Manifest cleared.")
        print("Database cleared.")

    def stats(self):
        """Show database statistics"""
        print("\n" + "="*80)
        print("Database Statistics")
        print("="*80 + "\n")
        self._run_command('stats')

    def init_manifest(self, path):
        """
        Mark audio files as already indexed (without re-processing them).
        Use this to initialize the manifest for files you've already indexed.

        Args:
            path: Path to audio file or directory to mark as indexed
        """
        # Expand ~ in paths
        path = Path(os.path.expanduser(str(path))).resolve()

        # Load existing manifest
        indexed = self._load_manifest()
        added = 0

        if path.is_file():
            if str(path) not in indexed:
                self._save_to_manifest(path)
                added = 1
                print(f"Marked as indexed: {path.name}")
            else:
                print(f"Already in manifest: {path.name}")
        elif path.is_dir():
            print(f"Scanning for audio files in: {path}")
            # Find all audio files
            audio_files = []
            for ext in self.AUDIO_EXTENSIONS:
                audio_files.extend(path.rglob(f"*{ext}"))

            if not audio_files:
                print(f"No audio files found in {path}")
                print(f"Supported formats: {', '.join(self.AUDIO_EXTENSIONS)}")
                return

            print(f"Found {len(audio_files)} audio files")

            for audio_file in sorted(audio_files):
                resolved = str(audio_file.resolve())
                if resolved not in indexed:
                    self._save_to_manifest(audio_file.resolve())
                    indexed.add(resolved)  # Update local set to avoid duplicates
                    added += 1

            print(f"\nAdded {added} files to manifest")
            if added < len(audio_files):
                print(f"Skipped {len(audio_files) - added} files (already in manifest)")
        else:
            print(f"Error: {path} not found", file=sys.stderr)
            return

        print(f"Manifest location: {self.MANIFEST_FILE}")

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

    def _get_audio_duration(self, audio_file):
        """Get duration of audio file in seconds using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_file)
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass
        return None

    def _segment_audio(self, audio_file, segment_length, overlap, temp_dir):
        """
        Segment audio file into overlapping chunks using ffmpeg.

        Returns list of (segment_path, start_time, end_time) tuples.
        """
        duration = self._get_audio_duration(audio_file)
        if duration is None:
            print(f"Warning: Could not determine duration of {audio_file}", file=sys.stderr)
            return []

        segments = []
        step = segment_length - overlap
        start = 0.0
        segment_num = 0

        while start < duration:
            end = min(start + segment_length, duration)
            # Skip very short final segments (less than 3 seconds)
            if end - start < 3:
                break

            segment_path = Path(temp_dir) / f"segment_{segment_num:04d}.wav"

            # Use ffmpeg to extract segment
            try:
                result = subprocess.run([
                    'ffmpeg', '-y', '-v', 'error',
                    '-i', str(audio_file),
                    '-ss', str(start),
                    '-t', str(segment_length),
                    '-ar', '16000',  # Resample to 16kHz (Panako's default)
                    '-ac', '1',      # Mono
                    str(segment_path)
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0 and segment_path.exists():
                    segments.append((segment_path, start, end))
                    segment_num += 1
            except subprocess.TimeoutExpired:
                print(f"Warning: Timeout creating segment at {start}s", file=sys.stderr)

            start += step

        return segments

    def _parse_query_output(self, output):
        """
        Parse Panako query output to extract match information.

        Panako output format (semicolon-separated):
        Index; Total; Query path; Query start; Query stop; Match path; Match id; Match start; Match stop; Score; Time factor; Freq factor; Match %

        Returns list of dicts with match details.
        """
        matches = []
        if not output:
            return matches

        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip non-data lines (headers, info messages)
            if not line[0].isdigit():
                continue

            # Parse semicolon-separated format
            parts = [p.strip() for p in line.split(';')]
            if len(parts) >= 10:
                try:
                    query_path = parts[2]
                    match_path = parts[5]
                    match_score = int(parts[9])

                    # Skip self-matches (query matching itself)
                    if query_path == match_path:
                        continue

                    # Skip if match_path is a temp segment file
                    if '/panako_deep_' in match_path or 'segment_' in match_path:
                        continue

                    matches.append({
                        'path': match_path,
                        'score': match_score,
                        'match_start': float(parts[7]) if parts[7] else 0,
                        'match_stop': float(parts[8]) if parts[8] else 0
                    })
                except (ValueError, IndexError):
                    continue

        return matches

    def deep_query(self, query_file, segment_length=15, overlap=2, min_segments=1, show_details=False):
        """
        Query database by segmenting a long audio file into overlapping chunks.

        This is useful for finding partial matches when the query file is long
        and may only partially match files in the database.

        Args:
            query_file: Path to query audio file
            segment_length: Length of each segment in seconds (default: 15)
            overlap: Overlap between segments in seconds (default: 2)
            min_segments: Minimum segment matches to report a file (default: 1)
            show_details: If True, show per-segment match details

        Returns:
            Dict of results with match statistics
        """
        # Expand ~ in paths
        query_file = Path(os.path.expanduser(str(query_file))).resolve()

        if not query_file.exists():
            print(f"Error: Query file not found: {query_file}", file=sys.stderr)
            return None

        # Check ffmpeg/ffprobe availability
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("Error: ffprobe not found. Install ffmpeg for deep-query support.", file=sys.stderr)
            return None

        duration = self._get_audio_duration(query_file)
        if duration is None:
            print(f"Error: Could not determine audio duration", file=sys.stderr)
            return None

        # Format duration for display
        dur_min = int(duration // 60)
        dur_sec = int(duration % 60)

        print(f"\n{'='*80}")
        print(f"Deep Query: {query_file.name}")
        print(f"Duration: {dur_min}:{dur_sec:02d} | Segment: {segment_length}s | Overlap: {overlap}s")
        print(f"{'='*80}\n")

        # Create temp directory for segments
        with tempfile.TemporaryDirectory(prefix='panako_deep_') as temp_dir:
            # Segment the audio
            print("Segmenting audio...", end=" ", flush=True)
            segments = self._segment_audio(query_file, segment_length, overlap, temp_dir)
            print(f"created {len(segments)} segments")

            if not segments:
                print("Error: No segments created", file=sys.stderr)
                return None

            # Query each segment and collect results
            all_matches = defaultdict(lambda: {'count': 0, 'segments': [], 'total_score': 0})

            print(f"\nQuerying segments:")
            for i, (seg_path, start_time, end_time) in enumerate(segments, 1):
                start_fmt = f"{int(start_time//60)}:{int(start_time%60):02d}"
                end_fmt = f"{int(end_time//60)}:{int(end_time%60):02d}"

                print(f"  [{i}/{len(segments)}] {start_fmt}-{end_fmt}...", end=" ", flush=True)

                # Run query
                result = self._run_command('query', str(seg_path), capture_output=True)

                if result and result.stdout:
                    matches = self._parse_query_output(result.stdout)
                    if matches:
                        print(f"✓ {len(matches)} match(es)")
                        for match in matches:
                            path = match.get('path', 'unknown')
                            score = match.get('score', 1)
                            all_matches[path]['count'] += 1
                            all_matches[path]['total_score'] += score
                            all_matches[path]['segments'].append({
                                'start': start_time,
                                'end': end_time,
                                'score': score
                            })
                        if show_details:
                            for match in matches:
                                print(f"       → {Path(match.get('path', 'unknown')).name}")
                    else:
                        print("○ no match")
                else:
                    print("○ no match")

            # Filter and sort results
            results = []
            for path, data in all_matches.items():
                if data['count'] >= min_segments:
                    # Calculate time ranges from segments
                    segments_list = sorted(data['segments'], key=lambda x: x['start'])

                    # Merge overlapping/adjacent time ranges
                    time_ranges = []
                    for seg in segments_list:
                        if time_ranges and seg['start'] <= time_ranges[-1][1] + overlap:
                            # Extend previous range
                            time_ranges[-1] = (time_ranges[-1][0], max(time_ranges[-1][1], seg['end']))
                        else:
                            time_ranges.append((seg['start'], seg['end']))

                    results.append({
                        'path': path,
                        'segment_count': data['count'],
                        'total_segments': len(segments),
                        'percentage': (data['count'] / len(segments)) * 100,
                        'total_score': data['total_score'],
                        'time_ranges': time_ranges
                    })

            # Sort by segment count (descending), then by total score
            results.sort(key=lambda x: (x['segment_count'], x['total_score']), reverse=True)

            # Print results
            print(f"\n{'='*80}")
            print(f"RESULTS: {len(results)} file(s) matched (min {min_segments} segment(s))")
            print(f"{'='*80}\n")

            if not results:
                print("No matches found meeting the minimum segment threshold.")
                print(f"Try lowering --min-segments (currently {min_segments})")
            else:
                for rank, r in enumerate(results, 1):
                    path = Path(r['path'])
                    print(f"{rank}. {path.name}")
                    print(f"   Path: {r['path']}")
                    print(f"   Segments: {r['segment_count']}/{r['total_segments']} ({r['percentage']:.1f}%)")
                    print(f"   Total score: {r['total_score']} fingerprints")

                    # Format time ranges
                    range_strs = []
                    for start, end in r['time_ranges']:
                        start_fmt = f"{int(start//60)}:{int(start%60):02d}"
                        end_fmt = f"{int(end//60)}:{int(end%60):02d}"
                        range_strs.append(f"{start_fmt}-{end_fmt}")
                    print(f"   Matched at: {', '.join(range_strs)}")
                    print()

            print(f"{'='*80}\n")

            return results

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
    print("  store [--force] <path>      Add audio file(s) to database")
    print("                              Skips already-indexed files unless --force is used")
    print("  init-manifest <path>        Mark files as indexed without re-processing")
    print("                              Use for files already in the database")
    print("  query <file>                Search for a match in database")
    print("  deep-query [options] <file> Segment long audio and find partial matches")
    print("  batch <directory>           Query all files in a directory")
    print("  stats                       Show database statistics")
    print("  list                        List all fingerprints in database")
    print("  delete <path>               Remove file(s) from database")
    print("  clear                       Clear entire database (with confirmation)")
    print("\nDeep Query Options:")
    print("  --segment <seconds>         Segment length (default: 15)")
    print("  --overlap <seconds>         Overlap between segments (default: 2)")
    print("  --min-segments <n>          Minimum segments to match (default: 1)")
    print("  --details                   Show per-segment match details")
    print("\nExamples:")
    print("  python3 panako.py verify")
    print("  python3 panako.py init-manifest ~/Data/Vangelis/ref  # Mark existing as indexed")
    print("  python3 panako.py store ~/Music")
    print("  python3 panako.py store --force ~/Music   # Re-index all files")
    print("  python3 panako.py query ~/unknown_song.wav")
    print("  python3 panako.py deep-query ~/long_recording.wav")
    print("  python3 panako.py deep-query --segment 20 --overlap 5 ~/recording.wav")
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
            print("Usage: python3 panako.py store [--force] <file_or_directory>", file=sys.stderr)
            sys.exit(1)
        # Check for --force flag
        force = '--force' in sys.argv
        path_arg = [arg for arg in sys.argv[2:] if arg != '--force'][0]
        panako.store(path_arg, force=force)

    elif command == 'init-manifest':
        if len(sys.argv) < 3:
            print("Error: Provide path to mark as indexed", file=sys.stderr)
            print("Usage: python3 panako.py init-manifest <file_or_directory>", file=sys.stderr)
            sys.exit(1)
        panako.init_manifest(sys.argv[2])

    elif command == 'query':
        if len(sys.argv) < 3:
            print("Error: Provide query file", file=sys.stderr)
            print("Usage: python3 panako.py query <query_file>", file=sys.stderr)
            sys.exit(1)
        panako.query(sys.argv[2])

    elif command == 'deep-query':
        if len(sys.argv) < 3:
            print("Error: Provide query file", file=sys.stderr)
            print("Usage: python3 panako.py deep-query [options] <query_file>", file=sys.stderr)
            sys.exit(1)

        # Parse options
        segment_length = 15
        overlap = 2
        min_segments = 1
        show_details = False
        query_file = None

        args = sys.argv[2:]
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--segment' and i + 1 < len(args):
                segment_length = int(args[i + 1])
                i += 2
            elif arg == '--overlap' and i + 1 < len(args):
                overlap = int(args[i + 1])
                i += 2
            elif arg == '--min-segments' and i + 1 < len(args):
                min_segments = int(args[i + 1])
                i += 2
            elif arg == '--details':
                show_details = True
                i += 1
            elif not arg.startswith('--'):
                query_file = arg
                i += 1
            else:
                print(f"Unknown option: {arg}", file=sys.stderr)
                sys.exit(1)

        if not query_file:
            print("Error: Provide query file", file=sys.stderr)
            sys.exit(1)

        panako.deep_query(
            query_file,
            segment_length=segment_length,
            overlap=overlap,
            min_segments=min_segments,
            show_details=show_details
        )

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