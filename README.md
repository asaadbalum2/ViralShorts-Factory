# 🎬 ViralShorts-Shorts

**Autonomous "Would You Rather" Video Generator for YouTube Shorts**

Generate engaging, viral-ready "Would You Rather" videos automatically using a **100% free tech stack**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-$0-brightgreen?style=flat-square)

## 🚀 Features

- **Zero-Cost**: Uses Edge-TTS (free Microsoft voices) + MoviePy
- **Vertical Format**: Perfect 1080x1920 for YouTube Shorts, TikTok, Reels
- **Engaging UI**: Split-screen with VS circle, countdown, and percentage reveal
- **Batch Generation**: Create multiple videos at once
- **Customizable**: Easy to modify colors, fonts, timing

## 📁 Project Structure

```
ViralShorts-Shorts/
├── script.py           # Main video generator
├── questions.json      # Your "Would You Rather" questions
├── requirements.txt    # Python dependencies
├── assets/
│   ├── backgrounds/    # Background videos (Minecraft parkour, etc.)
│   ├── sfx/            # Sound effects (tick.mp3, ding.mp3)
│   └── fonts/          # Custom fonts (optional)
└── output/             # Generated videos go here
```

## 🛠️ Installation

### Prerequisites

1. **Python 3.10+**
2. **FFmpeg** (required for video processing)
   - Windows: `winget install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
   - Mac: `brew install ffmpeg`
3. **ImageMagick** (required for text rendering)
   - Windows: Download from [imagemagick.org](https://imagemagick.org/script/download.php)
   - Linux: `sudo apt install imagemagick`
   - Mac: `brew install imagemagick`

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ViralShorts-Shorts.git
cd ViralShorts-Shorts

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Add Background Videos

Download some satisfying background videos and place them in `assets/backgrounds/`:

**Free sources:**
- [Pexels](https://www.pexels.com/search/videos/satisfying/) - Satisfying/ASMR videos
- [Pixabay](https://pixabay.com/videos/search/minecraft/) - Gaming footage
- Search YouTube for "free stock Minecraft parkour footage"

### Add Sound Effects (Optional)

Add to `assets/sfx/`:
- `tick.mp3` - Countdown tick sound
- `ding.mp3` - Reveal sound

Free sources: [Freesound.org](https://freesound.org/)

## 📝 Usage

### Generate a Single Video

```bash
python script.py
```

### Generate Multiple Videos (Batch)

```bash
python script.py --batch 10  # Generate 10 videos
```

### Help

```bash
python script.py --help
```

## 📋 Question Format

Edit `questions.json` to add your own questions:

```json
[
  {
    "option_a": "Have $1 million today",
    "option_b": "Have $10 million in 10 years",
    "percentage_a": 42
  },
  {
    "option_a": "Be able to fly",
    "option_b": "Be able to read minds",
    "percentage_a": 55
  }
]
```

- `option_a`: First choice
- `option_b`: Second choice
- `percentage_a`: What percentage chose option A (for the reveal)

## 🎨 Customization

Edit the configuration section in `script.py`:

```python
# Colors (RGB tuples)
OPTION_A_COLOR = (220, 53, 69)   # Red
OPTION_B_COLOR = (0, 123, 255)   # Blue
VS_CIRCLE_COLOR = (255, 193, 7)  # Yellow/Gold

# Voice
VOICE = "en-US-ChristopherNeural"  # Change voice
VOICE_RATE = "-5%"                  # Speed adjustment

# Video
VIDEO_FPS = 24
VIDEO_DURATION = 60  # Max duration in seconds
```

### Available Voices

Some popular Edge-TTS voices:
- `en-US-ChristopherNeural` (Male, American)
- `en-US-JennyNeural` (Female, American)
- `en-GB-RyanNeural` (Male, British)
- `en-AU-WilliamNeural` (Male, Australian)

List all voices: `edge-tts --list-voices`

## 🚀 Deployment (Oracle Cloud Free Tier)

1. Create an Oracle Cloud account (Always Free tier)
2. Launch an ARM instance (VM.Standard.A1.Flex)
3. SSH into the instance and run:

```bash
# Update and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip ffmpeg imagemagick git -y

# Clone and setup
git clone https://github.com/YOUR_USERNAME/ViralShorts-Shorts.git
cd ViralShorts-Shorts
pip3 install -r requirements.txt

# Run
python3 script.py --batch 10
```

## 📊 Scaling Strategy

1. **Content Variety**: Create multiple `questions.json` files for different niches
2. **Multiple Channels**: Deploy multiple instances for different YouTube channels
3. **Scheduling**: Use cron jobs to generate videos automatically
4. **A/B Testing**: Track which question types perform best

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

## 📄 License

MIT License - feel free to use commercially!

---

**Made with ❤️ for the hustle**

