# Arena Shooter 2D - Robot Battle

A top-down 2D arena shooter game built with Python and Pygame. Fight waves of robot enemies, unlock weapons, and survive! Now with online multiplayer!

## How to Play

### Controls
| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move |
| Mouse | Aim |
| Left Click | Shoot / Throw Grenade |
| Q | Switch Weapon |
| R | Reload |
| H | Use Medkit (heals to full HP) |
| Enter | Knife Attack (when knife equipped) |
| TAB | Open Shop |
| ESC | Return to Menu |

### Player 2 Controls (Local Multiplayer)
| Key | Action |
|-----|--------|
| IJKL | Move |
| Numpad 1-9 | Aim (8 directions) |
| Numpad 0 | Shoot |
| O | Switch Weapon |
| P | Reload |

### Weapons
**Starting Weapons:**
- **Rifle** - Balanced automatic weapon (30 rounds, 5 reloads)
- **Handgun** - Fast firing pistol (40 rounds, 4 reloads)
- **Knife** - Melee weapon, no ammo needed
- **Grenade** - Explosive, area damage (10 grenades)

**Shop Weapons:**
- **Shotgun** - Spread shot, high close-range damage (30 shells) - *10 coins*
- **RPG** - Rocket launcher with explosions (1 rocket, 10 reloads) - *50 coins*
- **Dual Pistols** - Fast firing golden pistols (60 rounds) - *60 coins*
- **Throwing Knives** - Silent ranged attack (20 knives, spinning effect) - *70 coins*
- **Flamethrower** - Continuous fire stream (100 fuel) - *80 coins*
- **Medkit** - Heals to full HP, 3 charges - *90 coins*
- **Crossbow** - High damage bolts (15 bolts, 80 damage) - *100 coins*
- **Freeze Ray** - Slows enemies for 2 seconds (40 ammo) - *110 coins*
- **Laser Gun** - Super fast green laser (50 ammo) - *120 coins*
- **Electric Gun** - Chain lightning hits nearby enemies (30 ammo) - *140 coins*
- **Sniper** - Headshot bonus, 150 damage (5 rounds) - *150 coins*
- **Minigun** - Massive ammo capacity, very fast fire (200 rounds) - *200 coins*

### Game Modes

#### Solo Modes
1. **Easy** - 8 robots, low damage
2. **Medium** - 15 robots, moderate difficulty
3. **Hard** - 25 robots, high damage and speed
4. **Impossible** - 5 waves + BOSS fight!

#### Local Multiplayer
- **[C] Co-op** - Team up with Player 2 against robots
- **[V] 1v1 PvP** - Fight against Player 2 (split-screen)

#### Online Multiplayer
- **[0] Online Co-op** - Team up with a friend online against robots
- **[P] Online PvP** - Fight against a friend online (1v1)

### Maps
Choose from 5 different map layouts:
- **Random** - Procedurally generated obstacles
- **Arena** - Central arena with surrounding walls
- **Corridors** - Narrow hallways and rooms
- **Fortress** - Four corner fortresses with center cross
- **Open** - Mostly open space with few pillars

### Enemy Robot Types
- **Gun Bots** (Red) - Standard robots with ranged attacks
- **Knife Bots** (Dark red) - Fast melee-only robots, 20% faster
- **Throwing Knife Bots** (Silver) - Ranged attackers with spinning knives, high damage
- **Dual Pistol Bots** (Gold) - Fast bots that shoot two bullets at once, 10% faster

### Tips
- Use cover! Hide behind obstacles to avoid enemy fire
- Knife bots are faster but can only melee - keep your distance!
- Watch out for gold dual pistol bots - they're fast and shoot twice!
- Save coins to buy powerful weapons from the shop
- The minimap (bottom-right) shows enemy positions
- Reload before engaging large groups
- Sniper headshots deal 150 damage (red dot appears on enemies)
- In co-op, game continues if one player dies (other can still win!)

---

## Running the Game

### Desktop Version (Python)
Requires Python 3.8+ and Pygame.

```bash
# Install dependencies
pip install pygame

# Run the game
cd /path/to/ani-games
python aarav_games.py
```

### Web Version
The web version is pre-built in the `build/web` folder.

**Test locally:**
```bash
cd build/web
python3 -m http.server 8000
```
Then open http://localhost:8000 in your browser.

**Play online:** https://akmrsingh.itch.io/2d-shooter-game

---

## Deploying to the Web

### Option 1: itch.io (Recommended - Free)

1. **Create account** at https://itch.io

2. **Create new project:**
   - Click profile icon → "Upload new project"
   - Title: "Arena Shooter 2D - Robot Battle"
   - Kind of project: **HTML**
   - Classification: Games

3. **Upload files:**
   - Upload all files from `build/web/` folder:
     - `index.html`
     - `favicon.png`
     - `web_build.apk`
   - Check **"This file will be played in the browser"**

4. **Configure embed:**
   - Width: **1400**
   - Height: **900**
   - Enable "Click to launch in fullscreen"

5. **Publish:**
   - Save and preview
   - Set Visibility to **Public**

Your game URL: `https://yourusername.itch.io/arena-shooter-2d`

### Option 2: GitHub Pages (Free)

1. **Create GitHub repository**

2. **Upload build files:**
   ```bash
   cd build/web
   git init
   git add .
   git commit -m "Initial web build"
   git branch -M main
   git remote add origin https://github.com/yourusername/arena-shooter.git
   git push -u origin main
   ```

3. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from branch
   - Branch: main, folder: / (root)
   - Save

Your game URL: `https://yourusername.github.io/arena-shooter/`

### Option 3: Netlify (Free)

1. Go to https://netlify.com and sign up

2. Drag and drop the `build/web` folder to deploy

3. Get your free URL instantly!

---

## Rebuilding the Web Version

If you modify the game, rebuild with:

```bash
# Install pygbag if not installed
pip install pygbag

# Build
cd /path/to/web_build
pygbag --build main.py
```

Output will be in `build/web/`

---

## Project Structure

```
ani-games/
├── aarav_games.py      # Main game (desktop + multiplayer)
├── save_data.json      # Save file (coins, unlocks)
└── web_build/
    ├── main.py         # Web-compatible version
    ├── multiplayer.js  # PeerJS multiplayer module
    ├── README.md       # This file
    └── build/
        └── web/        # Deployable web files
            ├── index.html
            ├── favicon.png
            └── web_build.apk
```

---

## Features

- 4 difficulty levels + boss fight
- 4 enemy robot types: Gun, Knife, Throwing Knife, and Dual Pistol bots
- 16 unique weapons with realistic visuals and special effects
- Special weapon effects: Freeze Ray slows enemies, Electric Gun chains to nearby targets
- Shell casings and muzzle flash effects
- Reload animations
- Healing effects with medkit
- Shop system with persistent coins (12 shop weapons)
- Minimap
- Procedurally generated music
- 5 different map layouts
- Local multiplayer (Co-op & PvP)
- Online multiplayer via WebRTC/PeerJS
- Sniper headshot system with red dot targeting

## Web Version Notes

- Progress saves during session only (resets on page refresh)
- Online multiplayer available via room codes
- Works best in Chrome/Firefox/Edge

---

## Credits

Built with Python and Pygame
Web version powered by Pygbag
Online multiplayer powered by PeerJS

Enjoy the game!
