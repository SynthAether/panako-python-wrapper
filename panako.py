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
    def __init__(self, panako_dir="/Users/sufian/Work/Panako"):
        """
        Initialize Panako wrapper
        
        Args:
            panako_dir: Path to Panako installation directory
        """
        self.panako_dir = Path(panako_dir)
        self.jar_path = self.panako_dir / "build/libs"
        
        # Setup environment
        self._setup_environment()
        
        # Build Java command base
        self.java_cmd = self._build_java_command()
        
    def _setup_environment(self):
        """Setup required environment variables"""
        # LMDB library path for macOS
        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')
        
        # Ensure JAVA_HOME is set (for M1 Macs with Homebrew Java)
        if 'JAVA_HOME' not in os.environ:
            # Try to find Java installation
            java_homes = [
                '/opt/homebrew/Cellar/openjdk@17',
                '/usr/local/Cellar/openjdk@17',
                '/Library/Java/JavaVirtualMachines',
            ]
            for java_home in java_homes:
                if os.path.exists(java_home):
                    # Find the actual JDK path
                    for item in os.listdir(java_home):
                        full_path = os.path.join(java_home, item)
                        if os.path.isdir(full_path):
                            os.environ['JAVA_HOME'] = full_path
                            break
                    if 'JAVA_HOME' in os.environ:
                        break
    
    def _build_java_command(self):
        """Build the base Java command with all required options"""
        # Find the Panako JAR file
        jar_files = list(self.jar_path.glob("panako-*-all.jar"))
        if not jar_files:
            raise FileNotFoundError(f"Panako JAR not found in {self.jar_path}")
        
        jar_file = jar_files[0]
        
        # Build Java command with all required flags
        java_opts = [
            'java',
            '--add-opens', 'java.base/java.nio=ALL-UNNAMED',
            '--add-opens', 'java.base/sun.nio.ch=ALL-UNNAMED',
            '-Djava.library.path=/opt/homebrew/lib',
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
            if capture_output and e.output:
                print(e.output, file=sys.stderr)
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
            print(f"Storing all WAV files from: {path}")
            # Find all WAV files
            wav_files = list(path.rglob("*.wav"))
            print(f"Found {len(wav_files)} WAV files")
            
            # Store all files
            for wav_file in wav_files:
                self._run_command('store', str(wav_file))
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
            print(f"Deleting all WAV files from: {path}")
            wav_files = list(path.rglob("*.wav"))
            print(f"Found {len(wav_files)} WAV files to delete")
            
            for wav_file in wav_files:
                self._run_command('delete', str(wav_file))
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
        Query all WAV files in a directory
        
        Args:
            query_dir: Directory containing query files
            threshold: Optional matching threshold
        """
        query_dir = Path(query_dir)
        
        if not query_dir.exists():
            print(f"Error: Directory not found: {query_dir}", file=sys.stderr)
            return
        
        # Find all WAV files
        wav_files = sorted(query_dir.rglob("*.wav"))
        
        print(f"\n{'='*80}")
        print(f"Batch Query: {len(wav_files)} files from {query_dir}")
        print(f"{'='*80}\n")
        
        for i, wav_file in enumerate(wav_files, 1):
            print(f"[{i}/{len(wav_files)}] ", end="")
            self.query(wav_file, show_output=True)


def main():
    """Command-line interface"""
    
    # Initialize Panako
    try:
        panako = Panako()
    except Exception as e:
        print(f"Error initializing Panako: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse command
    if len(sys.argv) < 2:
        print("Panako Python Wrapper")
        print("\nUsage:")
        print("  python3 panako.py store <file_or_directory>")
        print("  python3 panako.py query <query_file>")
        print("  python3 panako.py delete <file_or_directory>")
        print("  python3 panako.py clear")
        print("  python3 panako.py stats")
        print("  python3 panako.py batch <query_directory>")
        print("\nExamples:")
        print("  python3 panako.py store /Users/sufian/Data/Vangelis/ref")
        print("  python3 panako.py query '/Users/sufian/Data/Vangelis/queries/test.wav'")
        print("  python3 panako.py stats")
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
        sys.exit(1)


if __name__ == "__main__":
    main()