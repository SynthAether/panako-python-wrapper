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
- ✅ Works on macOS (including M1/M2) and Linux
- ✅ Auto-configures library paths
- ✅ Simplifies batch operations

## Installation

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

# Set JAVA_HOME (add to ~/.zshrc or ~/.bash_profile)
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Install LMDB
brew install lmdb

# Install ffmpeg (for audio processing)
brew install ffmpeg
```

#### 3. Install Panako
```bash
# Clone Panako repository
git clone https://github.com/JorenSix/Panako.git
cd Panako

# Build Panako
./gradlew shadowJar

# Verify build
ls build/libs/panako-*-all.jar
```

#### 4. Install This Wrapper
```bash
# Clone this repository
git clone https://github.com/SynthAether/panako-python-wrapper.git
cd panako-python-wrapper

# Make panako.py executable
chmod +x panako.py
```

### Ubuntu/Debian Installation

#### 1. Install Dependencies
```bash
# Update package list
sudo apt update

# Install Java 17
sudo apt install openjdk-17-jdk

# Install LMDB
sudo apt install liblmdb-dev

# Install ffmpeg
sudo apt install ffmpeg

# Install build tools
sudo apt install git gradle
```

#### 2. Set JAVA_HOME
```bash
# Add to ~/.bashrc
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc
```

#### 3. Install Panako
```bash
# Clone Panako repository
git clone https://github.com/JorenSix/Panako.git
cd Panako

# Build Panako
./gradlew shadowJar

# Verify build
ls build/libs/panako-*-all.jar
```

#### 4. Install This Wrapper
```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/panako-python-wrapper.git
cd panako-python-wrapper

# Make panako.py executable
chmod +x panako.py
```

## Configuration

### Update Panako Path

Edit `panako.py` and update the default Panako directory:
```python
def __init__(self, panako_dir="/path/to/your/Panako"):
```

Or specify it when creating the instance:
```python
from panako import Panako
panako = Panako(panako_dir="/path/to/your/Panako")
```

## Usage

### Command Line Interface

#### Build Database from Audio Files
```bash
# Store a single file
python3 panako.py store /path/to/audio.wav

# Store entire directory (recursive)
python3 panako.py store /path/to/audio/directory
```

#### Query Database
```bash
# Query with a single file
python3 panako.py query /path/to/query.wav

# Batch query all files in directory
python3 panako.py batch /path/to/queries
```

#### Database Management
```bash
# Show database statistics
python3 panako.py stats

# List cached files
python3 panako.py list

# Delete entries
python3 panako.py delete /path/to/audio.wav

# Clear entire database (with confirmation)
python3 panako.py clear
```

### Python API

#### Basic Usage
```python
from panako import Panako

# Initialize
panako = Panako()

# Store audio files
panako.store("/path/to/reference/audio")

# Query
panako.query("/path/to/query.wav")

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

## Troubleshooting

### Java Not Found

**Error:** `java: command not found`

**Solution:**
```bash
# macOS
brew install openjdk@17
export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"

# Ubuntu
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### LMDB Library Not Found

**Error:** `UnsatisfiedLinkError: liblmdb.dylib`

**Solution:**
```bash
# macOS
brew install lmdb

# Ubuntu
sudo apt install liblmdb-dev
```

### Panako JAR Not Found

**Error:** `FileNotFoundError: Panako JAR not found`

**Solution:**
```bash
# Rebuild Panako
cd /path/to/Panako
./gradlew clean shadowJar
```

### Module Access Warnings

**Warning:** `Unable to make field ... accessible`

**Solution:** These are handled automatically by the wrapper. If you still see them, ensure you're using Java 17+.

## Performance Tips

### Processing Speed

- **Expected speed:** ~100-200x real-time (4-minute song processes in ~2 seconds)
- **Database queries:** Typically < 100ms per query
- **Storage:** ~5-10KB per minute of audio

### Optimizing Large Databases

For databases with 10,000+ files:
- Use SSD storage for the database directory (`~/.panako/dbs`)
- Increase Java heap size for very large queries
- Consider splitting into multiple smaller databases

## Advanced Configuration

### Custom Panako Settings

Panako's configuration is in `~/.panako/config.properties`. Key settings:
```properties
# Matching threshold
OLAF_HIT_THRESHOLD = 30

# Time matching tolerance
OLAF_MAX_DELTA_T = 300

# Fingerprint sampling rate
OLAF_SAMPLE_RATE = 16000
```

### Adjusting Match Sensitivity

To make matching more/less strict, edit `config.properties`:
```properties
# More strict (fewer false positives)
OLAF_HIT_THRESHOLD = 50

# More permissive (more matches, may include false positives)
OLAF_HIT_THRESHOLD = 20
```

## Project Structure
```
panako-python-wrapper/
├── panako.py              # Main wrapper class
├── README.md              # This file
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies (none!)
├── .gitignore            # Git ignore rules
└── examples/             # Usage examples
    ├── basic_usage.py
    └── batch_matching.py
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Credits

- **Panako**: Created by Joren Six - https://github.com/JorenSix/Panako
- **This Wrapper**: Python interface for easier usage

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [Panako](https://github.com/JorenSix/Panako) - The underlying audio fingerprinting system
- [Chromaprint](https://acoustid.org/chromaprint) - Alternative fingerprinting system
- [Dejavu](https://github.com/worldveil/dejavu) - Python-based audio fingerprinting

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/YOUR_USERNAME/panako-python-wrapper/issues)
- **Panako Documentation**: https://panako.be/
- **Discussions**: Open a discussion for questions and ideas