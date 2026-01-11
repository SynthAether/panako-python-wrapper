# Panako Python Wrapper

A Python wrapper for [Panako](https://github.com/JorenSix/Panako), an acoustic fingerprinting system for audio matching. This wrapper simplifies the Java command-line interface and provides a clean Python API for audio fingerprinting tasks.

## What is Panako?

Panako is an acoustic fingerprinting system that can identify audio fragments in large audio databases. It's similar to Shazam but designed for:

- Finding exact recordings across different sources
- Matching audio with minor variations (compression, noise, etc.)
- Building custom audio recognition systems
- Copyright detection and duplicate finding

## Why Use This Wrapper?

The original Panako requires complex Java commands with multiple flags. This wrapper:

- ✅ Handles all Java configuration automatically
- ✅ Provides simple Python API and CLI
- ✅ Works on macOS (including M1/M2/M3) and Linux
- ✅ Auto-configures library paths
- ✅ Simplifies batch operations
- ✅ Automatic duplicate detection (skips already-indexed files)
- ✅ Deep query mode for long recordings (segments audio to find partial matches)
- ✅ Real-time monitoring mode for stream-style processing with live match output

## Installation

### Quick Install (Recommended)

The easiest way to install is via pip:

```bash
# Install the wrapper
pip install panako-python-wrapper

# Install system dependencies (if not already installed)
# macOS:
brew install openjdk@17 lmdb ffmpeg

# Ubuntu/Debian:
sudo apt install openjdk-17-jdk liblmdb-dev ffmpeg

# Run setup to download and build Panako
panako setup

# Verify installation
panako verify

# Start using!
panako store ~/Music
panako query ~/unknown_song.wav
```

The `setup` command automatically:
- Checks for required dependencies (Java, LMDB)
- Clones Panako from GitHub to `~/.panako/Panako/`
- Builds Panako with Gradle (takes 2-5 minutes on first run)

### Manual Installation

If you prefer manual control or already have Panako installed, you can set it up manually.

#### Project Structure

This wrapper works alongside Panako as separate projects. We recommend creating a parent directory to hold both repositories:

```
audio-fingerprinting/          # Parent directory (choose any name you like)
├── Panako/                    # Joren Six's Panako (Java audio fingerprinting engine)
└── panako-python-wrapper/     # This Python wrapper
```

This structure allows you to:
- Keep the projects separate (different repositories, licenses, update cycles)
- Use a simple relative path: `export PANAKO_DIR=../Panako`
- Maintain a clean, explicit setup

### Prerequisites

- Python 3.7+
- Java 17+
- Git

### macOS Installation

#### 1. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Install Dependencies
```bash
# Install Java 17
brew install openjdk@17

# Add Java to PATH (add to ~/.zshrc or ~/.bash_profile)
# For Apple Silicon (M1/M2/M3):
export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

# For Intel Macs:
# export PATH="/usr/local/opt/openjdk@17/bin:$PATH"
# export JAVA_HOME="/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

# Create symlink for system Java wrappers to find this JDK (optional)
# Apple Silicon:
sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk
# Intel:
# sudo ln -sfn /usr/local/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk

# Install LMDB
brew install lmdb

# Install ffmpeg (for audio processing)
brew install ffmpeg
```

**Important:** Add the `export` lines above to your shell profile to make them persistent:
```bash
# For zsh (default on modern macOS):
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"' >> ~/.zshrc
source ~/.zshrc

# For bash:
# echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.bash_profile
# echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"' >> ~/.bash_profile
# source ~/.bash_profile
```

**Verify Java installation:**
```bash
java -version
# Should show: openjdk version "17.x.x"
```

#### 3. Create Project Directory and Install Both Repositories

```bash
# Create parent directory (choose any name you like)
mkdir -p ~/audio-fingerprinting
cd ~/audio-fingerprinting

# Clone Panako repository
git clone https://github.com/JorenSix/Panako.git
cd Panako

# Make Gradle wrapper executable (may be needed after cloning)
chmod +x gradlew

# Build Panako
./gradlew shadowJar

# Verify build
ls build/libs/panako-*-all.jar

# Return to parent directory
cd ..

# Clone this wrapper repository
git clone https://github.com/SynthAether/panako-python-wrapper.git
cd panako-python-wrapper

# Make panako.py executable
chmod +x panako.py
```

> **Note:** If you get a "Permission denied" error when running `./gradlew`, the executable bit may have been lost during cloning. Run `chmod +x gradlew` first.

> **Note:** The first time you run `./gradlew shadowJar`, Gradle will download dependencies from the internet. This requires an active internet connection and may take a few minutes (~50-100MB download, 2-5 minutes build time).

#### 4. Set PANAKO_DIR and Verify Installation

```bash
# From within the panako-python-wrapper directory:
export PANAKO_DIR=../Panako

# Verify the setup
python3 panako.py verify
```

> **Important:** The `export PANAKO_DIR=../Panako` command sets the path for your current terminal session only. This is intentional - it keeps your environment clean and makes the setup explicit. You'll need to run this command each time you open a new terminal and want to use the wrapper.

> **Note:** The wrapper automatically configures library paths for LMDB and Java on macOS (via `DYLD_LIBRARY_PATH`), so you typically don't need to set these manually.

#### 5. Quick Start

```bash
# Each time you start a new terminal session, from the panako-python-wrapper directory:
cd ~/audio-fingerprinting/panako-python-wrapper
export PANAKO_DIR=../Panako

# Build your database
python3 panako.py store ~/Music

# Query a file
python3 panako.py query ~/unknown_song.wav

# Check what's indexed
python3 panako.py stats
```

### Ubuntu/Debian Installation

#### 1. Install Dependencies
```bash
# Update package list
sudo apt update

# Install Python 3 (if not already installed)
sudo apt install python3 python3-venv

# Install Java 17
sudo apt install openjdk-17-jdk

# Install LMDB
sudo apt install liblmdb-dev

# Install ffmpeg
sudo apt install ffmpeg

# Install build tools
sudo apt install git
```

> **Note:** The wrapper uses only Python standard library modules, so no additional Python packages or virtual environment are required. If you prefer to use a virtualenv for isolation, you can create one with `python3 -m venv .venv && source .venv/bin/activate`, but it's entirely optional.

#### 2. Set JAVA_HOME
```bash
# Add to ~/.bashrc
# For AMD64/x86_64 systems:
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc

# For ARM64/aarch64 systems (e.g., Raspberry Pi, AWS Graviton):
# echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64' >> ~/.bashrc

source ~/.bashrc
```

**Verify Java installation:**
```bash
java -version
# Should show: openjdk version "17.x.x"
```

#### 3. Create Project Directory and Install Both Repositories

```bash
# Create parent directory (choose any name you like)
mkdir -p ~/audio-fingerprinting
cd ~/audio-fingerprinting

# Clone Panako repository
git clone https://github.com/JorenSix/Panako.git
cd Panako

# Make Gradle wrapper executable (may be needed after cloning)
chmod +x gradlew

# Build Panako
./gradlew shadowJar

# Verify build
ls build/libs/panako-*-all.jar

# Return to parent directory
cd ..

# Clone this wrapper repository
git clone https://github.com/SynthAether/panako-python-wrapper.git
cd panako-python-wrapper

# Make panako.py executable
chmod +x panako.py
```

> **Note:** If you get a "Permission denied" error when running `./gradlew`, the executable bit may have been lost during cloning. Run `chmod +x gradlew` first.

> **Note:** The first time you run `./gradlew shadowJar`, Gradle will download dependencies from the internet. This requires an active internet connection and may take a few minutes (~50-100MB download, 2-5 minutes build time).

#### 4. Set PANAKO_DIR and Verify Installation

```bash
# From within the panako-python-wrapper directory:
export PANAKO_DIR=../Panako

# Verify the setup
python3 panako.py verify
```

> **Important:** The `export PANAKO_DIR=../Panako` command sets the path for your current terminal session only. This is intentional - it keeps your environment clean and makes the setup explicit. You'll need to run this command each time you open a new terminal and want to use the wrapper.

> **Note:** The wrapper automatically configures library paths for LMDB and Java on Linux (via `LD_LIBRARY_PATH`), so you typically don't need to set these manually.

#### 5. Quick Start

```bash
# Each time you start a new terminal session, from the panako-python-wrapper directory:
cd ~/audio-fingerprinting/panako-python-wrapper
export PANAKO_DIR=../Panako

# Build your database
python3 panako.py store ~/Music

# Query a file
python3 panako.py query ~/unknown_song.wav

# Check what's indexed
python3 panako.py stats
```

### Windows Installation (WSL)

We recommend using Windows Subsystem for Linux (WSL2). Once WSL is set up, follow the Ubuntu/Debian installation instructions above.

## Configuration

### Setting the Panako Path

The wrapper needs to know where Panako is installed. Since both repositories are in the same parent directory, you can use a simple relative path.

**Recommended Approach (Session-Only):**
```bash
# From within the panako-python-wrapper directory:
export PANAKO_DIR=../Panako
```

This is **session-only and intentional**. It keeps your environment clean and makes the setup explicit. You'll run this command each time you open a new terminal.

**Alternative: Absolute Path (Session-Only):**
```bash
export PANAKO_DIR="$HOME/audio-fingerprinting/Panako"
```

**Alternative: Make It Permanent:**

If you prefer to make `PANAKO_DIR` permanent (not recommended, but available):
```bash
# Add to ~/.zshrc (macOS) or ~/.bashrc (Linux)
echo 'export PANAKO_DIR="$HOME/audio-fingerprinting/Panako"' >> ~/.zshrc
source ~/.zshrc
```

**Alternative: Specify in Code:**
```python
from panako import Panako
panako = Panako(panako_dir="/path/to/your/Panako")
```

**Path Resolution Order:**

The wrapper looks for Panako in this order:
1. Path passed directly to the constructor
2. `PANAKO_DIR` environment variable
3. Default: `~/Panako`

**Verify Your Configuration:**
```bash
# Always verify your setup
python3 panako.py verify
```

## Usage

### Working Directory

All commands in this section assume you're in the `panako-python-wrapper` directory and have set `PANAKO_DIR`:

```bash
cd ~/audio-fingerprinting/panako-python-wrapper
export PANAKO_DIR=../Panako
```

### Command Line Interface

#### Build Database from Audio Files
```bash
# Store a single file
python3 panako.py store /path/to/audio.wav

# Store entire directory (recursive)
python3 panako.py store /path/to/audio/directory

# Force re-index (even if already indexed)
python3 panako.py store --force /path/to/audio/directory
```

> **Note:** The `store` command automatically skips files that have already been indexed. Use `--force` to re-index them anyway. See [Duplicate Detection](#duplicate-detection) for details.

#### Query Database
```bash
# Query with a single file
python3 panako.py query /path/to/query.wav

# Batch query all files in directory
python3 panako.py batch /path/to/queries
```

#### Deep Query (for long audio files)

For long recordings that may contain multiple tracks or partial matches, use `deep-query` to segment the audio and find all matching content:

```bash
# Basic deep query (15-second segments with 2-second overlap)
python3 panako.py deep-query /path/to/long_recording.wav

# Custom segment length and overlap
python3 panako.py deep-query --segment 20 --overlap 5 /path/to/recording.wav

# Only report files matching at least 3 segments
python3 panako.py deep-query --min-segments 3 /path/to/recording.wav

# Show per-segment match details
python3 panako.py deep-query --details /path/to/recording.wav
```

**Options:**
- `--segment <seconds>` - Length of each segment (default: 15)
- `--overlap <seconds>` - Overlap between segments (default: 2)
- `--min-segments <n>` - Minimum segments to match (default: 1)
- `--details` - Show which file matched each segment

See [Deep Query](#deep-query) for detailed documentation.

#### Real-time Monitoring

For processing audio files as continuous streams with real-time match reporting:

```bash
# Monitor an audio file (reports matches as they are detected)
python3 panako.py monitor /path/to/audio_stream.wav
```

See [Real-time Monitoring](#real-time-monitoring) for detailed documentation.

#### Database Management
```bash
# Show database statistics
python3 panako.py stats

# List cached fingerprint files
python3 panako.py list

# Delete entries
python3 panako.py delete /path/to/audio.wav

# Clear entire database (with confirmation)
python3 panako.py clear
```

#### Initialize Manifest (for existing databases)
```bash
# Mark files as already indexed (without re-processing)
python3 panako.py init-manifest /path/to/already/indexed/folder
```

Use this when you have files already in the database and want to set up duplicate detection. See [Duplicate Detection](#duplicate-detection) for details.

#### Verify Installation
```bash
python3 panako.py verify
```

#### Get Help
```bash
python3 panako.py --help
```

#### Supported Audio Formats
The wrapper processes **WAV, MP3, FLAC, OGG, M4A, AAC, WMA** formats. WAV files work out of the box. Other formats (MP3/FLAC/etc) require ffmpeg to be installed.

### Python API

#### Basic Usage
```python
from panako import Panako

# Initialize (uses PANAKO_DIR environment variable or default ~/Panako)
panako = Panako()

# Or specify Panako directory explicitly
panako = Panako(panako_dir="/path/to/Panako")

# Store audio files (skips already-indexed files)
panako.store("/path/to/reference/audio")

# Force re-index even if already indexed
panako.store("/path/to/reference/audio", force=True)

# Mark files as indexed without processing (for existing databases)
panako.init_manifest("/path/to/already/indexed/folder")

# Query
panako.query("/path/to/query.wav")

# Query with custom threshold (lower = more matches, default: 30)
panako.query("/path/to/query.wav", threshold=15)

# Show statistics
panako.stats()
```

#### Batch Processing
```python
from panako import Panako

panako = Panako()

# Build database from reference library
print("Building database...")
panako.store("/path/to/music/library")

# Show statistics
panako.stats()

# Query all test files
print("\nTesting queries...")
panako.batch_query("/path/to/test/queries")

# Batch query with custom threshold
panako.batch_query("/path/to/test/queries", threshold=15)
```

#### Managing Database
```python
from panako import Panako

panako = Panako()

# Delete specific files
panako.delete("/path/to/old/audio.wav")

# Clear database (requires confirmation)
panako.clear(confirm=True)

# Clear without confirmation (careful!)
panako.clear(confirm=False)
```

## Example Use Cases

### 1. Music Recognition System
```python
from panako import Panako

# Initialize system
panako = Panako()

# Build reference database from your music library
panako.store("/home/music/library")

# Later: identify unknown audio clips
result = panako.query("/home/downloads/unknown_song.wav")
```

### 2. Copyright Detection
```python
from panako import Panako

panako = Panako()

# Index copyrighted material
panako.store("/media/copyrighted_content")

# Check uploads for matches
panako.batch_query("/uploads/user_content")
```

### 3. Duplicate Detection
```python
from panako import Panako

panako = Panako()

# Store your audio collection
panako.store("/media/audio_archive")

# Find duplicates by querying against itself
panako.batch_query("/media/audio_archive")
```

## Understanding Results

When you query, Panako returns matches with:

- **Match path**: The matched file in your database
- **Match score**: Number of matching fingerprints (higher = better match)
- **Time offset**: Where in the reference file the match occurs
- **Time factor**: Speed variation (1.000 = identical speed)
- **Frequency factor**: Pitch variation (1.000 = identical pitch)

Example output:
```
Match: /path/to/reference/song.wav
Score: 568 matching fingerprints
Match quality: 92%
Time factor: 1.000 (perfect tempo match)
Frequency factor: 1.000 (perfect pitch match)
```

### Interpreting Match Quality

- **90-100%**: Excellent match (likely same recording)
- **80-90%**: Good match (same audio, minor variations)
- **70-80%**: Moderate match (similar content)
- **<70%**: Weak match (may be false positive)

## Tips and Tricks

### Quick Command Alias

To avoid typing `export PANAKO_DIR=../Panako` every time, create a shell alias:

```bash
# Add to ~/.zshrc (macOS) or ~/.bashrc (Linux):
alias panako='cd ~/audio-fingerprinting/panako-python-wrapper && export PANAKO_DIR=../Panako && python3 panako.py'

# Then reload your shell config:
source ~/.zshrc  # or source ~/.bashrc

# Now you can use it from anywhere:
panako verify
panako query ~/test.wav
panako stats
```

### Directory Structure Reference

**After `pip install` + `panako setup`:**

```
~/.panako/                           # All Panako data (auto-created)
├── Panako/                          # Java backend (installed by setup)
│   └── build/libs/panako-*.jar
├── indexed_files.txt                # Manifest tracking indexed files
└── dbs/                             # Fingerprint storage
    ├── olaf_cache/                  # Cached fingerprints (.tdb files)
    └── olaf_db/                     # LMDB database (paths and index)
```

**After manual installation:**

```
~/audio-fingerprinting/              # Your chosen parent directory
├── Panako/                          # The Java audio fingerprinting engine
│   ├── build/
│   │   └── libs/
│   │       └── panako-5.0-all.jar   # Built JAR file (created by Gradle)
│   ├── gradlew                      # Gradle wrapper script
│   ├── build.gradle                 # Gradle build configuration
│   └── src/                         # Java source code
│
├── panako-python-wrapper/           # This Python wrapper
│   ├── panako.py                    # Main wrapper script
│   ├── README.md                    # This documentation
│   ├── LICENSE                      # MIT License
│   ├── .gitignore
│   └── .gitattributes
│
└── ~/.panako/                       # Database directory (auto-created)
    ├── indexed_files.txt            # Manifest tracking indexed files
    └── dbs/                         # Fingerprint storage
        ├── olaf_cache/              # Cached fingerprints (.tdb files)
        └── olaf_db/                 # LMDB database (paths and fingerprint index)
```

### Running from Different Directories

**Option 1: Always navigate to wrapper directory first (Recommended)**
```bash
cd ~/audio-fingerprinting/panako-python-wrapper
export PANAKO_DIR=../Panako
python3 panako.py query ~/test.wav
```

**Option 2: Use full paths**
```bash
# From anywhere:
PANAKO_DIR="$HOME/audio-fingerprinting/Panako" python3 ~/audio-fingerprinting/panako-python-wrapper/panako.py query ~/test.wav
```

**Option 3: Add wrapper to PATH with permanent PANAKO_DIR**
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$PATH:$HOME/audio-fingerprinting/panako-python-wrapper"
export PANAKO_DIR="$HOME/audio-fingerprinting/Panako"

# Then from anywhere:
panako.py query ~/test.wav
```

## Duplicate Detection

The wrapper automatically tracks which files have been indexed to prevent duplicate processing. This is useful when:

- Adding new files to an existing database
- Re-running `store` on a directory with mixed old and new files
- Managing large audio collections across multiple sessions

### How It Works

1. When you run `store`, the wrapper checks each file against a manifest (`~/.panako/indexed_files.txt`)
2. Files already in the manifest are skipped automatically
3. Successfully indexed files are added to the manifest
4. The `delete` and `clear` commands also update the manifest

### Commands

```bash
# Store command automatically skips already-indexed files
python3 panako.py store ~/Music
# Output: "Skipping 500 already-indexed files (use --force to re-index)"
# Only processes new files

# Force re-index everything (ignores manifest)
python3 panako.py store --force ~/Music

# Initialize manifest for files already in database
# (Use this once if you have an existing database)
python3 panako.py init-manifest ~/Music
```

### Setting Up for an Existing Database

If you already have files indexed in Panako and want to enable duplicate detection:

```bash
# Mark your already-indexed folder as "done"
python3 panako.py init-manifest /path/to/already/indexed/folder

# Now you can safely add new folders - duplicates will be skipped
python3 panako.py store /path/to/new/folder
```

### Manifest File Location

The manifest is stored at `~/.panako/indexed_files.txt`. It's a simple text file with one file path per line. You can:

- View it: `cat ~/.panako/indexed_files.txt`
- Count entries: `wc -l ~/.panako/indexed_files.txt`
- Clear it manually: `rm ~/.panako/indexed_files.txt`

> **Note:** The `clear` command automatically deletes the manifest along with the database.

## Deep Query

The `deep-query` command is designed for matching long audio recordings (e.g., from videocassettes, analog tapes, or DJ mixes) against your database. It segments the audio into overlapping chunks and queries each segment independently, then consolidates the results.

### When to Use Deep Query

- **Long recordings** - Query files that are several minutes or hours long
- **Mixed content** - Recordings that contain multiple tracks, dialog, or sound effects
- **Partial matches** - When only portions of the query might match database entries
- **Videocassette/tape archives** - Audio extracted from video sources with edits and transitions

### How It Works

1. **Segmentation** - The audio file is split into overlapping segments (default: 15 seconds with 2-second overlap)
2. **Individual queries** - Each segment is queried against the database
3. **Consolidation** - Results are grouped by matched file, counting how many segments matched
4. **Ranking** - Files are ranked by number of matching segments (more segments = higher confidence)

### Example Output

```
================================================================================
Deep Query: videocassette_side_a.wav
Duration: 45:32 | Segment: 15s | Overlap: 2s
================================================================================

Segmenting audio... created 210 segments

Querying segments:
  [1/210] 0:00-0:15... ✓ 1 match(es)
  [2/210] 0:13-0:28... ✓ 1 match(es)
  ...

================================================================================
RESULTS: 5 file(s) matched (min 1 segment(s))
================================================================================

1. MyArtist-Sky_on_Fire.wav
   Path: /Users/user01/Data/MyArtist/ref/1981/track01.wav
   Segments: 18/210 (8.6%)
   Total score: 4523 fingerprints
   Matched at: 2:15-6:45

2. MyArtist-Blues.wav
   Path: /Users/user01/Data/MyArtist/ref/1982/track05.wav
   Segments: 12/210 (5.7%)
   Total score: 2891 fingerprints
   Matched at: 15:30-18:45, 32:00-34:30
```

### Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `--segment <seconds>` | 15 | Length of each audio segment |
| `--overlap <seconds>` | 2 | Overlap between consecutive segments |
| `--min-segments <n>` | 1 | Minimum segments required to report a match |
| `--details` | off | Show which database file matched each segment |

### Choosing Parameters

**Segment Length (`--segment`)**
- **Shorter (10-15s)**: Better for finding short clips, more segments to process
- **Longer (20-30s)**: Faster processing, may miss short matches
- Recommendation: Start with 15s, adjust based on your content

**Overlap (`--overlap`)**
- Prevents missing matches that span segment boundaries
- 2-5 seconds is usually sufficient
- Higher overlap = more segments = slower but more thorough

**Minimum Segments (`--min-segments`)**
- Filter out weak/accidental matches
- Use `--min-segments 2` or higher to reduce false positives
- Use `1` (default) when you want to catch every possible match

### Edge Cases

**Short audio files:**
- If the audio file is shorter than the segment length (e.g., a 10-second file with 15-second segments), the entire file is used as a single segment
- Files shorter than 3 seconds are rejected with an error (too short for reliable fingerprinting)
- The wrapper automatically detects this and informs you: "File is shorter than segment length, using entire file as a single query segment"

**When to use regular `query` vs `deep-query`:**
- Use `query` for short clips (< 30 seconds) or when you expect a full match
- Use `deep-query` for longer recordings or when you expect partial matches
- For very short files, both commands will work, but `query` is simpler

### Python API

```python
from panako import Panako

panako = Panako()

# Basic deep query
results = panako.deep_query("/path/to/long_recording.wav")

# With custom parameters
results = panako.deep_query(
    "/path/to/recording.wav",
    segment_length=20,
    overlap=5,
    min_segments=2,
    show_details=True,
    threshold=15  # Lower = more matches (default: 30)
)

# Process results
for match in results:
    print(f"{match['path']}: {match['segment_count']}/{match['total_segments']} segments")
```

## Real-time Monitoring

The `monitor` command processes audio files as continuous streams, reporting matches in real-time as they are detected. This is useful for monitoring long recordings, broadcast captures, or any scenario where you want to see matches as they occur rather than waiting for the full file to process.

### When to Use Monitor

- **Long recordings** - Process multi-hour recordings and see matches as they're found
- **Broadcast captures** - Monitor recorded radio/TV streams for music identification
- **Studio monitoring** - Process tape archive recordings with real-time feedback
- **Simulated live monitoring** - Capture audio to a file, then monitor it

### How It Works

1. **Stream processing** - Panako processes the audio file as a continuous stream
2. **Chunked fingerprinting** - Audio is fingerprinted in ~25-second chunks with 5-second overlap
3. **Real-time matching** - Each chunk is matched against the database as it's processed
4. **Live reporting** - Matches are printed to the console immediately when detected

### Usage

```bash
# Monitor an audio file (required)
python3 panako.py monitor /path/to/audio_stream.wav
```

Press `Ctrl+C` to stop monitoring before the file completes.

### Live Microphone Monitoring

Panako doesn't support direct microphone input. For live monitoring scenarios, first capture audio to a file using ffmpeg:

```bash
# macOS - capture 5 minutes from microphone
ffmpeg -f avfoundation -i ":0" -t 300 recording.wav

# Linux - capture 5 minutes from microphone
ffmpeg -f pulse -i default -t 300 recording.wav

# Then monitor the recording
python3 panako.py monitor recording.wav
```

For continuous live monitoring, you can capture in one terminal and monitor in another:

```bash
# Terminal 1: Continuous capture (overwrites file every 5 minutes)
while true; do ffmpeg -y -f avfoundation -i ":0" -t 300 /tmp/live_capture.wav; done

# Terminal 2: Monitor the captures
python3 panako.py monitor /tmp/live_capture.wav
```

### Example Output

```
================================================================================
Real-time Audio Monitor
================================================================================

Source: /path/to/broadcast_recording.wav

Processing audio stream... (Press Ctrl+C to stop)

--------------------------------------------------------------------------------
1;1;query;0.00;25.00;/path/to/music/song.wav;123;45.20;70.20;542;1.000;1.000
1;1;query;20.00;45.00;/path/to/music/another_song.wav;456;0.00;25.00;389;1.000;1.000
...
```

### Python API

```python
from panako import Panako

panako = Panako()

# Monitor an audio file (required)
panako.monitor("/path/to/audio_stream.wav")

# Monitor with custom threshold (lower = more matches)
panako.monitor("/path/to/audio_stream.wav", threshold=15)
```

### Monitor vs Query vs Deep Query

| Feature | `query` | `deep-query` | `monitor` |
|---------|---------|--------------|-----------|
| Input | Audio file | Audio file | Audio file |
| Processing | Full file, then results | Segments file, consolidates | Stream, real-time output |
| Use case | Identify a file | Find partial matches | See matches as they occur |
| Output | Final results | Consolidated summary | Live match stream |

## Expand Matches (Iterative Discovery)

The `expand` command is designed for iterative match discovery. When you have a folder of **confirmed matches** (files that are all the same piece of music from different sources), you can use them as "seeds" to find MORE undetected instances in your database.

### Why Use Expand?

When working with audio archives (e.g., videocassettes, tape recordings, broadcast captures), you often find the same piece of music recorded multiple times from different sources. Each recording may have:

- Different audio quality or compression
- Different start/end points
- Background noise or room acoustics
- Speed or pitch variations

Because of these variations, a single query might not find all instances. The `expand` command solves this by:

1. Using multiple confirmed matches as query seeds
2. Running deep-query on each seed file
3. Filtering out files already in your confirmed folder
4. Showing only NEW potential matches you haven't found yet
5. Ranking results by confidence (how many seeds matched the same file)

### When to Use Expand

- **After initial discovery** - You've found a few matches manually and want to find more
- **Building complete collections** - Ensuring you've found all instances of a piece
- **Cross-referencing sources** - Different recordings might match different database entries

### Usage

```bash
# Basic usage - expand from a folder of confirmed matches
python3 panako.py expand ./found/comet/segment04/

# With custom threshold (lower = more matches)
python3 panako.py expand --threshold 15 ./found/comet/segment04/

# With custom segment settings
python3 panako.py expand --segment 20 --overlap 5 ./found/track01/

# Save results to a report file
python3 panako.py expand --report results.txt ./found/comet/segment04/
```

### Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `--threshold <n>` | 30 | Match threshold (lower = more matches) |
| `--segment <seconds>` | 15 | Length of each audio segment |
| `--overlap <seconds>` | 2 | Overlap between consecutive segments |
| `--min-segments <n>` | 1 | Minimum segments required to report a match |
| `--report <file>` | none | Save results to a text file |

### Example Workflow

```bash
# 1. You've manually confirmed these files are all the same piece:
ls ./found/comet/segment04/
# Vangelis-Cosmos-01-Comet-1a.wav
# Vangelis-Cosmos-02-Comet-2b.wav
# Vangelis-Cosmos-04-Comet-4d.wav
# Vangelis-Cosmos-12-Children-Of-Stars.wav

# 2. Use expand to find more instances
python3 panako.py expand --threshold 15 ./found/comet/segment04/

# 3. Review the new matches found
# 4. Manually verify and add confirmed matches to the folder
# 5. Repeat to find even more!
```

### Example Output

```
================================================================================
Expand Matches: segment04
================================================================================

Seed files: 5
Known stems: 5
Settings: segment=15s, overlap=2s, min_segments=1, threshold=15

--------------------------------------------------------------------------------
[1/5] Querying: Vangelis-Cosmos-01-Comet-1a.wav
--------------------------------------------------------------------------------
  Found 8 matches, 3 new (not in seed folder)

--------------------------------------------------------------------------------
[2/5] Querying: Vangelis-Cosmos-02-Comet-2b.wav
--------------------------------------------------------------------------------
  Found 6 matches, 2 new (not in seed folder)

...

================================================================================
EXPANSION RESULTS: 7 new file(s) discovered
================================================================================

1. Vangelis-Cosmos-Special-Edition-Track05
   Path: /Users/user01/Data/Vangelis/ref/special-edition/track05.wav
   Confidence: matched by 4/5 seeds
   Total score: 12453 fingerprints

2. Vangelis-Other-Album-Track12
   Path: /Users/user01/Data/Vangelis/ref/other-album/track12.wav
   Confidence: matched by 3/5 seeds
   Total score: 8921 fingerprints

3. Unknown-Recording-Segment03
   Path: /Users/user01/Data/archive/tape-recordings/segment03.wav
   Confidence: matched by 2/5 seeds
   Total score: 4532 fingerprints
```

### How Confidence is Calculated

- **"matched by 4/5 seeds"** means 4 out of 5 seed files found this match
- Higher seed count = higher confidence that it's the same piece
- Files matched by multiple seeds are ranked higher in results

### Python API

```python
from panako import Panako

panako = Panako()

# Basic expand
results = panako.expand("./found/comet/segment04/")

# With custom parameters
results = panako.expand(
    "./found/comet/segment04/",
    segment_length=20,
    overlap=5,
    min_segments=1,
    threshold=15,
    report_file="results.txt"
)

# Process results
for match in results:
    print(f"{match['stem']}: matched by {match['seed_count']} seeds")
    print(f"  Path: {match['path']}")
```

## Troubleshooting

### Java Not Found

**Error:** `java: command not found`

**Solution:**
```bash
# macOS (Apple Silicon)
brew install openjdk@17
export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

# macOS (Intel)
brew install openjdk@17
export PATH="/usr/local/opt/openjdk@17/bin:$PATH"
export JAVA_HOME="/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

# Ubuntu/Debian
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64  # or java-17-openjdk-arm64 for ARM
```

### LMDB Library Not Found

**Error:** `UnsatisfiedLinkError: liblmdb.dylib` or `liblmdb.so`

**Solution:**
```bash
# macOS
brew install lmdb

# Ubuntu/Debian
sudo apt install liblmdb-dev
```

### Panako JAR Not Found

**Error:** `FileNotFoundError: Panako JAR not found`

**Solution:**
```bash
# Rebuild Panako
cd ~/audio-fingerprinting/Panako
./gradlew clean shadowJar

# Verify the JAR was created
ls build/libs/panako-*-all.jar
```

### PANAKO_DIR Points to Wrong Directory

**Error:** `PANAKO_DIR should point to Panako installation, not this wrapper`

**Solution:**
```bash
# Make sure you're in the wrapper directory
cd ~/audio-fingerprinting/panako-python-wrapper

# Set PANAKO_DIR to the sibling Panako directory
export PANAKO_DIR=../Panako

# Verify
python3 panako.py verify
```

### Module Access Warnings

**Warning:** `Unable to make field ... accessible`

**Solution:** These warnings are handled automatically by the wrapper with the `--add-opens` flags. If you still see them, ensure you're using Java 17 or higher:
```bash
java -version
# Should show version 17 or higher
```

### Permission Denied on gradlew

**Error:** `Permission denied: ./gradlew`

**Solution:**
```bash
cd ~/audio-fingerprinting/Panako
chmod +x gradlew
./gradlew shadowJar
```

## Performance Tips

### Large Databases

For databases with 10,000+ files:
- Use SSD storage for the database directory (`~/.panako/dbs`)
- Increase Java heap size for very large queries by modifying Panako's configuration
- Consider splitting into multiple smaller databases by category or time period

### Network and Build Time

- First Panako build requires internet connection (downloads ~50-100MB)
- Build time: 2-5 minutes on first run, <10 seconds on subsequent runs
- No internet needed after initial build

## Advanced Configuration

### Custom Panako Settings

Panako's configuration file is located at `~/.panako/config.properties`. Key settings:

```properties
# Matching threshold (higher = stricter matching)
OLAF_HIT_THRESHOLD = 30

# Time matching tolerance (in deciseconds)
OLAF_MAX_DELTA_T = 300

# Fingerprint sampling rate
OLAF_SAMPLE_RATE = 16000

# Cache fingerprints for faster repeated queries
OLAF_CACHE_TO_FILE = TRUE
```

### Adjusting Match Sensitivity

To make matching more or less strict, edit `~/.panako/config.properties`:

```properties
# More strict matching (fewer false positives, may miss some matches)
OLAF_HIT_THRESHOLD = 50

# More permissive matching (more matches, may include false positives)
OLAF_HIT_THRESHOLD = 20
```

After changing settings, restart your queries for changes to take effect.

## Project Structure

```
panako-python-wrapper/
├── panako.py                    # Main wrapper class and CLI
├── README.md                    # This documentation file
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
└── .gitattributes               # Git attributes
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your PR:
- Maintains compatibility with both macOS and Linux
- Includes appropriate error handling
- Updates documentation if adding new features
- Follows the existing code style

## Credits

- **Panako**: Created by Joren Six - https://github.com/JorenSix/Panako
- **This Wrapper**: Python interface for easier usage
- **Contributors**: See GitHub contributors page

## License

MIT License - see [LICENSE](LICENSE) file for details.

Panako itself is licensed under AGPL v3. This wrapper is a separate work under MIT license.

## Related Projects

- [Panako](https://github.com/JorenSix/Panako) - The underlying audio fingerprinting system
- [Chromaprint](https://acoustid.org/chromaprint) - Alternative fingerprinting library
- [Dejavu](https://github.com/worldveil/dejavu) - Python-based audio fingerprinting
- [Audfprint](https://github.com/dpwe/audfprint) - Audio fingerprinting using peak landmarks

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/SynthAether/panako-python-wrapper/issues)
- **Panako Documentation**: https://panako.be/
- **Discussions**: Open a discussion for questions and ideas
- **Panako Support**: For Panako-specific issues, see [Panako's GitHub](https://github.com/JorenSix/Panako)
