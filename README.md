# Skill Plate Bot

A Discord bot for browsing and suggesting Skill Plates for WWE Champions.

## Commands
| Command | Description |
|--------|-------------|
| `!sp <keywords>` | Text search for plates |
| `/sp` | Browse plates (with pagination, dropdown) |
| `/sp <keywords>` | Filter plates using text search |
| `/suggest` | Guided picker (gem color → plate effect) |

## Setup
1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create a `.env` file (use `.env.example` as reference):
```
PLATE_DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
PLATE_GUILD_ID=YOUR_SERVER_ID_HERE
```

3. Run the bot:
```
python bot.py
```

## File Structure
```
Skill-Plate-Bot/
│ bot.py
│ plates.html
│ requirements.txt
│ README.md
│ .env (not committed)
│ .gitignore
└─ plates_files/
   └─ images
```
