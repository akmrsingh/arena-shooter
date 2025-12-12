#!/usr/bin/env python3
"""
Arena Shooter 2D - Robot Battle
Top-down shooter with robot enemies (Web Version)

Controls:
- WASD/Arrow Keys: Move
- Mouse: Aim
- Left Click: Shoot/Throw Grenade
- Q: Switch Weapon
- Enter: Knife Attack
- R: Reload
- ESC: Menu

Weapons: Rifle, Handgun, Knife, Grenade, RPG (shop)
"""

import asyncio
import pygame
import math
import random
import sys
import struct
import io

# Web version - no file saving, no networking
WEB_VERSION = True

pygame.init()
# Disable mixer for web (causes issues)
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except:
    pass


def generate_boss_music():
    """Generate intense boss battle music programmatically"""
    sample_rate = 44100
    duration = 8  # 8 second loop
    num_samples = sample_rate * duration

    # Create audio buffer
    audio_data = []

    # Boss music parameters - intense and fast
    bpm = 140
    beat_duration = 60.0 / bpm
    samples_per_beat = int(sample_rate * beat_duration)

    # Bass frequencies for intense feel
    bass_notes = [55, 55, 65, 55, 55, 65, 73, 65]  # A1, A1, C2, A1, etc

    for i in range(num_samples):
        t = i / sample_rate
        beat = int(t / beat_duration) % 8

        # Heavy bass drum on beats
        bass_drum = 0
        beat_pos = (t % beat_duration) / beat_duration
        if beat_pos < 0.1:
            bass_drum = math.sin(2 * math.pi * 60 * t) * (1 - beat_pos * 10) * 0.5

        # Snare on off-beats
        snare = 0
        if beat in [1, 3, 5, 7] and beat_pos < 0.05:
            snare = random.uniform(-0.3, 0.3) * (1 - beat_pos * 20)

        # Bass synth
        bass_freq = bass_notes[beat]
        bass = math.sin(2 * math.pi * bass_freq * t) * 0.3

        # Add some grit to bass
        bass += math.sin(2 * math.pi * bass_freq * 2 * t) * 0.1

        # High intensity lead melody
        lead_freq = bass_freq * 4
        lead = math.sin(2 * math.pi * lead_freq * t) * 0.15
        lead += math.sin(2 * math.pi * lead_freq * 1.5 * t) * 0.05

        # Combine all elements
        sample = bass_drum + snare + bass + lead

        # Soft clip to prevent distortion
        sample = max(-0.9, min(0.9, sample))

        # Convert to 16-bit integer
        audio_data.append(int(sample * 32767))

    # Create stereo sound
    sound_buffer = io.BytesIO()
    for sample in audio_data:
        # Write same sample to both channels (stereo)
        sound_buffer.write(struct.pack('<hh', sample, sample))

    sound_buffer.seek(0)
    sound = pygame.mixer.Sound(buffer=sound_buffer.getvalue())
    return sound


def generate_menu_music():
    """Generate calmer menu music"""
    sample_rate = 44100
    duration = 6
    num_samples = sample_rate * duration

    audio_data = []

    # Slower, ambient feel
    for i in range(num_samples):
        t = i / sample_rate

        # Ambient pad
        pad = math.sin(2 * math.pi * 110 * t) * 0.2
        pad += math.sin(2 * math.pi * 165 * t) * 0.1
        pad += math.sin(2 * math.pi * 220 * t) * 0.1

        # Slow modulation
        mod = (math.sin(2 * math.pi * 0.5 * t) + 1) / 2
        pad *= (0.5 + mod * 0.5)

        sample = max(-0.9, min(0.9, pad))
        audio_data.append(int(sample * 32767))

    sound_buffer = io.BytesIO()
    for sample in audio_data:
        sound_buffer.write(struct.pack('<hh', sample, sample))

    sound_buffer.seek(0)
    sound = pygame.mixer.Sound(buffer=sound_buffer.getvalue())
    return sound

# Web version uses browser localStorage for persistent storage
import json as json_module
import platform

# Check if running in browser (Pyodide/Pygbag)
IS_BROWSER = platform.system() == 'Emscripten' or 'wasm' in platform.machine().lower()

# Try to import browser storage module
try:
    from platform import window
    HAS_LOCALSTORAGE = True
except:
    HAS_LOCALSTORAGE = False

# Storage keys
STORAGE_KEY_USERS = "arena_shooter_users"
STORAGE_KEY_GUEST = "arena_shooter_guest"

# Fallback in-memory storage
web_save_data = {
    "coins": 0, "has_rpg": False, "has_shotgun": False, "medkit_charges": 0, "has_sniper": False,
    "has_flamethrower": False, "has_laser": False, "has_minigun": False, "has_crossbow": False,
    "has_electric": False, "has_freeze": False, "has_dual_pistols": False, "has_throwing_knives": False
}
web_users = {}
current_user = None


def storage_get(key):
    """Get data from localStorage"""
    global HAS_LOCALSTORAGE
    try:
        if HAS_LOCALSTORAGE:
            from platform import window
            data = window.localStorage.getItem(key)
            if data:
                return json_module.loads(data)
    except Exception as e:
        print(f"Storage get error: {e}")
    return None


def storage_set(key, value):
    """Set data in localStorage"""
    global HAS_LOCALSTORAGE
    try:
        if HAS_LOCALSTORAGE:
            from platform import window
            window.localStorage.setItem(key, json_module.dumps(value))
            return True
    except Exception as e:
        print(f"Storage set error: {e}")
    return False


# Firebase cloud sync helpers
firebase_pending_result = None
firebase_result_ready = False

def firebase_available():
    """Check if Firebase is available in browser"""
    try:
        from platform import window
        return hasattr(window, 'FirebaseDB')
    except:
        return False

def firebase_call_async(method, *args):
    """Call a Firebase async method and return a promise-like object"""
    global firebase_pending_result, firebase_result_ready
    try:
        from platform import window
        if not hasattr(window, 'FirebaseDB'):
            return None

        firebase_pending_result = None
        firebase_result_ready = False

        # Get the method from FirebaseDB
        db = window.FirebaseDB
        if method == "getUser":
            promise = db.getUser(args[0])
        elif method == "createUser":
            promise = db.createUser(args[0], args[1], args[2] if len(args) > 2 else {})
        elif method == "verifyLogin":
            promise = db.verifyLogin(args[0], args[1])
        elif method == "saveProgress":
            promise = db.saveProgress(args[0], args[1])
        elif method == "userExists":
            promise = db.userExists(args[0])
        else:
            return None

        return promise
    except Exception as e:
        print(f"Firebase call error: {e}")
        return None

def firebase_sync_create_user(username, passcode, initial_data=None):
    """Synchronously create user in Firebase (non-blocking call)"""
    try:
        from platform import window
        if not hasattr(window, 'FirebaseDB'):
            return False

        data = initial_data or {}
        # Fire and forget - don't wait for result
        window.FirebaseDB.createUser(username, passcode, window.JSON.parse(json_module.dumps(data)))
        print(f"Firebase: Creating cloud account for {username}")
        return True
    except Exception as e:
        print(f"Firebase create user error: {e}")
        return False

def firebase_sync_save_progress(username, progress_data):
    """Save progress to Firebase (non-blocking call)"""
    try:
        from platform import window
        if not hasattr(window, 'FirebaseDB'):
            return False

        # Fire and forget - don't wait for result
        window.FirebaseDB.saveProgress(username, window.JSON.parse(json_module.dumps(progress_data)))
        print(f"Firebase: Saving progress for {username}")
        return True
    except Exception as e:
        print(f"Firebase save progress error: {e}")
        return False


def load_users():
    """Load all user accounts from localStorage"""
    global web_users
    stored = storage_get(STORAGE_KEY_USERS)
    if stored:
        web_users = stored
    return web_users


def save_users_to_storage():
    """Save all user accounts to localStorage"""
    global web_users
    storage_set(STORAGE_KEY_USERS, web_users)


def register_user(username, passcode):
    """Register a new user (local + cloud)"""
    global web_users
    # Reload from storage first
    load_users()

    if username in web_users:
        return False, "Username already exists"
    if len(username) < 3:
        return False, "Username too short (min 3 chars)"
    if len(passcode) < 4:
        return False, "Passcode too short (min 4 chars)"

    initial_data = {
        "coins": 0,
        "has_rpg": False,
        "has_shotgun": False,
        "medkit_charges": 0,
        "has_sniper": False,
        "has_flamethrower": False,
        "has_laser": False,
        "has_minigun": False,
        "has_crossbow": False,
        "has_electric": False,
        "has_freeze_ray": False,
        "has_dual_pistols": False,
        "has_throwing_knives": False
    }

    web_users[username] = {
        "passcode": passcode,
        **initial_data
    }
    save_users_to_storage()

    # Also create in Firebase cloud for cross-device sync
    firebase_sync_create_user(username, passcode, initial_data)

    return True, "Account created!"


def login_user(username, passcode):
    """Login a user (checks local first, then cloud)"""
    global current_user, web_users
    # Reload from storage first
    load_users()

    # First try local login
    if username in web_users:
        if web_users[username]["passcode"] != passcode:
            return False, "Wrong passcode"
        current_user = username
        return True, "Login successful!"

    # Local user not found - return message indicating cloud check might work
    # Cloud login will be attempted asynchronously
    return False, "Checking cloud..."


def login_from_cloud_data(username, passcode, cloud_data):
    """Create local user from cloud data after successful cloud login"""
    global current_user, web_users

    # Create local user with cloud data
    web_users[username] = {
        "passcode": passcode,
        "coins": cloud_data.get("coins", 0),
        "has_rpg": cloud_data.get("has_rpg", False),
        "has_shotgun": cloud_data.get("has_shotgun", False),
        "medkit_charges": cloud_data.get("medkit_charges", 0),
        "has_sniper": cloud_data.get("has_sniper", False),
        "has_flamethrower": cloud_data.get("has_flamethrower", False),
        "has_laser": cloud_data.get("has_laser", False),
        "has_minigun": cloud_data.get("has_minigun", False),
        "has_crossbow": cloud_data.get("has_crossbow", False),
        "has_electric": cloud_data.get("has_electric", False),
        "has_freeze": cloud_data.get("has_freeze_ray", False),
        "has_dual_pistols": cloud_data.get("has_dual_pistols", False),
        "has_throwing_knives": cloud_data.get("has_throwing_knives", False),
        "current_avatar": cloud_data.get("current_avatar", "default"),
        "owned_avatars": cloud_data.get("owned_avatars", ["default"])
    }
    save_users_to_storage()
    current_user = username
    print(f"Cloud login successful! Synced data for {username}")
    return True


def logout_user():
    """Logout current user"""
    global current_user
    current_user = None


def load_save():
    """Load saved data for current user from localStorage"""
    global current_user, web_users, web_save_data

    if current_user:
        # Reload users from storage
        load_users()
        if current_user in web_users:
            data = web_users[current_user]
            return (data.get("coins", 0), data.get("has_rpg", False),
                    data.get("has_shotgun", False), data.get("medkit_charges", 0),
                    data.get("has_sniper", False), data.get("has_flamethrower", False),
                    data.get("has_laser", False), data.get("has_minigun", False),
                    data.get("has_crossbow", False), data.get("has_electric", False),
                    data.get("has_freeze", False), data.get("has_dual_pistols", False),
                    data.get("has_throwing_knives", False),
                    data.get("current_avatar", "default"),
                    data.get("owned_avatars", ["default"]))

    # Guest mode - try to load guest data from storage
    guest_data = storage_get(STORAGE_KEY_GUEST)
    if guest_data:
        web_save_data = guest_data

    return (web_save_data.get("coins", 0), web_save_data.get("has_rpg", False),
            web_save_data.get("has_shotgun", False), web_save_data.get("medkit_charges", 0),
            web_save_data.get("has_sniper", False), web_save_data.get("has_flamethrower", False),
            web_save_data.get("has_laser", False), web_save_data.get("has_minigun", False),
            web_save_data.get("has_crossbow", False), web_save_data.get("has_electric", False),
            web_save_data.get("has_freeze", False), web_save_data.get("has_dual_pistols", False),
            web_save_data.get("has_throwing_knives", False),
            web_save_data.get("current_avatar", "default"),
            web_save_data.get("owned_avatars", ["default"]))


def save_game(coins, has_rpg, has_shotgun, medkit_charges, has_sniper,
               has_flamethrower=False, has_laser=False, has_minigun=False, has_crossbow=False,
               has_electric=False, has_freeze=False, has_dual_pistols=False, has_throwing_knives=False,
               current_avatar="default", owned_avatars=None):
    """Save data for current user to localStorage and Firebase cloud"""
    global current_user, web_users, web_save_data

    if owned_avatars is None:
        owned_avatars = ["default"]

    progress_data = {
        "coins": coins,
        "has_rpg": has_rpg,
        "has_shotgun": has_shotgun,
        "medkit_charges": medkit_charges,
        "has_sniper": has_sniper,
        "has_flamethrower": has_flamethrower,
        "has_laser": has_laser,
        "has_minigun": has_minigun,
        "has_crossbow": has_crossbow,
        "has_electric": has_electric,
        "has_freeze_ray": has_freeze,  # Note: Firebase uses has_freeze_ray
        "has_dual_pistols": has_dual_pistols,
        "has_throwing_knives": has_throwing_knives,
        "current_avatar": current_avatar,
        "owned_avatars": owned_avatars
    }

    if current_user:
        # Reload users first to avoid overwriting
        load_users()
        if current_user in web_users:
            web_users[current_user]["coins"] = coins
            web_users[current_user]["has_rpg"] = has_rpg
            web_users[current_user]["has_shotgun"] = has_shotgun
            web_users[current_user]["medkit_charges"] = medkit_charges
            web_users[current_user]["has_sniper"] = has_sniper
            web_users[current_user]["has_flamethrower"] = has_flamethrower
            web_users[current_user]["has_laser"] = has_laser
            web_users[current_user]["has_minigun"] = has_minigun
            web_users[current_user]["has_crossbow"] = has_crossbow
            web_users[current_user]["has_electric"] = has_electric
            web_users[current_user]["has_freeze"] = has_freeze
            web_users[current_user]["has_dual_pistols"] = has_dual_pistols
            web_users[current_user]["has_throwing_knives"] = has_throwing_knives
            web_users[current_user]["current_avatar"] = current_avatar
            web_users[current_user]["owned_avatars"] = owned_avatars
            save_users_to_storage()

            # Also sync to Firebase cloud
            firebase_sync_save_progress(current_user, progress_data)
            return True

    # Guest mode - save to guest storage (no cloud sync for guests)
    web_save_data["coins"] = coins
    web_save_data["has_rpg"] = has_rpg
    web_save_data["has_shotgun"] = has_shotgun
    web_save_data["medkit_charges"] = medkit_charges
    web_save_data["has_sniper"] = has_sniper
    web_save_data["has_flamethrower"] = has_flamethrower
    web_save_data["has_laser"] = has_laser
    web_save_data["has_minigun"] = has_minigun
    web_save_data["has_crossbow"] = has_crossbow
    web_save_data["has_electric"] = has_electric
    web_save_data["has_freeze"] = has_freeze
    web_save_data["has_dual_pistols"] = has_dual_pistols
    web_save_data["has_throwing_knives"] = has_throwing_knives
    web_save_data["current_avatar"] = current_avatar
    web_save_data["owned_avatars"] = owned_avatars
    storage_set(STORAGE_KEY_GUEST, web_save_data)
    return True


# Initialize by loading users from storage at startup
load_users()

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Map is much bigger than screen
MAP_WIDTH = 5000
MAP_HEIGHT = 5000

# Mobile detection - check for actual mobile devices (not just touch-capable desktops)
IS_MOBILE = False
IS_TOUCH_DEVICE = False
try:
    from platform import window
    # Check user agent for mobile devices
    user_agent = window.navigator.userAgent.lower()
    IS_TOUCH_DEVICE = hasattr(window, 'ontouchstart') or window.navigator.maxTouchPoints > 0
    # Only enable mobile controls for actual mobile user agents (phones/tablets)
    # This prevents desktop touch screens from getting mobile UI
    is_mobile_ua = any(x in user_agent for x in ['android', 'iphone', 'ipad', 'ipod', 'mobile', 'tablet'])
    # Only auto-enable on actual mobile devices with touch
    IS_MOBILE = is_mobile_ua and IS_TOUCH_DEVICE
except:
    pass

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 60, 60)
GREEN = (60, 200, 60)
BLUE = (60, 120, 220)
YELLOW = (220, 220, 60)
ORANGE = (255, 140, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 90, 43)
LIGHT_BLUE = (135, 206, 235)
FLOOR_COLOR = (70, 75, 80)

# Difficulty settings
DIFFICULTY = {
    "easy": {"count": 8, "health": 40, "speed": 2, "damage": 5, "fire_rate": 90, "color": GREEN, "points": 100, "coins": 1},
    "medium": {"count": 15, "health": 60, "speed": 3, "damage": 10, "fire_rate": 60, "color": YELLOW, "points": 200, "coins": 3},
    "hard": {"count": 25, "health": 100, "speed": 4, "damage": 15, "fire_rate": 40, "color": RED, "points": 300, "coins": 8},
    "impossible": {"count": 10, "health": 120, "speed": 5, "damage": 20, "fire_rate": 30, "color": (150, 0, 150), "points": 500, "coins": 15, "waves": 5, "has_boss": True},
    "pvp": {"count": 0, "health": 0, "speed": 0, "damage": 0, "fire_rate": 0, "color": WHITE, "points": 0, "coins": 0}  # No robots in PvP
}

# Avatar types - realistic character designs with body parts
AVATAR_TYPES = {
    "default": {
        "name": "T-800",
        "price": 0,  # Free default avatar
        "skin_color": (120, 120, 130),  # Metallic chrome
        "shirt_color": (20, 20, 25),  # Black leather
        "pants_color": (15, 15, 20),  # Black leather
        "hair_color": (30, 30, 35),  # Dark
        "hair_style": "short",
        "glove_color": (80, 80, 90),  # Metal hands
        "boot_color": (25, 25, 30),  # Black boots
        "accessory": "terminator",  # Special terminator look
        "eye_color": (255, 0, 0),  # Red glowing eyes
        "description": "I'll be back"
    },
    "commando": {
        "name": "Commando",
        "price": 500,
        "skin_color": (180, 140, 100),  # Darker skin
        "shirt_color": (30, 30, 35),  # Black tactical
        "pants_color": (25, 25, 30),  # Dark pants
        "hair_color": (20, 20, 20),  # Black hair
        "hair_style": "bald",
        "glove_color": (40, 40, 40),
        "boot_color": (30, 30, 30),
        "accessory": "bandana",
        "description": "Elite special forces operative"
    },
    "ninja": {
        "name": "Shadow",
        "price": 800,
        "skin_color": (220, 190, 160),  # Light skin
        "shirt_color": (20, 20, 25),  # Near black
        "pants_color": (15, 15, 20),
        "hair_color": (10, 10, 10),
        "hair_style": "hidden",
        "glove_color": (20, 20, 25),
        "boot_color": (20, 20, 25),
        "accessory": "mask",
        "description": "Silent assassin from the shadows"
    },
    "marine": {
        "name": "Marine",
        "price": 600,
        "skin_color": (200, 160, 120),
        "shirt_color": (80, 100, 80),  # Camo green
        "pants_color": (90, 110, 90),
        "hair_color": (60, 40, 20),  # Light brown
        "hair_style": "short",
        "glove_color": (100, 90, 70),  # Tan gloves
        "boot_color": (60, 50, 40),
        "accessory": "helmet",
        "description": "US Marine - Semper Fi"
    },
    "mercenary": {
        "name": "Merc",
        "price": 750,
        "skin_color": (190, 150, 110),
        "shirt_color": (100, 80, 60),  # Desert tan
        "pants_color": (90, 70, 50),
        "hair_color": (100, 80, 60),  # Sandy hair
        "hair_style": "mohawk",
        "glove_color": (80, 70, 60),
        "boot_color": (70, 60, 50),
        "accessory": "glasses",
        "description": "Gun for hire - no questions asked"
    },
    "cyborg": {
        "name": "Cyborg",
        "price": 1200,
        "skin_color": (150, 150, 160),  # Metallic skin
        "shirt_color": (60, 60, 70),  # Steel gray
        "pants_color": (50, 50, 60),
        "hair_color": (100, 100, 110),  # Silver
        "hair_style": "short",
        "glove_color": (70, 70, 80),
        "boot_color": (50, 50, 55),
        "accessory": "visor",
        "description": "Half human, half machine"
    },
    "veteran": {
        "name": "Veteran",
        "price": 1000,
        "skin_color": (200, 170, 140),
        "shirt_color": (70, 90, 70),  # Olive drab
        "pants_color": (60, 80, 60),
        "hair_color": (150, 150, 150),  # Gray hair
        "hair_style": "short",
        "glove_color": (50, 50, 50),
        "boot_color": (45, 40, 35),
        "accessory": "cigar",
        "description": "War-hardened survivor"
    },
    "arctic": {
        "name": "Arctic",
        "price": 700,
        "skin_color": (230, 210, 190),  # Pale skin
        "shirt_color": (220, 220, 230),  # White/gray camo
        "pants_color": (200, 200, 210),
        "hair_color": (200, 180, 160),  # Blonde
        "hair_style": "hidden",
        "glove_color": (180, 180, 190),
        "boot_color": (150, 150, 160),
        "accessory": "goggles",
        "description": "Cold weather specialist"
    }
}


class Avatar:
    """Realistic avatar with articulated body parts and animations"""

    def __init__(self, avatar_type="default"):
        self.avatar_type = avatar_type
        self.config = AVATAR_TYPES.get(avatar_type, AVATAR_TYPES["default"])

        # Body part sizes - larger character for better visibility
        self.head_radius = 10  # Visible head
        self.neck_length = 5
        self.torso_width = 32  # Wide torso
        self.torso_height = 30  # Tall torso
        self.shoulder_width = 38  # Broad shoulders
        self.arm_length = 26  # Long arms
        self.arm_width = 9
        self.hand_radius = 6
        self.leg_length = 24  # Long legs
        self.leg_width = 10
        self.foot_length = 12

        # Animation state
        self.walk_cycle = 0  # 0-1 for walk animation
        self.arm_angle_offset = 0  # For arm movements
        self.reload_hand_offset = (0, 0)  # Hand position during reload
        self.breathing_cycle = 0  # Subtle breathing animation

    def draw(self, screen, x, y, angle, is_firing=False, is_reloading=False,
             reload_phase=0, weapon_name="Rifle", walk_speed=0, anim_timer=0):
        """Draw the full avatar with body parts"""
        config = self.config

        # Update walk animation
        if walk_speed > 0.1:
            self.walk_cycle = (self.walk_cycle + walk_speed * 0.15) % (math.pi * 2)
        else:
            # Smoothly return to neutral
            self.walk_cycle *= 0.9

        # Subtle breathing animation
        self.breathing_cycle = (anim_timer * 0.05) % (math.pi * 2)
        breath_offset = math.sin(self.breathing_cycle) * 0.5

        # Body stays upright (facing down on screen = angle 0)
        # Only arms rotate to aim
        body_angle = 0  # Body always faces "down" on screen (top-down view)
        aim_angle = angle  # Arms aim toward mouse

        # Determine which side the character is aiming (for flipping)
        aiming_right = -math.pi/2 < aim_angle < math.pi/2

        # Draw shadow under character - simple ellipse (no surface for performance)
        pygame.draw.ellipse(screen, (30, 30, 30), (int(x - 25), int(y + 18), 50, 24))

        # Draw layers from back to front
        # 1. Back leg
        self._draw_leg(screen, x, y + 5, body_angle, is_back=True)

        # 2. Back arm (support hand for weapon)
        self._draw_arm(screen, x, y - 5, aim_angle, is_front=False, is_reloading=is_reloading,
                      reload_phase=reload_phase, weapon_name=weapon_name, anim_timer=anim_timer)

        # 3. Torso with breathing
        self._draw_torso(screen, x, y + breath_offset, body_angle)

        # 4. Neck
        self._draw_neck(screen, x, y - 10 + breath_offset)

        # 5. Head (slightly turns toward aim direction)
        head_turn = aim_angle * 0.2  # Head turns slightly toward aim
        self._draw_head(screen, x, y - 14 + breath_offset, head_turn, aim_angle, anim_timer)

        # 6. Front leg
        self._draw_leg(screen, x, y + 5, body_angle, is_back=False)

        # 7. Front arm (holding weapon) - drawn by weapon system
        # The weapon drawing functions will call draw_holding_hand

    def _draw_neck(self, screen, x, y):
        """Draw the neck connecting head to torso"""
        config = self.config
        skin = config["skin_color"]
        # Darker skin for neck shadow
        neck_color = tuple(max(0, c - 25) for c in skin)
        neck_light = tuple(min(255, c + 10) for c in skin)
        # Larger neck
        pygame.draw.ellipse(screen, neck_color, (int(x - 6), int(y - 3), 12, 10))
        pygame.draw.ellipse(screen, skin, (int(x - 5), int(y - 2), 10, 8))
        pygame.draw.ellipse(screen, neck_light, (int(x - 3), int(y - 1), 6, 4))

    def _draw_head(self, screen, x, y, angle, aim_angle, anim_timer):
        """Draw the head with realistic features - optimized for web"""
        config = self.config

        # Head position (slight turn based on aim)
        head_x = x + math.sin(angle) * 2
        head_y = y

        # Base head shape - draw directly to screen (no surface creation)
        skin = config["skin_color"]
        skin_dark = tuple(max(0, c - 30) for c in skin)
        skin_light = tuple(min(255, c + 20) for c in skin)
        hr = self.head_radius

        # Draw head shadow (back of head)
        pygame.draw.ellipse(screen, skin_dark,
                           (int(head_x - hr), int(head_y - hr - 2), hr * 2, hr * 2 + 4))

        # Draw main head
        pygame.draw.ellipse(screen, skin,
                           (int(head_x - hr + 1), int(head_y - hr - 1), hr * 2 - 2, hr * 2 + 2))

        # Draw highlight on forehead
        pygame.draw.ellipse(screen, skin_light,
                           (int(head_x - hr//2), int(head_y - hr), hr, hr//2 + 2))

        # Check if this is a terminator-style avatar
        is_terminator = config.get("accessory") == "terminator"
        eye_color = config.get("eye_color", (70, 50, 30))

        # Draw facial features - eyes look toward aim
        eye_offset_x = math.cos(aim_angle) * 3
        eye_offset_y = math.sin(aim_angle) * 2
        eye_spacing = 4

        # Left eye
        eye_lx = head_x - eye_spacing
        eye_ly = head_y + 1

        if is_terminator:
            # TERMINATOR EYES - glowing red
            # Dark metal socket
            pygame.draw.ellipse(screen, (30, 30, 35),
                               (int(eye_lx - 4), int(eye_ly - 3), 8, 6))
            # Red glow outer
            pygame.draw.circle(screen, (150, 0, 0), (int(eye_lx), int(eye_ly)), 4)
            # Bright red center
            pygame.draw.circle(screen, (255, 0, 0), (int(eye_lx), int(eye_ly)), 3)
            # White hot center
            pygame.draw.circle(screen, (255, 100, 100), (int(eye_lx), int(eye_ly)), 1)
        else:
            # Normal human eyes
            pygame.draw.ellipse(screen, skin_dark,
                               (int(eye_lx - 4), int(eye_ly - 3), 8, 6))
            pygame.draw.ellipse(screen, (255, 255, 255),
                               (int(eye_lx - 3), int(eye_ly - 2), 7, 5))
            iris_x = eye_lx + eye_offset_x * 0.3
            iris_y = eye_ly + eye_offset_y * 0.3
            pygame.draw.circle(screen, eye_color, (int(iris_x), int(iris_y)), 2)
            pygame.draw.circle(screen, (10, 10, 10), (int(iris_x), int(iris_y)), 1)
            pygame.draw.circle(screen, (255, 255, 255), (int(iris_x - 1), int(iris_y - 1)), 1)

        # Right eye
        eye_rx = head_x + eye_spacing
        eye_ry = head_y + 1

        if is_terminator:
            # TERMINATOR EYES - glowing red
            pygame.draw.ellipse(screen, (30, 30, 35),
                               (int(eye_rx - 4), int(eye_ry - 3), 8, 6))
            pygame.draw.circle(screen, (150, 0, 0), (int(eye_rx), int(eye_ry)), 4)
            pygame.draw.circle(screen, (255, 0, 0), (int(eye_rx), int(eye_ry)), 3)
            pygame.draw.circle(screen, (255, 100, 100), (int(eye_rx), int(eye_ry)), 1)
        else:
            pygame.draw.ellipse(screen, skin_dark,
                               (int(eye_rx - 4), int(eye_ry - 3), 8, 6))
            pygame.draw.ellipse(screen, (255, 255, 255),
                               (int(eye_rx - 3), int(eye_ry - 2), 7, 5))
            iris_rx = eye_rx + eye_offset_x * 0.3
            iris_ry = eye_ry + eye_offset_y * 0.3
            pygame.draw.circle(screen, eye_color, (int(iris_rx), int(iris_ry)), 2)
            pygame.draw.circle(screen, (10, 10, 10), (int(iris_rx), int(iris_ry)), 1)
            pygame.draw.circle(screen, (255, 255, 255), (int(iris_rx - 1), int(iris_ry - 1)), 1)

        # Draw eyebrows (metallic for terminator)
        if is_terminator:
            brow_color = (60, 60, 70)  # Metal brow ridge
        else:
            brow_color = tuple(max(0, c - 40) for c in config["hair_color"])
        pygame.draw.line(screen, brow_color,
                        (int(eye_lx - 4), int(eye_ly - 5)),
                        (int(eye_lx + 3), int(eye_ly - 4)), 2)
        pygame.draw.line(screen, brow_color,
                        (int(eye_rx - 3), int(eye_ry - 4)),
                        (int(eye_rx + 4), int(eye_ry - 5)), 2)

        # Draw nose
        nose_y = head_y + 4
        pygame.draw.ellipse(screen, skin_dark,
                           (int(head_x - 2), int(nose_y - 1), 4, 3))

        # Draw ears (metallic sensors for terminator)
        if is_terminator:
            ear_color = (60, 60, 70)
        else:
            ear_color = tuple(max(0, c - 15) for c in skin)
        pygame.draw.ellipse(screen, ear_color,
                           (int(head_x - hr - 2), int(head_y - 1), 5, 7))
        pygame.draw.ellipse(screen, ear_color,
                           (int(head_x + hr - 3), int(head_y - 1), 5, 7))

        # Draw hair based on style
        hair_style = config["hair_style"]
        hair_color = config["hair_color"]
        if hair_style == "short":
            # Short cropped hair
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x - 7), int(head_y - 10), 14, 8))
            # Side hair
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x - 8), int(head_y - 6), 4, 6))
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x + 4), int(head_y - 6), 4, 6))
        elif hair_style == "mohawk":
            # Mohawk spikes
            for i in range(5):
                spike_x = head_x + (i - 2) * 3
                spike_h = 6 + (2 - abs(i - 2)) * 2
                pygame.draw.polygon(screen, hair_color, [
                    (int(spike_x - 2), int(head_y - 6)),
                    (int(spike_x), int(head_y - 6 - spike_h)),
                    (int(spike_x + 2), int(head_y - 6))
                ])
        elif hair_style == "bald":
            # Just a slight shine on bald head
            pygame.draw.ellipse(screen, skin_light,
                              (int(head_x - 3), int(head_y - 8), 6, 4))
        elif hair_style == "buzz":
            # Buzz cut (stubble)
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x - 6), int(head_y - 9), 12, 7))
        elif hair_style == "long":
            # Long hair flowing back
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x - 8), int(head_y - 10), 16, 10))
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x - 9), int(head_y - 4), 6, 12))
            pygame.draw.ellipse(screen, hair_color,
                              (int(head_x + 3), int(head_y - 4), 6, 12))

        # Draw accessories
        accessory = config.get("accessory")
        if accessory == "helmet":
            # Military helmet with depth
            helmet_color = (80, 90, 80)
            helmet_light = (100, 110, 100)
            pygame.draw.ellipse(screen, helmet_color,
                              (int(head_x - 10), int(head_y - 12), 20, 14))
            pygame.draw.ellipse(screen, helmet_light,
                              (int(head_x - 6), int(head_y - 11), 12, 6))
        elif accessory == "glasses":
            # Tactical sunglasses
            pygame.draw.rect(screen, (20, 20, 30),
                           (int(head_x - 7), int(head_y - 2), 14, 4), border_radius=2)
            pygame.draw.ellipse(screen, (10, 10, 20),
                              (int(head_x - 6), int(head_y - 1), 5, 3))
            pygame.draw.ellipse(screen, (10, 10, 20),
                              (int(head_x + 1), int(head_y - 1), 5, 3))
        elif accessory == "bandana":
            pygame.draw.ellipse(screen, (150, 30, 30),
                              (int(head_x - 8), int(head_y - 8), 16, 5))
            # Bandana tails
            pygame.draw.line(screen, (150, 30, 30),
                           (int(head_x + 7), int(head_y - 5)),
                           (int(head_x + 12), int(head_y)), 2)
        elif accessory == "mask":
            # Ninja mask covering lower face
            pygame.draw.ellipse(screen, (20, 20, 25),
                              (int(head_x - 7), int(head_y), 14, 8))
        elif accessory == "visor":
            # Glowing cyber visor (simplified - no surface for performance)
            pygame.draw.rect(screen, (80, 180, 255),
                           (int(head_x - 8), int(head_y - 2), 16, 5), border_radius=2)
            # Simple glow border instead of surface
            pygame.draw.rect(screen, (100, 200, 255),
                           (int(head_x - 9), int(head_y - 3), 18, 7), 1, border_radius=3)
        elif accessory == "goggles":
            # Snow/tactical goggles
            pygame.draw.ellipse(screen, (50, 50, 60),
                              (int(head_x - 9), int(head_y - 4), 18, 7))
            pygame.draw.ellipse(screen, (150, 180, 220),
                              (int(head_x - 7), int(head_y - 3), 6, 5))
            pygame.draw.ellipse(screen, (150, 180, 220),
                              (int(head_x + 1), int(head_y - 3), 6, 5))
        elif accessory == "cigar":
            # Cigar in mouth
            cigar_x = head_x + 4
            cigar_y = head_y + 4
            pygame.draw.line(screen, (100, 70, 40),
                           (int(cigar_x), int(cigar_y)),
                           (int(cigar_x + 10), int(cigar_y - 2)), 3)
            # Glowing tip
            pygame.draw.circle(screen, (255, 150, 50), (int(cigar_x + 10), int(cigar_y - 2)), 2)
            # Smoke puffs (simplified - no surfaces for performance)
            if anim_timer % 30 < 15:
                gray_shades = [(200, 200, 200), (180, 180, 180), (160, 160, 160)]
                for i in range(3):
                    smoke_x = cigar_x + 12 + i * 4
                    smoke_y = cigar_y - 4 - i * 3
                    pygame.draw.circle(screen, gray_shades[i], (int(smoke_x), int(smoke_y)), 3 - i)

    def _draw_torso(self, screen, x, y, angle):
        """Draw the torso - optimized for web (no surface/rotation)"""
        config = self.config
        shirt = config["shirt_color"]
        shirt_dark = tuple(max(0, c - 30) for c in shirt)
        shirt_light = tuple(min(255, c + 25) for c in shirt)

        tw = self.torso_width
        th = self.torso_height

        # Draw torso directly to screen (body stays upright in top-down view)
        # Shadow side
        pygame.draw.ellipse(screen, shirt_dark,
                          (int(x - tw//2), int(y - th//2), tw, th))
        # Main body
        pygame.draw.ellipse(screen, shirt,
                          (int(x - tw//2 + 2), int(y - th//2 + 1), tw - 4, th - 2))
        # Highlight
        pygame.draw.ellipse(screen, shirt_light,
                          (int(x - tw//4), int(y - th//2 + 2), tw//2, th//3))

        # Draw belt at waist
        pygame.draw.rect(screen, (50, 40, 30),
                        (int(x - 7), int(y + th//2 - 5), 14, 3))
        # Belt buckle
        pygame.draw.rect(screen, (180, 160, 80),
                        (int(x - 2), int(y + th//2 - 5), 4, 3))

    def _draw_leg(self, screen, x, y, angle, is_back=False):
        """Draw a leg with realistic walk animation"""
        config = self.config
        pants = config["pants_color"]
        pants_dark = tuple(max(0, c - 25) for c in pants)
        boot = config["boot_color"]
        boot_dark = tuple(max(0, c - 30) for c in boot)
        boot_light = tuple(min(255, c + 20) for c in boot)

        # Leg offset from center
        side_offset = -5 if is_back else 5

        # Walk animation - legs swing opposite each other
        walk_offset = math.sin(self.walk_cycle + (math.pi if is_back else 0)) * 0.5
        leg_angle = angle + math.pi/2 + walk_offset  # Legs point "down" relative to body

        # Knee bend during walk
        knee_bend = abs(math.sin(self.walk_cycle + (math.pi if is_back else 0))) * 0.3

        # Hip position
        hip_x = x + math.cos(angle + math.pi/2) * side_offset
        hip_y = y + math.sin(angle + math.pi/2) * side_offset + 4

        # Knee position (with bend)
        knee_x = hip_x + math.cos(leg_angle + 0.2 + knee_bend) * (self.leg_length * 0.5)
        knee_y = hip_y + math.sin(leg_angle + 0.2 + knee_bend) * (self.leg_length * 0.5)

        # Foot position
        foot_angle = leg_angle - 0.1 - knee_bend * 0.5
        foot_x = knee_x + math.cos(foot_angle) * (self.leg_length * 0.55)
        foot_y = knee_y + math.sin(foot_angle) * (self.leg_length * 0.55)

        # Draw thigh with shading
        # Shadow
        pygame.draw.line(screen, pants_dark,
                        (int(hip_x + 1), int(hip_y)),
                        (int(knee_x + 1), int(knee_y)), self.leg_width + 1)
        # Main thigh
        pygame.draw.line(screen, pants,
                        (int(hip_x), int(hip_y)),
                        (int(knee_x), int(knee_y)), self.leg_width)

        # Draw knee joint
        pygame.draw.circle(screen, pants_dark, (int(knee_x), int(knee_y)), 3)

        # Draw shin with shading
        pygame.draw.line(screen, pants_dark,
                        (int(knee_x + 1), int(knee_y)),
                        (int(foot_x + 1), int(foot_y)), self.leg_width - 1)
        pygame.draw.line(screen, pants,
                        (int(knee_x), int(knee_y)),
                        (int(foot_x), int(foot_y)), self.leg_width - 2)

        # Draw boot (more detailed)
        # Boot shaft
        pygame.draw.ellipse(screen, boot_dark,
                          (int(foot_x - 4), int(foot_y - 3), 8, 7))
        pygame.draw.ellipse(screen, boot,
                          (int(foot_x - 3), int(foot_y - 2), 6, 5))
        # Boot toe (pointing in walk direction)
        toe_x = foot_x + math.cos(foot_angle) * 4
        toe_y = foot_y + math.sin(foot_angle) * 4
        pygame.draw.ellipse(screen, boot,
                          (int(toe_x - 3), int(toe_y - 2), 6, 4))
        # Boot highlight
        pygame.draw.ellipse(screen, boot_light,
                          (int(foot_x - 2), int(foot_y - 2), 3, 2))

    def _draw_arm(self, screen, x, y, angle, is_front=True, is_reloading=False,
                 reload_phase=0, weapon_name="Rifle", anim_timer=0):
        """Draw an arm with realistic shading and reload animation"""
        config = self.config
        shirt = config["shirt_color"]
        shirt_dark = tuple(max(0, c - 25) for c in shirt)
        skin = config["skin_color"]
        skin_dark = tuple(max(0, c - 20) for c in skin)
        glove = config["glove_color"]
        glove_dark = tuple(max(0, c - 25) for c in glove)
        glove_light = tuple(min(255, c + 20) for c in glove)

        # Arm offset from center (shoulder position)
        side_offset = 6 if is_front else -6

        # Shoulder position
        shoulder_x = x + math.cos(angle + math.pi/2) * side_offset
        shoulder_y = y + math.sin(angle + math.pi/2) * side_offset - 2

        if is_front:
            # Front arm follows gun angle
            arm_angle = angle
            # During reload, hand moves to magazine/action
            if is_reloading:
                hand_pos = self._get_reload_hand_position(reload_phase, weapon_name, x, y, angle)
                elbow_x = shoulder_x + math.cos(arm_angle + 0.3) * (self.arm_length * 0.5)
                elbow_y = shoulder_y + math.sin(arm_angle + 0.3) * (self.arm_length * 0.5)
                hand_x, hand_y = hand_pos
            else:
                elbow_x = shoulder_x + math.cos(arm_angle + 0.2) * (self.arm_length * 0.5)
                elbow_y = shoulder_y + math.sin(arm_angle + 0.2) * (self.arm_length * 0.5)
                hand_x = elbow_x + math.cos(arm_angle) * (self.arm_length * 0.6)
                hand_y = elbow_y + math.sin(arm_angle) * (self.arm_length * 0.6)
        else:
            # Back arm - for one-handed weapons, arm hangs at side naturally
            one_handed = weapon_name in ["Handgun", "Knife", "Grenade", "Smoke"]

            if one_handed and not is_reloading:
                # Arm hangs at side/slightly back - natural idle pose
                idle_angle = angle + math.pi * 0.7  # Point backward/down
                elbow_x = shoulder_x + math.cos(idle_angle) * (self.arm_length * 0.4)
                elbow_y = shoulder_y + math.sin(idle_angle) * (self.arm_length * 0.4)
                hand_x = elbow_x + math.cos(idle_angle + 0.3) * (self.arm_length * 0.5)
                hand_y = elbow_y + math.sin(idle_angle + 0.3) * (self.arm_length * 0.5)
            elif is_reloading:
                # Support hand moves during reload
                arm_angle = angle + 0.5
                elbow_x = shoulder_x + math.cos(arm_angle) * (self.arm_length * 0.4)
                elbow_y = shoulder_y + math.sin(arm_angle) * (self.arm_length * 0.4)
                hand_pos = self._get_support_hand_position(reload_phase, weapon_name, x, y, angle)
                hand_x, hand_y = hand_pos
            else:
                # Two-handed weapons - support arm helps hold weapon
                arm_angle = angle + 0.5
                elbow_x = shoulder_x + math.cos(arm_angle) * (self.arm_length * 0.4)
                elbow_y = shoulder_y + math.sin(arm_angle) * (self.arm_length * 0.4)
                hand_x = elbow_x + math.cos(arm_angle - 0.2) * (self.arm_length * 0.5)
                hand_y = elbow_y + math.sin(arm_angle - 0.2) * (self.arm_length * 0.5)

        # Draw shoulder joint
        pygame.draw.circle(screen, shirt_dark, (int(shoulder_x), int(shoulder_y)), 4)

        # Draw upper arm (sleeve) with shading
        pygame.draw.line(screen, shirt_dark,
                        (int(shoulder_x + 1), int(shoulder_y + 1)),
                        (int(elbow_x + 1), int(elbow_y + 1)), self.arm_width + 1)
        pygame.draw.line(screen, shirt,
                        (int(shoulder_x), int(shoulder_y)),
                        (int(elbow_x), int(elbow_y)), self.arm_width)

        # Draw elbow joint
        pygame.draw.circle(screen, shirt_dark, (int(elbow_x), int(elbow_y)), 3)

        # Draw forearm (exposed skin or sleeve)
        pygame.draw.line(screen, skin_dark,
                        (int(elbow_x + 1), int(elbow_y + 1)),
                        (int(hand_x + 1), int(hand_y + 1)), self.arm_width)
        pygame.draw.line(screen, skin,
                        (int(elbow_x), int(elbow_y)),
                        (int(hand_x), int(hand_y)), self.arm_width - 1)

        # Draw wrist
        wrist_x = hand_x - math.cos(arm_angle) * 3
        wrist_y = hand_y - math.sin(arm_angle) * 3
        pygame.draw.circle(screen, skin_dark, (int(wrist_x), int(wrist_y)), 3)

        # Draw gloved hand with shading
        pygame.draw.circle(screen, glove_dark,
                         (int(hand_x + 1), int(hand_y + 1)), self.hand_radius + 1)
        pygame.draw.circle(screen, glove,
                         (int(hand_x), int(hand_y)), self.hand_radius)
        pygame.draw.circle(screen, glove_light,
                         (int(hand_x - 1), int(hand_y - 1)), 2)

        # Draw fingers during reload
        if is_reloading and not is_front:
            self._draw_fingers(screen, hand_x, hand_y, angle, glove)

    def _draw_fingers(self, screen, hand_x, hand_y, angle, color):
        """Draw individual fingers for detailed hand animation"""
        # Draw 4 finger tips
        for i in range(4):
            finger_angle = angle + (i - 1.5) * 0.15
            finger_x = hand_x + math.cos(finger_angle) * 5
            finger_y = hand_y + math.sin(finger_angle) * 5
            pygame.draw.circle(screen, color, (int(finger_x), int(finger_y)), 2)

    def _get_reload_hand_position(self, phase, weapon_name, x, y, angle):
        """Get the position of the main hand during reload animation"""
        # Base position (holding the gun grip)
        base_x = x + math.cos(angle) * 15
        base_y = y + math.sin(angle) * 15

        # During reload, hand stays on grip but moves slightly
        if weapon_name == "Rifle":
            if phase < 0.3:
                # Tilting gun
                offset = phase / 0.3 * 3
                return base_x, base_y + offset
            else:
                return base_x, base_y + 3
        elif weapon_name == "Shotgun":
            # Pump action - hand moves back and forth
            if phase < 0.4:
                offset = phase / 0.4 * 8
                return base_x - offset * math.cos(angle), base_y - offset * math.sin(angle)
            elif phase < 0.6:
                return base_x - 8 * math.cos(angle), base_y - 8 * math.sin(angle)
            else:
                offset = (1 - (phase - 0.6) / 0.4) * 8
                return base_x - offset * math.cos(angle), base_y - offset * math.sin(angle)

        return base_x, base_y

    def _get_support_hand_position(self, phase, weapon_name, x, y, angle):
        """Get the position of the support hand during reload"""
        if weapon_name == "Rifle":
            # Support hand grabs magazine
            mag_x = x + math.cos(angle) * 10 + math.cos(angle + math.pi/2) * 5
            mag_y = y + math.sin(angle) * 10 + math.sin(angle + math.pi/2) * 5

            if phase < 0.3:
                # Move to magazine
                return mag_x, mag_y
            elif phase < 0.5:
                # Pull magazine out
                offset = (phase - 0.3) / 0.2 * 15
                return mag_x + math.cos(angle + math.pi/2) * offset, mag_y + math.sin(angle + math.pi/2) * offset
            elif phase < 0.8:
                # Insert new magazine
                offset = 15 * (1 - (phase - 0.5) / 0.3)
                return mag_x + math.cos(angle + math.pi/2) * offset, mag_y + math.sin(angle + math.pi/2) * offset
            else:
                return mag_x, mag_y

        elif weapon_name == "Handgun":
            # Support hand pulls slide
            slide_x = x + math.cos(angle) * 12
            slide_y = y + math.sin(angle) * 12

            if phase < 0.3:
                offset = phase / 0.3 * 6
                return slide_x - math.cos(angle) * offset, slide_y - math.sin(angle) * offset
            elif phase < 0.7:
                return slide_x - math.cos(angle) * 6, slide_y - math.sin(angle) * 6
            else:
                offset = (1 - (phase - 0.7) / 0.3) * 6
                return slide_x - math.cos(angle) * offset, slide_y - math.sin(angle) * offset

        elif weapon_name == "Shotgun":
            # Support hand on pump
            pump_x = x + math.cos(angle) * 18
            pump_y = y + math.sin(angle) * 18

            if phase < 0.4:
                offset = phase / 0.4 * 12
                return pump_x - math.cos(angle) * offset, pump_y - math.sin(angle) * offset
            elif phase < 0.6:
                return pump_x - math.cos(angle) * 12, pump_y - math.sin(angle) * 12
            else:
                offset = (1 - (phase - 0.6) / 0.4) * 12
                return pump_x - math.cos(angle) * offset, pump_y - math.sin(angle) * offset

        # Default support hand position
        return x + math.cos(angle) * 15, y + math.sin(angle) * 15

    def draw_holding_hands(self, screen, x, y, angle, weapon_name, is_reloading=False,
                          reload_phase=0, is_firing=False, recoil=0):
        """Draw both hands holding the weapon (called after weapon is drawn)"""
        config = self.config

        # Calculate hand positions based on weapon type
        if weapon_name in ["Rifle", "Shotgun", "Sniper", "Minigun"]:
            # Two-handed grip
            # Front hand on foregrip
            front_dist = 20 - recoil * 0.5
            front_x = x + math.cos(angle) * front_dist
            front_y = y + math.sin(angle) * front_dist

            # Back hand on grip
            back_dist = 8 - recoil * 0.3
            back_x = x + math.cos(angle) * back_dist + math.cos(angle + math.pi/2) * 3
            back_y = y + math.sin(angle) * back_dist + math.sin(angle + math.pi/2) * 3

            # Modify positions during reload
            if is_reloading:
                front_x, front_y = self._get_support_hand_position(reload_phase, weapon_name, x, y, angle)

            # Draw hands
            pygame.draw.circle(screen, config["glove_color"], (int(front_x), int(front_y)), self.hand_radius)
            pygame.draw.circle(screen, config["glove_color"], (int(back_x), int(back_y)), self.hand_radius)

            # Draw finger details on front hand
            self._draw_fingers(screen, front_x, front_y, angle, config["glove_color"])

        elif weapon_name == "Handgun":
            # Single hand grip for handgun
            main_x = x + math.cos(angle) * 10
            main_y = y + math.sin(angle) * 10
            pygame.draw.circle(screen, config["glove_color"], (int(main_x), int(main_y)), self.hand_radius)
            self._draw_fingers(screen, main_x, main_y, angle, config["glove_color"])

        elif weapon_name == "Dual Pistols":
            # Both hands extended
            left_x = x + math.cos(angle - 0.3) * 12
            left_y = y + math.sin(angle - 0.3) * 12
            right_x = x + math.cos(angle + 0.3) * 12
            right_y = y + math.sin(angle + 0.3) * 12

            pygame.draw.circle(screen, config["glove_color"], (int(left_x), int(left_y)), self.hand_radius)
            pygame.draw.circle(screen, config["glove_color"], (int(right_x), int(right_y)), self.hand_radius)

        elif weapon_name == "RPG":
            # Shoulder-mounted
            shoulder_x = x + math.cos(angle + math.pi/2) * 5
            shoulder_y = y + math.sin(angle + math.pi/2) * 5
            grip_x = x + math.cos(angle) * 15
            grip_y = y + math.sin(angle) * 15

            pygame.draw.circle(screen, config["glove_color"], (int(shoulder_x), int(shoulder_y)), self.hand_radius)
            pygame.draw.circle(screen, config["glove_color"], (int(grip_x), int(grip_y)), self.hand_radius)

        elif weapon_name == "Knife":
            # Single hand grip for knife
            hand_x = x + math.cos(angle) * 10
            hand_y = y + math.sin(angle) * 10
            pygame.draw.circle(screen, config["glove_color"], (int(hand_x), int(hand_y)), self.hand_radius)
            self._draw_fingers(screen, hand_x, hand_y, angle, config["glove_color"])

        elif weapon_name in ["Grenade", "Smoke"]:
            # Single hand for throwing grenades
            hand_x = x + math.cos(angle) * 8
            hand_y = y + math.sin(angle) * 8
            pygame.draw.circle(screen, config["glove_color"], (int(hand_x), int(hand_y)), self.hand_radius)
            self._draw_fingers(screen, hand_x, hand_y, angle, config["glove_color"])

        else:
            # Default single hand for other weapons
            hand_x = x + math.cos(angle) * 12
            hand_y = y + math.sin(angle) * 12
            pygame.draw.circle(screen, config["glove_color"], (int(hand_x), int(hand_y)), self.hand_radius)


class VirtualJoystick:
    """Virtual joystick for mobile touch controls"""
    # Class-level cached surfaces (created once, shared by all instances)
    _base_surf = None
    _knob_surf = None
    _cached_radius = None
    _cached_knob_radius = None

    def __init__(self, x, y, radius=60):
        self.base_x = x
        self.base_y = y
        self.radius = radius
        self.knob_radius = 25
        self.knob_x = x
        self.knob_y = y
        self.active = False
        self.touch_id = None
        self.dx = 0  # -1 to 1
        self.dy = 0  # -1 to 1

    def contains_point(self, x, y):
        """Check if a point is within the joystick touch area"""
        dist = math.sqrt((x - self.base_x)**2 + (y - self.base_y)**2)
        return dist < self.radius * 1.5

    def handle_touch_down(self, x, y, touch_id):
        if self.contains_point(x, y):
            self.active = True
            self.touch_id = touch_id
            self.update_knob(x, y)
            return True
        return False

    def handle_touch_move(self, x, y, touch_id):
        if self.active and touch_id == self.touch_id:
            self.update_knob(x, y)
            return True
        return False

    def handle_touch_up(self, touch_id):
        if touch_id == self.touch_id:
            self.active = False
            self.touch_id = None
            self.knob_x = self.base_x
            self.knob_y = self.base_y
            self.dx = 0
            self.dy = 0
            return True
        return False

    def update_knob(self, x, y):
        dx = x - self.base_x
        dy = y - self.base_y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > self.radius:
            dx = dx / dist * self.radius
            dy = dy / dist * self.radius

        self.knob_x = self.base_x + dx
        self.knob_y = self.base_y + dy
        self.dx = dx / self.radius
        self.dy = dy / self.radius

    def draw(self, screen):
        # Create cached surfaces once (lazy initialization)
        if VirtualJoystick._base_surf is None or VirtualJoystick._cached_radius != self.radius:
            VirtualJoystick._cached_radius = self.radius
            VirtualJoystick._base_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(VirtualJoystick._base_surf, (100, 100, 100, 100), (self.radius, self.radius), self.radius)
            pygame.draw.circle(VirtualJoystick._base_surf, (150, 150, 150, 150), (self.radius, self.radius), self.radius, 3)

        if VirtualJoystick._knob_surf is None or VirtualJoystick._cached_knob_radius != self.knob_radius:
            VirtualJoystick._cached_knob_radius = self.knob_radius
            VirtualJoystick._knob_surf = pygame.Surface((self.knob_radius * 2, self.knob_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(VirtualJoystick._knob_surf, (200, 200, 200, 180), (self.knob_radius, self.knob_radius), self.knob_radius)

        # Draw base circle (using cached surface)
        screen.blit(VirtualJoystick._base_surf, (self.base_x - self.radius, self.base_y - self.radius))

        # Draw knob (using cached surface)
        screen.blit(VirtualJoystick._knob_surf, (self.knob_x - self.knob_radius, self.knob_y - self.knob_radius))


class TouchButton:
    """Touch button for mobile controls"""
    # Class-level font cache
    _cached_font = None

    def __init__(self, x, y, radius, label, color=(100, 100, 200)):
        self.x = x
        self.y = y
        self.radius = radius
        self.label = label
        self.color = color
        self.pressed = False
        self.touch_id = None
        # Instance-level cached surfaces and text
        self._normal_surf = None
        self._pressed_surf = None
        self._text_surf = None

    def contains_point(self, x, y):
        """Check if a point is within the button touch area"""
        dx = x - self.x
        dy = y - self.y
        return (dx * dx + dy * dy) < (self.radius * self.radius)

    def handle_touch_down(self, x, y, touch_id):
        if self.contains_point(x, y):
            self.pressed = True
            self.touch_id = touch_id
            return True
        return False

    def handle_touch_up(self, touch_id):
        if touch_id == self.touch_id:
            self.pressed = False
            self.touch_id = None
            return True
        return False

    def _create_cached_surfaces(self):
        """Create cached surfaces once"""
        if self._normal_surf is None:
            # Normal state surface
            self._normal_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            color = (self.color[0], self.color[1], self.color[2], 120)
            pygame.draw.circle(self._normal_surf, color, (self.radius, self.radius), self.radius)
            pygame.draw.circle(self._normal_surf, (200, 200, 200, 150), (self.radius, self.radius), self.radius, 3)

            # Pressed state surface
            self._pressed_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            color = (self.color[0], self.color[1], self.color[2], 180)
            pygame.draw.circle(self._pressed_surf, color, (self.radius, self.radius), self.radius)
            pygame.draw.circle(self._pressed_surf, (255, 255, 255, 200), (self.radius, self.radius), self.radius, 3)

            # Cached font and text
            if TouchButton._cached_font is None:
                TouchButton._cached_font = pygame.font.Font(None, 24)
            self._text_surf = TouchButton._cached_font.render(self.label, True, (255, 255, 255))

    def draw(self, screen):
        # Create cached surfaces on first draw
        self._create_cached_surfaces()

        # Draw appropriate surface based on state
        surf = self._pressed_surf if self.pressed else self._normal_surf
        screen.blit(surf, (self.x - self.radius, self.y - self.radius))

        # Draw label (cached)
        screen.blit(self._text_surf, (self.x - self._text_surf.get_width() // 2, self.y - self._text_surf.get_height() // 2))


class FakeKeys:
    """Fake keys class for mobile joystick - defined once at module level for performance"""
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy
    def __getitem__(self, key):
        if key == pygame.K_w or key == pygame.K_UP:
            return self.dy < -0.3
        if key == pygame.K_s or key == pygame.K_DOWN:
            return self.dy > 0.3
        if key == pygame.K_a or key == pygame.K_LEFT:
            return self.dx < -0.3
        if key == pygame.K_d or key == pygame.K_RIGHT:
            return self.dx > 0.3
        return False


class Camera:
    def __init__(self, view_width=SCREEN_WIDTH, view_height=SCREEN_HEIGHT):
        self.x = 0
        self.y = 0
        self.view_width = view_width
        self.view_height = view_height

    def update(self, target_x, target_y):
        # Center camera on target
        self.x = target_x - self.view_width // 2
        self.y = target_y - self.view_height // 2

        # Keep camera in bounds
        self.x = max(0, min(MAP_WIDTH - self.view_width, self.x))
        self.y = max(0, min(MAP_HEIGHT - self.view_height, self.y))

    def apply(self, x, y):
        return x - self.x, y - self.y


class Bullet:
    def __init__(self, x, y, angle, is_player=True, is_shotgun=False, weapon_type="Rifle"):
        self.x = x
        self.y = y
        self.start_x = x  # Track starting position for shotgun damage calc
        self.start_y = y
        self.angle = angle
        self.speed = 15 if is_player else 8
        self.is_player = is_player
        self.is_shotgun = is_shotgun
        self.weapon_type = weapon_type
        self.radius = 5
        self.base_damage = 25 if is_player else 10
        self.damage = self.base_damage
        self.lifetime = 180
        self.color = YELLOW if is_player else ORANGE

        # Trail effect
        self.trail = []
        self.max_trail_length = 5

    def update(self):
        # Store position for trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1

        # Check bounds
        if self.x < 0 or self.x > MAP_WIDTH or self.y < 0 or self.y > MAP_HEIGHT:
            self.lifetime = 0

    def get_damage(self):
        """Get damage, accounting for shotgun distance falloff"""
        if not self.is_shotgun:
            return self.damage

        # Calculate distance traveled
        dist = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)

        # Shotgun: max damage up close (50), falls off with distance
        # At 0 distance: 50 damage
        # At 150+ distance: 10 damage (minimum)
        max_effective_range = 150
        if dist < max_effective_range:
            # Linear falloff from base_damage to 10
            damage_mult = 1 - (dist / max_effective_range) * 0.8
            return int(self.base_damage * damage_mult)
        else:
            return 10  # Minimum damage at long range

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        if -20 < sx < SCREEN_WIDTH + 20 and -20 < sy < SCREEN_HEIGHT + 20:
            # Draw trail first (behind bullet)
            if len(self.trail) > 1:
                for i, (tx, ty) in enumerate(self.trail):
                    tsx, tsy = camera.apply(tx, ty)
                    alpha = (i + 1) / len(self.trail)
                    trail_size = int(self.radius * 0.5 * alpha)
                    if trail_size > 0:
                        wt = self.weapon_type
                        if wt == "Sniper":
                            # Sniper has a longer, thinner trail
                            trail_color = (200, 220, 255)
                        elif wt == "Shotgun":
                            # Shotgun pellets have orange trail
                            trail_color = (255, 150, 50)
                        elif wt == "RPG":
                            # RPG has smoke trail
                            trail_color = (150, 150, 150)
                        elif wt == "Flamethrower":
                            # Fire trail
                            trail_color = (255, 100 + random.randint(0, 100), 0)
                        elif wt in ["Laser", "Laser Gun"]:
                            # Green glow trail
                            trail_color = (0, 200, 0)
                        elif wt == "Minigun":
                            # Brass trail
                            trail_color = (180, 140, 60)
                        elif wt == "Crossbow":
                            # Brown trail
                            trail_color = (139, 69, 19)
                        elif wt in ["Electric", "Electric Gun"]:
                            # Electric blue trail
                            trail_color = (100, 150, 255)
                        elif wt in ["Freeze", "Freeze Ray"]:
                            # Ice blue trail
                            trail_color = (150, 220, 255)
                        elif wt == "Dual Pistols":
                            # Gold trail
                            trail_color = (255, 215, 0)
                        elif wt == "Throwing Knives":
                            # Silver trail
                            trail_color = (192, 192, 192)
                        else:
                            trail_color = (255, 200, 100)
                        pygame.draw.circle(screen, trail_color, (int(tsx), int(tsy)), trail_size)

            # Draw bullet based on weapon type
            wt = self.weapon_type
            if wt == "Rifle":
                self._draw_rifle_bullet(screen, sx, sy)
            elif wt == "Handgun":
                self._draw_handgun_bullet(screen, sx, sy)
            elif wt == "Shotgun":
                self._draw_shotgun_pellet(screen, sx, sy)
            elif wt == "Sniper":
                self._draw_sniper_bullet(screen, sx, sy)
            elif wt == "RPG":
                self._draw_rpg_rocket(screen, sx, sy)
            elif wt == "Flamethrower":
                self._draw_flamethrower(screen, sx, sy)
            elif wt in ["Laser", "Laser Gun"]:
                self._draw_laser(screen, sx, sy)
            elif wt == "Minigun":
                self._draw_minigun(screen, sx, sy)
            elif wt == "Crossbow":
                self._draw_crossbow(screen, sx, sy)
            elif wt in ["Electric", "Electric Gun"]:
                self._draw_electric(screen, sx, sy)
            elif wt in ["Freeze", "Freeze Ray"]:
                self._draw_freeze(screen, sx, sy)
            elif wt == "Dual Pistols":
                self._draw_dual_pistols(screen, sx, sy)
            elif wt == "Throwing Knives":
                self._draw_throwing_knife(screen, sx, sy)
            elif wt == "Enemy_Knife":
                self._draw_enemy_knife(screen, sx, sy)
            elif wt == "Enemy_Pistol":
                self._draw_enemy_pistol(screen, sx, sy)
            else:
                # Enemy bullets or default
                self._draw_enemy_bullet(screen, sx, sy)

    def _draw_rifle_bullet(self, screen, sx, sy):
        """Draw realistic rifle bullet - pointed brass casing"""
        # Bullet body (brass colored, elongated)
        bullet_length = 12
        bullet_width = 4

        # Calculate bullet tip and base
        tip_x = sx + math.cos(self.angle) * (bullet_length / 2)
        tip_y = sy + math.sin(self.angle) * (bullet_length / 2)
        base_x = sx - math.cos(self.angle) * (bullet_length / 2)
        base_y = sy - math.sin(self.angle) * (bullet_length / 2)

        # Draw bullet body (brass)
        pygame.draw.line(screen, (180, 140, 60), (base_x, base_y), (tip_x, tip_y), bullet_width)

        # Draw copper tip
        pygame.draw.line(screen, (200, 100, 50),
                        (sx, sy), (tip_x, tip_y), bullet_width - 1)

        # Highlight
        pygame.draw.line(screen, (220, 180, 100),
                        (base_x, base_y), (sx, sy), 2)

    def _draw_handgun_bullet(self, screen, sx, sy):
        """Draw smaller pistol bullet"""
        bullet_length = 8
        bullet_width = 3

        tip_x = sx + math.cos(self.angle) * (bullet_length / 2)
        tip_y = sy + math.sin(self.angle) * (bullet_length / 2)
        base_x = sx - math.cos(self.angle) * (bullet_length / 2)
        base_y = sy - math.sin(self.angle) * (bullet_length / 2)

        # Brass casing
        pygame.draw.line(screen, (180, 140, 60), (base_x, base_y), (tip_x, tip_y), bullet_width)
        # Lead tip
        pygame.draw.line(screen, (100, 100, 100), (sx, sy), (tip_x, tip_y), bullet_width - 1)

    def _draw_shotgun_pellet(self, screen, sx, sy):
        """Draw small round shotgun pellet"""
        # Small lead pellet
        pygame.draw.circle(screen, (80, 80, 80), (int(sx), int(sy)), 3)
        pygame.draw.circle(screen, (120, 120, 120), (int(sx), int(sy)), 3, 1)
        # Shine
        pygame.draw.circle(screen, (150, 150, 150), (int(sx - 1), int(sy - 1)), 1)

    def _draw_sniper_bullet(self, screen, sx, sy):
        """Draw long sniper bullet with tracer effect"""
        bullet_length = 18
        bullet_width = 4

        tip_x = sx + math.cos(self.angle) * (bullet_length / 2)
        tip_y = sy + math.sin(self.angle) * (bullet_length / 2)
        base_x = sx - math.cos(self.angle) * (bullet_length / 2)
        base_y = sy - math.sin(self.angle) * (bullet_length / 2)

        # Long brass casing
        pygame.draw.line(screen, (180, 140, 60), (base_x, base_y), (tip_x, tip_y), bullet_width)

        # Steel/copper tip
        pygame.draw.line(screen, (150, 80, 40), (sx, sy), (tip_x, tip_y), bullet_width - 1)

        # Tracer glow (cyan)
        pygame.draw.line(screen, (100, 200, 255), (base_x, base_y), (sx, sy), 2)
        pygame.draw.circle(screen, (150, 220, 255), (int(base_x), int(base_y)), 3)

    def _draw_rpg_rocket(self, screen, sx, sy):
        """Draw RPG rocket"""
        rocket_length = 20
        rocket_width = 6

        tip_x = sx + math.cos(self.angle) * (rocket_length / 2)
        tip_y = sy + math.sin(self.angle) * (rocket_length / 2)
        base_x = sx - math.cos(self.angle) * (rocket_length / 2)
        base_y = sy - math.sin(self.angle) * (rocket_length / 2)

        # Rocket body (olive/gray)
        pygame.draw.line(screen, (80, 90, 70), (base_x, base_y), (tip_x, tip_y), rocket_width)

        # Warhead (darker tip)
        pygame.draw.line(screen, (60, 60, 60), (sx, sy), (tip_x, tip_y), rocket_width - 1)

        # Fins at the back
        fin_angle1 = self.angle + math.pi/2
        fin_angle2 = self.angle - math.pi/2
        fin_length = 6
        fin1_x = base_x + math.cos(fin_angle1) * fin_length
        fin1_y = base_y + math.sin(fin_angle1) * fin_length
        fin2_x = base_x + math.cos(fin_angle2) * fin_length
        fin2_y = base_y + math.sin(fin_angle2) * fin_length
        pygame.draw.line(screen, (60, 70, 50), (base_x, base_y), (fin1_x, fin1_y), 2)
        pygame.draw.line(screen, (60, 70, 50), (base_x, base_y), (fin2_x, fin2_y), 2)

        # Rocket flame at back
        flame_x = base_x - math.cos(self.angle) * 8
        flame_y = base_y - math.sin(self.angle) * 8
        pygame.draw.line(screen, (255, 200, 50), (base_x, base_y), (flame_x, flame_y), 4)
        pygame.draw.line(screen, (255, 100, 0), (base_x, base_y), (flame_x, flame_y), 2)

    def _draw_enemy_bullet(self, screen, sx, sy):
        """Draw enemy bullet - red/orange energy ball"""
        # Outer glow
        pygame.draw.circle(screen, (255, 100, 50), (int(sx), int(sy)), self.radius + 2)
        # Inner core
        pygame.draw.circle(screen, (255, 200, 100), (int(sx), int(sy)), self.radius)
        # Hot center
        pygame.draw.circle(screen, (255, 255, 200), (int(sx), int(sy)), self.radius - 2)

    def _draw_enemy_knife(self, screen, sx, sy):
        """Draw enemy throwing knife - spinning silver blade"""
        knife_length = 14
        # Spinning effect using lifetime
        spin_angle = self.angle + (self.lifetime * 0.4)
        tip_x = sx + math.cos(spin_angle) * knife_length
        tip_y = sy + math.sin(spin_angle) * knife_length
        base_x = sx - math.cos(spin_angle) * (knife_length / 2)
        base_y = sy - math.sin(spin_angle) * (knife_length / 2)
        # Blade
        pygame.draw.line(screen, (192, 192, 192), (base_x, base_y), (tip_x, tip_y), 3)
        # Shine on blade
        pygame.draw.line(screen, (255, 255, 255), (sx, sy), (tip_x, tip_y), 1)
        # Small red glow for danger
        pygame.draw.circle(screen, (200, 50, 50), (int(sx), int(sy)), 3)

    def _draw_enemy_pistol(self, screen, sx, sy):
        """Draw enemy dual pistol bullet - small golden bullet"""
        bullet_length = 7
        tip_x = sx + math.cos(self.angle) * bullet_length
        tip_y = sy + math.sin(self.angle) * bullet_length
        # Gold casing
        pygame.draw.line(screen, (255, 180, 50), (sx, sy), (tip_x, tip_y), 3)
        # Shine
        pygame.draw.line(screen, (255, 240, 150), (sx, sy), (tip_x, tip_y), 1)

    def _draw_flamethrower(self, screen, sx, sy):
        """Draw flamethrower fire particle"""
        # Random flickering fire effect
        size = self.radius + random.randint(-2, 3)
        # Outer orange flame
        pygame.draw.circle(screen, (255, 100, 0), (int(sx), int(sy)), size + 2)
        # Inner yellow flame
        pygame.draw.circle(screen, (255, 200, 0), (int(sx), int(sy)), size)
        # Hot white core
        pygame.draw.circle(screen, (255, 255, 150), (int(sx), int(sy)), max(1, size - 2))

    def _draw_laser(self, screen, sx, sy):
        """Draw laser beam - thin bright green line"""
        beam_length = 15
        tip_x = sx + math.cos(self.angle) * beam_length
        tip_y = sy + math.sin(self.angle) * beam_length
        # Glow effect
        pygame.draw.line(screen, (0, 200, 0), (sx, sy), (tip_x, tip_y), 4)
        # Bright core
        pygame.draw.line(screen, (100, 255, 100), (sx, sy), (tip_x, tip_y), 2)
        # Bright tip
        pygame.draw.circle(screen, (200, 255, 200), (int(tip_x), int(tip_y)), 3)

    def _draw_minigun(self, screen, sx, sy):
        """Draw minigun bullet - small fast brass"""
        bullet_length = 6
        bullet_width = 2
        tip_x = sx + math.cos(self.angle) * bullet_length
        tip_y = sy + math.sin(self.angle) * bullet_length
        pygame.draw.line(screen, (180, 140, 60), (sx, sy), (tip_x, tip_y), bullet_width)
        pygame.draw.circle(screen, (200, 160, 80), (int(tip_x), int(tip_y)), 2)

    def _draw_crossbow(self, screen, sx, sy):
        """Draw crossbow bolt/arrow"""
        bolt_length = 16
        # Shaft (brown)
        tip_x = sx + math.cos(self.angle) * bolt_length
        tip_y = sy + math.sin(self.angle) * bolt_length
        base_x = sx - math.cos(self.angle) * (bolt_length / 2)
        base_y = sy - math.sin(self.angle) * (bolt_length / 2)
        pygame.draw.line(screen, (120, 80, 40), (base_x, base_y), (tip_x, tip_y), 3)
        # Metal tip
        pygame.draw.line(screen, (150, 150, 150), (sx, sy), (tip_x, tip_y), 2)
        # Fletching at back
        fletch_angle1 = self.angle + 2.5
        fletch_angle2 = self.angle - 2.5
        f1_x = base_x + math.cos(fletch_angle1) * 5
        f1_y = base_y + math.sin(fletch_angle1) * 5
        f2_x = base_x + math.cos(fletch_angle2) * 5
        f2_y = base_y + math.sin(fletch_angle2) * 5
        pygame.draw.line(screen, (200, 50, 50), (base_x, base_y), (f1_x, f1_y), 2)
        pygame.draw.line(screen, (200, 50, 50), (base_x, base_y), (f2_x, f2_y), 2)

    def _draw_electric(self, screen, sx, sy):
        """Draw electric bolt - zigzag lightning"""
        # Electric blue core
        pygame.draw.circle(screen, (100, 150, 255), (int(sx), int(sy)), 6)
        pygame.draw.circle(screen, (200, 220, 255), (int(sx), int(sy)), 4)
        pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), 2)
        # Random lightning sparks
        for _ in range(3):
            spark_x = sx + random.randint(-8, 8)
            spark_y = sy + random.randint(-8, 8)
            pygame.draw.line(screen, (150, 200, 255), (int(sx), int(sy)), (int(spark_x), int(spark_y)), 1)

    def _draw_freeze(self, screen, sx, sy):
        """Draw freeze ray - ice blue crystal"""
        # Ice crystal shape
        pygame.draw.circle(screen, (150, 220, 255), (int(sx), int(sy)), 5)
        pygame.draw.circle(screen, (200, 240, 255), (int(sx), int(sy)), 3)
        # Crystal spikes
        for i in range(6):
            spike_angle = i * (math.pi / 3)
            spike_x = sx + math.cos(spike_angle) * 7
            spike_y = sy + math.sin(spike_angle) * 7
            pygame.draw.line(screen, (180, 230, 255), (int(sx), int(sy)), (int(spike_x), int(spike_y)), 1)

    def _draw_dual_pistols(self, screen, sx, sy):
        """Draw golden dual pistol bullet"""
        bullet_length = 8
        tip_x = sx + math.cos(self.angle) * bullet_length
        tip_y = sy + math.sin(self.angle) * bullet_length
        # Gold casing
        pygame.draw.line(screen, (255, 215, 0), (sx, sy), (tip_x, tip_y), 3)
        # Shine
        pygame.draw.line(screen, (255, 240, 150), (sx, sy), (tip_x, tip_y), 1)

    def _draw_throwing_knife(self, screen, sx, sy):
        """Draw spinning throwing knife"""
        knife_length = 12
        # Spinning effect using lifetime
        spin_angle = self.angle + (self.lifetime * 0.3)
        tip_x = sx + math.cos(spin_angle) * knife_length
        tip_y = sy + math.sin(spin_angle) * knife_length
        base_x = sx - math.cos(spin_angle) * (knife_length / 2)
        base_y = sy - math.sin(spin_angle) * (knife_length / 2)
        # Blade
        pygame.draw.line(screen, (192, 192, 192), (base_x, base_y), (tip_x, tip_y), 3)
        # Shine on blade
        pygame.draw.line(screen, (255, 255, 255), (sx, sy), (tip_x, tip_y), 1)


class Grenade:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 8
        self.damage = 150  # High explosive damage
        self.explosion_radius = 150  # Larger explosion radius
        self.lifetime = 90  # Explodes after ~1.5 seconds (more time to roll)
        self.color = (100, 80, 60)
        self.exploded = False
        self.roll_angle = 0  # For visual rolling effect

    def update(self):
        # Grenade rolls - slows down gradually like a ball
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Roll friction - slower deceleration for rolling effect
        if self.speed > 0.5:
            self.speed *= 0.98  # Gentler slowdown for rolling
        else:
            self.speed = 0  # Stop when very slow

        # Update roll angle for visual effect
        self.roll_angle += self.speed * 0.3

        self.lifetime -= 1

        # Keep in bounds and bounce off walls
        if self.x < self.radius:
            self.x = self.radius
            self.angle = math.pi - self.angle
            self.speed *= 0.7
        elif self.x > MAP_WIDTH - self.radius:
            self.x = MAP_WIDTH - self.radius
            self.angle = math.pi - self.angle
            self.speed *= 0.7
        if self.y < self.radius:
            self.y = self.radius
            self.angle = -self.angle
            self.speed *= 0.7
        elif self.y > MAP_HEIGHT - self.radius:
            self.y = MAP_HEIGHT - self.radius
            self.angle = -self.angle
            self.speed *= 0.7

    def should_explode(self):
        return self.lifetime <= 0 and not self.exploded

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Draw realistic grenade body (olive green)
        pygame.draw.circle(screen, (60, 80, 60), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(screen, (80, 100, 80), (int(sx), int(sy)), self.radius, 2)

        # Draw grenade segments (the textured lines)
        for i in range(4):
            seg_angle = self.roll_angle + i * (math.pi / 2)
            seg_x1 = sx + math.cos(seg_angle) * 2
            seg_y1 = sy + math.sin(seg_angle) * 2
            seg_x2 = sx + math.cos(seg_angle) * (self.radius - 1)
            seg_y2 = sy + math.sin(seg_angle) * (self.radius - 1)
            pygame.draw.line(screen, (50, 70, 50), (seg_x1, seg_y1), (seg_x2, seg_y2), 1)

        # Draw spoon/lever (flies off after throw but we keep it for visual)
        spoon_angle = self.roll_angle + 0.5
        spoon_x = sx + math.cos(spoon_angle) * (self.radius + 2)
        spoon_y = sy + math.sin(spoon_angle) * (self.radius + 2)
        spoon_end_x = spoon_x + math.cos(spoon_angle) * 6
        spoon_end_y = spoon_y + math.sin(spoon_angle) * 6
        pygame.draw.line(screen, (100, 100, 100), (spoon_x, spoon_y), (spoon_end_x, spoon_end_y), 2)

        # Draw fuse/top cap
        cap_x = sx + math.cos(self.roll_angle + math.pi) * (self.radius - 2)
        cap_y = sy + math.sin(self.roll_angle + math.pi) * (self.radius - 2)
        pygame.draw.circle(screen, (80, 80, 80), (int(cap_x), int(cap_y)), 3)

        # Draw fuse spark (blinking, gets faster as it gets close to exploding)
        blink_rate = 10 if self.lifetime > 30 else 5 if self.lifetime > 15 else 2
        if self.lifetime % blink_rate < blink_rate // 2 + 1:
            spark_x = cap_x + math.cos(self.roll_angle + math.pi) * 4
            spark_y = cap_y + math.sin(self.roll_angle + math.pi) * 4
            # Spark gets bigger and redder as it's about to explode
            spark_size = 3 if self.lifetime > 30 else 4 if self.lifetime > 15 else 5
            spark_color = ORANGE if self.lifetime > 30 else (255, 100, 0) if self.lifetime > 15 else RED
            pygame.draw.circle(screen, spark_color, (int(spark_x), int(spark_y)), spark_size)
            # Add glow effect when close to exploding
            if self.lifetime < 20:
                pygame.draw.circle(screen, (255, 200, 100), (int(spark_x), int(spark_y)), spark_size + 2, 1)


class SmokeGrenade:
    """Smoke grenade that creates a smoke cloud to block robot vision"""
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 8
        self.radius = 7
        self.lifetime = 60  # Pops after 1 second
        self.color = (100, 100, 100)
        self.popped = False
        self.roll_angle = 0

    def update(self):
        # Smoke grenade rolls
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Roll friction
        if self.speed > 0.5:
            self.speed *= 0.96
        else:
            self.speed = 0

        self.roll_angle += self.speed * 0.3
        self.lifetime -= 1

        # Bounce off walls
        if self.x < self.radius:
            self.x = self.radius
            self.angle = math.pi - self.angle
            self.speed *= 0.7
        elif self.x > MAP_WIDTH - self.radius:
            self.x = MAP_WIDTH - self.radius
            self.angle = math.pi - self.angle
            self.speed *= 0.7
        if self.y < self.radius:
            self.y = self.radius
            self.angle = -self.angle
            self.speed *= 0.7
        elif self.y > MAP_HEIGHT - self.radius:
            self.y = MAP_HEIGHT - self.radius
            self.angle = -self.angle
            self.speed *= 0.7

    def should_pop(self):
        return self.lifetime <= 0 and not self.popped

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Draw smoke grenade body (gray cylinder)
        pygame.draw.circle(screen, (80, 80, 90), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(screen, (100, 100, 110), (int(sx), int(sy)), self.radius, 2)

        # Draw stripe (to differentiate from regular grenade)
        stripe_y1 = sy - 2
        stripe_y2 = sy + 2
        pygame.draw.line(screen, (200, 200, 200), (sx - self.radius + 2, stripe_y1),
                        (sx + self.radius - 2, stripe_y1), 2)

        # Draw pin/cap
        cap_x = sx + math.cos(self.roll_angle + math.pi) * (self.radius - 2)
        cap_y = sy + math.sin(self.roll_angle + math.pi) * (self.radius - 2)
        pygame.draw.circle(screen, (60, 60, 60), (int(cap_x), int(cap_y)), 3)

        # Hissing indicator when about to pop
        if self.lifetime < 30:
            hiss_size = 2 if self.lifetime > 15 else 3
            hiss_x = cap_x + math.cos(self.roll_angle + math.pi) * 4
            hiss_y = cap_y + math.sin(self.roll_angle + math.pi) * 4
            pygame.draw.circle(screen, (180, 180, 180), (int(hiss_x), int(hiss_y)), hiss_size)


class SmokeCloud:
    """Smoke cloud effect that blocks robot vision"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20  # Start small
        self.max_radius = 150  # Expands to this size
        self.lifetime = 300  # 5 seconds at 60fps
        self.max_lifetime = 300
        self.particles = []
        self.expanding = True

        # Create smoke particles - use very few particles for web performance
        for _ in range(8):
            self.particles.append({
                'offset_x': random.uniform(-40, 40),
                'offset_y': random.uniform(-40, 40),
                'size': random.randint(25, 45),
                'drift_x': random.uniform(-0.2, 0.2),
                'drift_y': random.uniform(-0.3, -0.1),  # Smoke rises
                'gray': random.randint(140, 180)  # Pre-compute gray value
            })

    def update(self):
        self.lifetime -= 1

        # Expand smoke cloud
        if self.expanding and self.radius < self.max_radius:
            self.radius += 5
        elif self.radius >= self.max_radius:
            self.expanding = False

        # Fade out in last second
        if self.lifetime < 60:
            self.radius = max(10, self.radius - 2)

        # Update particles (drift)
        for p in self.particles:
            p['offset_x'] += p['drift_x']
            p['offset_y'] += p['drift_y']

    def is_done(self):
        return self.lifetime <= 0

    def point_in_smoke(self, x, y):
        """Check if a point is inside the smoke cloud - optimized without sqrt"""
        dx = x - self.x
        dy = y - self.y
        return (dx * dx + dy * dy) < (self.radius * self.radius)

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Calculate alpha based on lifetime
        alpha_mult = min(1.0, self.lifetime / 60) if self.lifetime < 60 else 1.0

        # Draw smoke particles - use pre-computed gray values
        scale = self.radius / self.max_radius
        for p in self.particles:
            px = sx + p['offset_x'] * scale
            py = sy + p['offset_y'] * scale
            size = int(p['size'] * scale)

            if size > 0:
                # Use pre-computed gray value
                gray = p['gray']
                pygame.draw.circle(screen, (gray, gray, gray), (int(px), int(py)), size)

        # Draw outer boundary (faint)
        pygame.draw.circle(screen, (160, 160, 160), (int(sx), int(sy)), int(self.radius), 2)


class Explosion:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.max_radius = radius
        self.current_radius = 10
        self.lifetime = 20
        self.growing = True

    def update(self):
        if self.growing:
            self.current_radius += 15
            if self.current_radius >= self.max_radius:
                self.growing = False
        self.lifetime -= 1

    def is_done(self):
        return self.lifetime <= 0

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        # Draw explosion rings
        alpha = int(255 * (self.lifetime / 20))
        for i in range(3):
            r = max(0, self.current_radius - i * 20)
            if r > 0:
                color = (255, min(255, 100 + i * 50), 0)
                pygame.draw.circle(screen, color, (int(sx), int(sy)), int(r), 4)
        # Center flash
        if self.lifetime > 15:
            pygame.draw.circle(screen, WHITE, (int(sx), int(sy)), int(self.current_radius * 0.3))


class HealingEffect:
    """Visual effect when using a medkit"""
    # Class-level cached font and text
    _cached_font = None
    _cached_text = None

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = 60  # 1 second at 60fps
        self.max_lifetime = 60
        self.particles = []
        self.ring_radius = 0
        self.max_ring_radius = 50

        # Create healing particles
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(20, 60)
            speed = random.uniform(0.5, 1.5)
            self.particles.append({
                'angle': angle,
                'distance': distance,
                'speed': speed,
                'size': random.randint(3, 6),
                'offset': random.uniform(0, math.pi * 2)
            })

    def update(self, player_x, player_y):
        """Update effect position to follow player"""
        self.x = player_x
        self.y = player_y
        self.lifetime -= 1

        # Expand ring
        progress = 1 - (self.lifetime / self.max_lifetime)
        self.ring_radius = self.max_ring_radius * progress

        # Update particles (move towards center)
        for p in self.particles:
            p['distance'] -= p['speed']
            if p['distance'] < 0:
                p['distance'] = 0

        return self.lifetime > 0

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        progress = 1 - (self.lifetime / self.max_lifetime)

        # Draw healing ring expanding outward
        if self.ring_radius > 0:
            ring_alpha = int(255 * (1 - progress))
            # Green healing ring
            pygame.draw.circle(screen, (50, 255, 100), (int(sx), int(sy)), int(self.ring_radius), 3)
            # Inner ring
            inner_radius = self.ring_radius * 0.7
            if inner_radius > 5:
                pygame.draw.circle(screen, (100, 255, 150), (int(sx), int(sy)), int(inner_radius), 2)

        # Draw healing particles floating towards player
        for p in self.particles:
            if p['distance'] > 0:
                # Particles spiral inward
                wobble = math.sin(self.lifetime * 0.2 + p['offset']) * 5
                px = sx + math.cos(p['angle']) * (p['distance'] + wobble)
                py = sy + math.sin(p['angle']) * (p['distance'] + wobble)

                # Green healing particle with glow
                glow_size = p['size'] + 2
                pygame.draw.circle(screen, (100, 255, 150), (int(px), int(py)), glow_size)
                pygame.draw.circle(screen, (150, 255, 200), (int(px), int(py)), p['size'])
                pygame.draw.circle(screen, (200, 255, 220), (int(px), int(py)), max(1, p['size'] - 2))

        # Draw plus sign in center when healing
        if self.lifetime > 30:
            plus_size = 15
            plus_width = 4
            # Vertical line of plus
            pygame.draw.line(screen, (50, 255, 100),
                           (sx, sy - plus_size), (sx, sy + plus_size), plus_width)
            # Horizontal line of plus
            pygame.draw.line(screen, (50, 255, 100),
                           (sx - plus_size, sy), (sx + plus_size, sy), plus_width)
            # White center
            pygame.draw.line(screen, (200, 255, 220),
                           (sx, sy - plus_size + 2), (sx, sy + plus_size - 2), 2)
            pygame.draw.line(screen, (200, 255, 220),
                           (sx - plus_size + 2, sy), (sx + plus_size - 2, sy), 2)

        # Draw health restore text floating up
        if self.lifetime > 40:
            text_y_offset = (self.max_lifetime - self.lifetime) * 0.5
            # Use cached font and text
            if HealingEffect._cached_font is None:
                HealingEffect._cached_font = pygame.font.Font(None, 28)
                HealingEffect._cached_text = HealingEffect._cached_font.render("+HEAL", True, (100, 255, 150))
            screen.blit(HealingEffect._cached_text, (sx - HealingEffect._cached_text.get_width()//2, sy - 50 - text_y_offset))


class Robot:
    # Class-level cached fonts for boss health bar
    _boss_font = None
    _boss_text = None

    def __init__(self, x, y, difficulty, knife_only=False, bot_type="gun"):
        self.x = x
        self.y = y
        self.settings = DIFFICULTY[difficulty]
        self.health = self.settings["health"]
        self.max_health = self.settings["health"]
        self.speed = self.settings["speed"]
        self.bot_type = bot_type  # "gun", "knife", "throwing_knife", "dual_pistol"

        # Override knife_only if bot_type is knife
        if bot_type == "knife":
            knife_only = True

        # Knife-only bots are slightly faster to chase player
        if knife_only:
            self.speed = self.speed * 1.2

        # Throwing knife bots are medium speed with ranged attacks
        if bot_type == "throwing_knife":
            self.speed = self.speed * 0.9
            self.color = (192, 192, 192)  # Silver color
        # Dual pistol bots are faster and more aggressive
        elif bot_type == "dual_pistol":
            self.speed = self.speed * 1.1
            self.color = (255, 215, 0)  # Gold color
        else:
            self.color = self.settings["color"]

        self.fire_cooldown = 0
        self.fire_rate = self.settings["fire_rate"]

        # Dual pistol bots fire faster
        if bot_type == "dual_pistol":
            self.fire_rate = max(15, self.fire_rate // 2)
        # Throwing knife bots fire slower but deal more damage
        elif bot_type == "throwing_knife":
            self.fire_rate = self.fire_rate + 20

        self.radius = 20
        self.angle = 0
        self.difficulty = difficulty
        self.state = "patrol"
        self.patrol_target = self.get_patrol_target()
        self.hit_flash = 0
        self.knife_cooldown = 0
        self.knife_damage = 15
        self.knife_range = 50
        self.knife_only = knife_only  # If True, this robot only uses knife
        self.headshot_radius = 8  # Red dot target size for sniper headshots
        self.headshot_offset_y = -35  # Position above robot (above health bar)
        self.show_sniper_target = False  # Whether to show red dot (set by game when sniper is equipped)
        self.freeze_timer = 0  # Freeze effect from freeze ray
        self.base_speed = self.speed  # Store original speed

    def get_patrol_target(self):
        margin = 100
        return (
            random.randint(margin, MAP_WIDTH - margin),
            random.randint(margin, MAP_HEIGHT - margin)
        )

    def update(self, player_x, player_y, obstacles):
        # Handle freeze timer
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            self.speed = self.base_speed * 0.3  # 70% slow when frozen
        else:
            self.speed = self.base_speed

        # Distance to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        # State machine - knife bots have longer detection range
        detect_range = 600 if self.knife_only else 400
        attack_range = 300

        if dist < detect_range:
            self.state = "chase"
            if dist < attack_range:
                self.state = "attack"
        else:
            self.state = "patrol"

        # Movement
        if self.state == "patrol":
            tx, ty = self.patrol_target
            dx = tx - self.x
            dy = ty - self.y
            dist_to_target = math.sqrt(dx*dx + dy*dy)

            if dist_to_target < 50:
                self.patrol_target = self.get_patrol_target()
            elif dist_to_target > 0:
                self.x += (dx / dist_to_target) * self.speed * 0.5
                self.y += (dy / dist_to_target) * self.speed * 0.5
                self.angle = math.atan2(dy, dx)

        elif self.state == "chase":
            # Recalculate dx/dy for player direction
            dx = player_x - self.x
            dy = player_y - self.y
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            self.angle = math.atan2(dy, dx)

        elif self.state == "attack":
            # Recalculate dx/dy for player direction
            dx = player_x - self.x
            dy = player_y - self.y
            self.angle = math.atan2(dy, dx)
            # Knife bots keep chasing even in attack state
            if self.knife_only and dist > self.knife_range:
                if dist > 0:
                    self.x += (dx / dist) * self.speed
                    self.y += (dy / dist) * self.speed

        # Keep in bounds
        self.x = max(self.radius + 50, min(MAP_WIDTH - self.radius - 50, self.x))
        self.y = max(self.radius + 50, min(MAP_HEIGHT - self.radius - 50, self.y))

        # Check obstacle collision
        for obs in obstacles:
            if obs.collides_circle(self.x, self.y, self.radius):
                # Push out of obstacle
                ox = obs.x + obs.width / 2
                oy = obs.y + obs.height / 2
                push_x = self.x - ox
                push_y = self.y - oy
                push_dist = math.sqrt(push_x*push_x + push_y*push_y)
                if push_dist > 0:
                    self.x += (push_x / push_dist) * 5
                    self.y += (push_y / push_dist) * 5

        # Fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        # Knife cooldown
        if self.knife_cooldown > 0:
            self.knife_cooldown -= 1

        # Hit flash
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def can_knife(self, player_x, player_y):
        """Check if robot can use knife attack"""
        # Gun bots cannot use knife
        if not self.knife_only:
            return False
        if self.knife_cooldown > 0:
            return False
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.knife_range

    def knife_attack(self):
        """Perform knife attack"""
        self.knife_cooldown = 30  # Cooldown for knife
        return self.knife_damage

    def can_shoot(self):
        # Knife-only bots cannot shoot
        if self.knife_only:
            return False
        return self.fire_cooldown <= 0 and self.state == "attack"

    def shoot(self, player_x, player_y):
        self.fire_cooldown = self.fire_rate

        # Add inaccuracy
        accuracy = 0.3 if self.difficulty == "easy" else 0.15 if self.difficulty == "medium" else 0.08
        angle = self.angle + random.uniform(-accuracy, accuracy)

        # Different weapon types for different bot types
        if self.bot_type == "throwing_knife":
            bullet = Bullet(self.x, self.y, angle, False, False, "Enemy_Knife")
            bullet.damage = 25  # Higher damage for throwing knives
            bullet.speed = 12
            return bullet
        elif self.bot_type == "dual_pistol":
            # Dual pistols shoot two bullets with slight angle offset
            bullets = []
            for offset in [-0.1, 0.1]:
                bullet = Bullet(self.x, self.y, angle + offset, False, False, "Enemy_Pistol")
                bullet.damage = 8  # Lower damage per bullet
                bullet.speed = 14
                bullets.append(bullet)
            return bullets
        else:
            return Bullet(self.x, self.y, angle, False, False, "Enemy")

    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 10
        return self.health <= 0

    def check_headshot(self, bullet_x, bullet_y):
        """Check if bullet hits the headshot target (red dot above robot)"""
        headshot_x = self.x
        headshot_y = self.y + self.headshot_offset_y
        dx = bullet_x - headshot_x
        dy = bullet_y - headshot_y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.headshot_radius + 5  # 5 is bullet radius

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Only draw if on screen
        if -50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50:
            # Body color (flash white when hit, blue when frozen)
            if self.hit_flash > 0:
                body_color = WHITE
            elif self.freeze_timer > 0:
                body_color = (100, 150, 255)  # Ice blue when frozen
            else:
                body_color = self.color

            # Draw body
            pygame.draw.circle(screen, body_color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(screen, DARK_GRAY, (int(sx), int(sy)), self.radius, 2)

            # Draw ice crystals when frozen
            if self.freeze_timer > 0:
                for i in range(4):
                    crystal_angle = i * (math.pi / 2) + (self.freeze_timer * 0.02)
                    cx = sx + math.cos(crystal_angle) * (self.radius + 5)
                    cy = sy + math.sin(crystal_angle) * (self.radius + 5)
                    pygame.draw.circle(screen, (200, 240, 255), (int(cx), int(cy)), 3)

            # Draw two red eyes
            eye_offset = 6  # Distance between eyes
            eye_dist = 8  # Distance from center

            # Left eye
            left_eye_angle = self.angle + 0.4
            left_eye_x = sx + math.cos(left_eye_angle) * eye_dist
            left_eye_y = sy + math.sin(left_eye_angle) * eye_dist
            pygame.draw.circle(screen, RED, (int(left_eye_x), int(left_eye_y)), 4)
            pygame.draw.circle(screen, (150, 0, 0), (int(left_eye_x), int(left_eye_y)), 2)

            # Right eye
            right_eye_angle = self.angle - 0.4
            right_eye_x = sx + math.cos(right_eye_angle) * eye_dist
            right_eye_y = sy + math.sin(right_eye_angle) * eye_dist
            pygame.draw.circle(screen, RED, (int(right_eye_x), int(right_eye_y)), 4)
            pygame.draw.circle(screen, (150, 0, 0), (int(right_eye_x), int(right_eye_y)), 2)

            # Draw weapon based on bot type
            if self.knife_only:
                # Draw knife - shorter and silver colored
                knife_length = self.radius + 8
                knife_x = sx + math.cos(self.angle) * knife_length
                knife_y = sy + math.sin(self.angle) * knife_length
                pygame.draw.line(screen, (192, 192, 192), (sx, sy), (knife_x, knife_y), 3)
                # Draw knife tip
                tip_x = sx + math.cos(self.angle) * (knife_length + 4)
                tip_y = sy + math.sin(self.angle) * (knife_length + 4)
                pygame.draw.line(screen, WHITE, (knife_x, knife_y), (tip_x, tip_y), 2)
            elif self.bot_type == "throwing_knife":
                # Draw multiple throwing knives on back (like a bandolier)
                for i in range(-1, 2):
                    offset_angle = self.angle + math.pi + (i * 0.3)
                    kx = sx + math.cos(offset_angle) * (self.radius - 5)
                    ky = sy + math.sin(offset_angle) * (self.radius - 5)
                    ktx = kx + math.cos(offset_angle) * 8
                    kty = ky + math.sin(offset_angle) * 8
                    pygame.draw.line(screen, (192, 192, 192), (kx, ky), (ktx, kty), 2)
                # Draw arm with knife ready to throw
                arm_x = sx + math.cos(self.angle) * (self.radius + 5)
                arm_y = sy + math.sin(self.angle) * (self.radius + 5)
                pygame.draw.line(screen, (150, 150, 150), (sx, sy), (arm_x, arm_y), 4)
            elif self.bot_type == "dual_pistol":
                # Draw two guns (dual pistols)
                for offset in [0.4, -0.4]:
                    gun_angle = self.angle + offset
                    gun_start_x = sx + math.cos(gun_angle) * 5
                    gun_start_y = sy + math.sin(gun_angle) * 5
                    gun_length = self.radius + 8
                    gun_x = sx + math.cos(gun_angle) * gun_length
                    gun_y = sy + math.sin(gun_angle) * gun_length
                    pygame.draw.line(screen, (255, 215, 0), (gun_start_x, gun_start_y), (gun_x, gun_y), 4)
                    # Gold tip
                    pygame.draw.circle(screen, (255, 240, 150), (int(gun_x), int(gun_y)), 2)
            else:
                # Draw standard gun
                gun_length = self.radius + 10
                gun_x = sx + math.cos(self.angle) * gun_length
                gun_y = sy + math.sin(self.angle) * gun_length
                pygame.draw.line(screen, DARK_GRAY, (sx, sy), (gun_x, gun_y), 6)

            # Health bar
            bar_width = 40
            bar_height = 6
            bar_x = sx - bar_width // 2
            bar_y = sy - self.radius - 15

            pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            health_width = int((self.health / self.max_health) * bar_width)
            health_color = GREEN if self.health > self.max_health * 0.5 else YELLOW if self.health > self.max_health * 0.25 else RED
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

            # Sniper headshot target (red dot above health bar) - only shows when sniper is equipped
            if self.show_sniper_target:
                headshot_x = int(sx)
                headshot_y = int(sy + self.headshot_offset_y)
                # Outer ring
                pygame.draw.circle(screen, (200, 0, 0), (headshot_x, headshot_y), self.headshot_radius, 2)
                # Inner dot
                pygame.draw.circle(screen, RED, (headshot_x, headshot_y), 4)


class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 1000
        self.max_health = 1000
        self.speed = 2
        self.radius = 50  # Much bigger than normal robots
        self.angle = 0
        self.fire_cooldown = 0
        self.fire_rate = 20  # Faster shooting
        self.hit_flash = 0
        self.attack_pattern = 0
        self.pattern_timer = 0
        self.charge_speed = 8
        self.is_charging = False
        self.charge_target = None
        self.headshot_radius = 12  # Bigger target for boss
        self.headshot_offset_y = -70  # Position above boss
        self.show_sniper_target = False  # Whether to show red dot (set by game when sniper is equipped)

    def update(self, player_x, player_y, obstacles):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        self.angle = math.atan2(dy, dx)

        # Pattern switching
        self.pattern_timer += 1
        if self.pattern_timer > 180:  # Switch pattern every 3 seconds
            self.pattern_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 3
            self.is_charging = False

        # Movement based on attack pattern
        if self.attack_pattern == 0:
            # Chase player slowly
            if dist > 100:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
        elif self.attack_pattern == 1:
            # Charge attack
            if not self.is_charging and self.pattern_timer == 1:
                self.is_charging = True
                self.charge_target = (player_x, player_y)
            if self.is_charging and self.charge_target:
                cdx = self.charge_target[0] - self.x
                cdy = self.charge_target[1] - self.y
                cdist = math.sqrt(cdx*cdx + cdy*cdy)
                if cdist > 20:
                    self.x += (cdx / cdist) * self.charge_speed
                    self.y += (cdy / cdist) * self.charge_speed
                else:
                    self.is_charging = False
        elif self.attack_pattern == 2:
            # Circle strafe
            strafe_angle = self.angle + math.pi / 2
            self.x += math.cos(strafe_angle) * self.speed * 1.5
            self.y += math.sin(strafe_angle) * self.speed * 1.5

        # Keep in bounds
        self.x = max(self.radius + 50, min(MAP_WIDTH - self.radius - 50, self.x))
        self.y = max(self.radius + 50, min(MAP_HEIGHT - self.radius - 50, self.y))

        # Cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def can_shoot(self):
        return self.fire_cooldown <= 0

    def shoot(self, player_x, player_y):
        self.fire_cooldown = self.fire_rate
        bullets = []

        # Boss shoots multiple bullets in a spread
        spread = 5
        for i in range(spread):
            angle_offset = (i - spread // 2) * 0.15
            angle = self.angle + angle_offset
            bullet = Bullet(self.x, self.y, angle, False, False, "Enemy")
            bullet.damage = 15
            bullet.speed = 10
            bullets.append(bullet)

        return bullets

    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 10
        return self.health <= 0

    def check_headshot(self, bullet_x, bullet_y):
        """Check if bullet hits the headshot target (red dot above boss)"""
        headshot_x = self.x
        headshot_y = self.y + self.headshot_offset_y
        dx = bullet_x - headshot_x
        dy = bullet_y - headshot_y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.headshot_radius + 5  # 5 is bullet radius

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        if -100 < sx < SCREEN_WIDTH + 100 and -100 < sy < SCREEN_HEIGHT + 100:
            # Body color (flash white when hit)
            body_color = WHITE if self.hit_flash > 0 else (150, 0, 150)

            # Draw body - bigger circle with outline
            pygame.draw.circle(screen, body_color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(screen, (100, 0, 100), (int(sx), int(sy)), self.radius, 4)

            # Draw evil eyes
            eye_offset = 15
            for ex in [-1, 1]:
                eye_x = sx + ex * eye_offset + math.cos(self.angle) * 10
                eye_y = sy + math.sin(self.angle) * 10
                pygame.draw.circle(screen, RED, (int(eye_x), int(eye_y)), 10)
                pygame.draw.circle(screen, BLACK, (int(eye_x), int(eye_y)), 5)

            # Draw gun (bigger)
            gun_length = self.radius + 20
            gun_x = sx + math.cos(self.angle) * gun_length
            gun_y = sy + math.sin(self.angle) * gun_length
            pygame.draw.line(screen, DARK_GRAY, (sx, sy), (gun_x, gun_y), 12)

            # Sniper headshot target (bigger red dot for boss) - only shows when sniper is equipped
            if self.show_sniper_target:
                headshot_x = int(sx)
                headshot_y = int(sy + self.headshot_offset_y)
                # Outer ring
                pygame.draw.circle(screen, (200, 0, 0), (headshot_x, headshot_y), self.headshot_radius, 3)
                # Inner dot
                pygame.draw.circle(screen, RED, (headshot_x, headshot_y), 6)

            # Health bar (bigger, at top of screen when boss is active)
            bar_width = 400
            bar_height = 20
            bar_x = SCREEN_WIDTH // 2 - bar_width // 2
            bar_y = 50

            pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
            health_width = int((self.health / self.max_health) * bar_width)
            pygame.draw.rect(screen, (150, 0, 150), (bar_x, bar_y, health_width, bar_height))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

            # Boss name (cached for performance)
            if Robot._boss_font is None:
                Robot._boss_font = pygame.font.Font(None, 36)
                Robot._boss_text = Robot._boss_font.render("BOSS", True, (150, 0, 150))
            screen.blit(Robot._boss_text, (SCREEN_WIDTH // 2 - Robot._boss_text.get_width() // 2, 25))


class Obstacle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = BROWN

    def collides_circle(self, cx, cy, radius):
        # Find closest point on rectangle to circle
        closest_x = max(self.x, min(cx, self.x + self.width))
        closest_y = max(self.y, min(cy, self.y + self.height))

        dx = cx - closest_x
        dy = cy - closest_y
        return (dx * dx + dy * dy) < (radius * radius)

    def collides_point(self, px, py):
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Only draw if on screen
        if sx + self.width > 0 and sx < SCREEN_WIDTH and sy + self.height > 0 and sy < SCREEN_HEIGHT:
            pygame.draw.rect(screen, self.color, (sx, sy, self.width, self.height))
            pygame.draw.rect(screen, DARK_GRAY, (sx, sy, self.width, self.height), 3)


class ShellCasing:
    """Ejected shell casing particle"""
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        # Eject to the right of the gun
        eject_angle = angle + math.pi / 2 + random.uniform(-0.3, 0.3)
        speed = random.uniform(3, 6)
        self.vx = math.cos(eject_angle) * speed
        self.vy = math.sin(eject_angle) * speed
        self.rotation = random.uniform(0, math.pi * 2)
        self.rot_speed = random.uniform(-0.5, 0.5)
        self.life = 60  # frames
        self.size = random.uniform(3, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92  # friction
        self.vy *= 0.92
        self.vy += 0.15  # gravity
        self.rotation += self.rot_speed
        self.life -= 1
        return self.life > 0

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        # Draw brass colored shell
        alpha = min(255, self.life * 8)
        color = (200, 160, 60)
        # Draw as small rectangle
        points = []
        for i in range(4):
            angle = self.rotation + i * math.pi / 2
            px = sx + math.cos(angle) * self.size
            py = sy + math.sin(angle) * self.size * 0.4
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(screen, color, points)


class MuzzleFlash:
    """Muzzle flash effect"""
    def __init__(self, x, y, angle, size=1.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.life = 4  # Very short
        self.size = size

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        # Draw flash as bright yellow/orange burst
        flash_length = 20 * self.size * (self.life / 4)
        flash_width = 12 * self.size * (self.life / 4)

        # Main flash
        end_x = sx + math.cos(self.angle) * flash_length
        end_y = sy + math.sin(self.angle) * flash_length

        # Draw multiple layers for glow effect
        for i in range(3):
            width = int(flash_width * (1 - i * 0.3))
            if i == 0:
                color = (255, 255, 200)  # White center
            elif i == 1:
                color = (255, 200, 50)   # Yellow
            else:
                color = (255, 100, 0)    # Orange edge
            pygame.draw.line(screen, color, (sx, sy), (end_x, end_y), max(1, width))

        # Side sparks
        for i in range(3):
            spark_angle = self.angle + random.uniform(-0.5, 0.5)
            spark_len = flash_length * random.uniform(0.3, 0.7)
            spark_x = sx + math.cos(spark_angle) * spark_len
            spark_y = sy + math.sin(spark_angle) * spark_len
            pygame.draw.line(screen, (255, 200, 100), (sx, sy), (spark_x, spark_y), 2)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 18
        self.speed = 5
        self.angle = 0
        self.health = 100
        self.max_health = 100
        self.hit_flash = 0
        self.fire_cooldown = 0

        # Recoil system
        self.recoil = 0  # Current recoil offset
        self.recoil_recovery = 0.85  # How fast recoil recovers

        # Reload animation system
        self.reloading = False
        self.reload_timer = 0
        self.reload_duration = 60  # frames (1 second at 60fps)
        self.reload_phase = 0  # 0-1 progress through reload

        # Weapon animation system
        self.anim_timer = 0  # Global animation timer
        self.minigun_rotation = 0  # Minigun barrel rotation angle
        self.is_firing = False  # Track if currently firing

        # Avatar system
        self.avatar_type = "default"  # Will be loaded from save
        self.avatar = Avatar("default")
        self.owned_avatars = ["default"]  # Player always owns default avatar
        self.walk_speed = 0  # For walk animation
        self.last_x = x
        self.last_y = y

        # Weapon system with realistic stats
        self.current_weapon = 0
        self.recoil = 0  # Current recoil offset (visual kickback)
        self.max_recoil = 0  # Max recoil for current weapon
        self.weapons = [
            # Rifle - 30 round mag, automatic
            {"name": "Rifle", "ammo": 30, "max_ammo": 30, "reloads": 5, "fire_rate": 6, "damage": 28,
             "bullet_speed": 22, "color": (255, 220, 100), "gun_length": 24, "gun_width": 5,
             "melee": False, "grenade": False, "recoil": 3, "reload_time": 90},
            # Handgun - 17 round mag, semi-auto
            {"name": "Handgun", "ammo": 17, "max_ammo": 17, "reloads": 6, "fire_rate": 8, "damage": 18,
             "bullet_speed": 20, "color": (255, 200, 100), "gun_length": 10, "gun_width": 4,
             "melee": False, "grenade": False, "recoil": 2, "reload_time": 60},
            # Knife - melee weapon (high damage, close range)
            {"name": "Knife", "ammo": 999, "max_ammo": 999, "reloads": 999, "fire_rate": 15,
             "damage": 75, "bullet_speed": 0, "color": WHITE, "gun_length": 12, "gun_width": 3,
             "melee": True, "grenade": False, "recoil": 0},
            # Grenade - explosive
            {"name": "Grenade", "ammo": 4, "max_ammo": 4, "reloads": 0, "fire_rate": 50, "damage": 150,
             "bullet_speed": 0, "color": (80, 100, 80), "gun_length": 6, "gun_width": 6,
             "melee": False, "grenade": True, "no_reload": True, "recoil": 0},
            # Smoke Grenade - creates smoke cloud to block robot vision
            {"name": "Smoke", "ammo": 3, "max_ammo": 3, "reloads": 0, "fire_rate": 50, "damage": 0,
             "bullet_speed": 0, "color": (120, 120, 130), "gun_length": 6, "gun_width": 6,
             "melee": False, "grenade": False, "smoke_grenade": True, "no_reload": True, "recoil": 0}
        ]

        # Load saved coins and unlocked weapons
        (saved_coins, saved_rpg, saved_shotgun, saved_medkit_charges, saved_sniper,
         saved_flamethrower, saved_laser, saved_minigun, saved_crossbow,
         saved_electric, saved_freeze, saved_dual_pistols, saved_throwing_knives,
         saved_avatar, saved_owned_avatars) = load_save()
        self.coins = saved_coins
        self.has_rpg = saved_rpg
        self.has_shotgun = saved_shotgun
        self.has_sniper = saved_sniper
        self.medkit_charges = saved_medkit_charges  # Number of heals available
        self.has_flamethrower = saved_flamethrower
        self.has_laser = saved_laser
        self.has_minigun = saved_minigun
        self.has_crossbow = saved_crossbow
        self.has_electric = saved_electric
        self.has_freeze = saved_freeze
        self.has_dual_pistols = saved_dual_pistols
        self.has_throwing_knives = saved_throwing_knives
        # Load avatar settings
        self.avatar_type = saved_avatar
        self.avatar = Avatar(saved_avatar)
        self.owned_avatars = saved_owned_avatars if saved_owned_avatars else ["default"]

        # Shotgun - pump-action, 8 shell mag
        if self.has_shotgun:
            self.weapons.append({
                "name": "Shotgun",
                "ammo": 8,
                "max_ammo": 8,
                "reloads": 4,
                "fire_rate": 35,  # Pump action delay
                "damage": 65,  # Per pellet, spread damage
                "bullet_speed": 18,
                "color": (255, 140, 50),
                "gun_length": 28,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "shotgun": True,
                "recoil": 6,
                "reload_time": 120
            })

        # RPG - rocket launcher
        if self.has_rpg:
            self.weapons.append({
                "name": "RPG",
                "ammo": 1,
                "max_ammo": 1,
                "reloads": 8,
                "fire_rate": 90,  # Slow reload between shots
                "damage": 200,  # Massive explosive damage
                "bullet_speed": 12,
                "color": (255, 80, 50),
                "gun_length": 32,
                "gun_width": 8,
                "melee": False,
                "grenade": False,
                "recoil": 8,
                "reload_time": 150
            })

        # Sniper - high damage, slow fire
        if self.has_sniper:
            self.weapons.append({
                "name": "Sniper",
                "ammo": 10,
                "max_ammo": 10,
                "reloads": 3,
                "fire_rate": 50,  # Bolt action style
                "damage": 180,  # One-shot potential
                "bullet_speed": 35,  # Very fast
                "color": (100, 255, 255),
                "gun_length": 38,
                "gun_width": 5,
                "melee": False,
                "grenade": False,
                "recoil": 10,  # Heavy recoil
                "reload_time": 120
            })

        # Flamethrower - continuous fire stream
        if self.has_flamethrower:
            self.weapons.append({
                "name": "Flamethrower",
                "ammo": 100,
                "max_ammo": 100,
                "reloads": 2,
                "fire_rate": 2,  # Continuous stream
                "damage": 12,  # DOT damage
                "bullet_speed": 10,
                "color": (255, 120, 30),
                "gun_length": 26,
                "gun_width": 7,
                "melee": False,
                "grenade": False,
                "flamethrower": True,
                "recoil": 1,
                "reload_time": 180
            })

        # Laser Gun - fast energy weapon
        if self.has_laser:
            self.weapons.append({
                "name": "Laser Gun",
                "ammo": 50,
                "max_ammo": 50,
                "reloads": 4,
                "fire_rate": 3,
                "damage": 18,
                "bullet_speed": 50,  # Light speed (instant)
                "color": (50, 255, 50),
                "gun_length": 22,
                "gun_width": 5,
                "melee": False,
                "grenade": False,
                "laser": True,
                "recoil": 0,  # No recoil
                "reload_time": 90
            })

        # Minigun - rotary machine gun, very fast fire
        if self.has_minigun:
            self.weapons.append({
                "name": "Minigun",
                "ammo": 200,
                "max_ammo": 200,
                "reloads": 2,
                "fire_rate": 2,  # Very fast
                "damage": 15,
                "bullet_speed": 24,
                "color": (200, 180, 50),
                "gun_length": 30,
                "gun_width": 10,
                "melee": False,
                "grenade": False,
                "minigun": True,
                "recoil": 2,  # Constant mild recoil
                "reload_time": 180
            })

        # Crossbow - high damage bolts
        if self.has_crossbow:
            self.weapons.append({
                "name": "Crossbow",
                "ammo": 12,
                "max_ammo": 12,
                "reloads": 5,
                "fire_rate": 45,  # Slow reload
                "damage": 90,  # High damage per bolt
                "bullet_speed": 28,
                "color": (160, 82, 45),
                "gun_length": 20,
                "gun_width": 8,
                "melee": False,
                "grenade": False,
                "crossbow": True,
                "recoil": 1,
                "reload_time": 100
            })

        # Electric Gun - chain lightning weapon
        if self.has_electric:
            self.weapons.append({
                "name": "Electric Gun",
                "ammo": 30,
                "max_ammo": 30,
                "reloads": 4,
                "fire_rate": 12,
                "damage": 30,
                "bullet_speed": 25,
                "color": (100, 180, 255),
                "gun_length": 18,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "electric": True,
                "recoil": 2,
                "reload_time": 90
            })

        # Freeze Ray - slows enemies
        if self.has_freeze:
            self.weapons.append({
                "name": "Freeze Ray",
                "ammo": 40,
                "max_ammo": 40,
                "reloads": 4,
                "fire_rate": 6,
                "damage": 14,
                "bullet_speed": 18,
                "color": (150, 230, 255),
                "gun_length": 20,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "freeze": True,
                "recoil": 1,
                "reload_time": 90
            })

        # Dual Pistols - two guns at once
        if self.has_dual_pistols:
            self.weapons.append({
                "name": "Dual Pistols",
                "ammo": 14,  # 7 per gun
                "max_ammo": 14,
                "reloads": 6,
                "fire_rate": 6,
                "damage": 35,
                "bullet_speed": 22,
                "color": (255, 215, 0),
                "gun_length": 12,
                "gun_width": 5,
                "melee": False,
                "grenade": False,
                "dual_pistols": True,
                "recoil": 4,
                "reload_time": 80
            })

        # Throwing Knives - silent ranged attack
        if self.has_throwing_knives:
            self.weapons.append({
                "name": "Throwing Knives",
                "ammo": 16,
                "max_ammo": 16,
                "reloads": 8,
                "fire_rate": 10,
                "damage": 50,  # Silent but deadly
                "bullet_speed": 26,
                "color": (200, 200, 210),
                "gun_length": 10,
                "gun_width": 3,
                "melee": False,
                "grenade": False,
                "throwing_knife": True,
                "recoil": 0,  # Silent, no recoil
                "reload_time": 40
            })

    @property
    def weapon(self):
        return self.weapons[self.current_weapon]

    @property
    def ammo(self):
        return self.weapon["ammo"]

    @ammo.setter
    def ammo(self, value):
        self.weapon["ammo"] = value

    @property
    def max_ammo(self):
        return self.weapon["max_ammo"]

    def switch_weapon(self):
        # SIMPLE weapon switch - deferred to update() to avoid event loop issues
        # Just set a flag, actual switch happens in update()
        self._want_switch = True

    def unlock_shotgun(self):
        if not self.has_shotgun and self.coins >= 10:
            self.coins -= 10
            self.has_shotgun = True
            # Add Shotgun to weapons
            self.weapons.append({
                "name": "Shotgun",
                "ammo": 30,
                "max_ammo": 30,
                "reloads": 3,
                "fire_rate": 30,
                "damage": 50,  # Base damage, modified by distance
                "bullet_speed": 12,
                "color": ORANGE,
                "gun_length": 14,
                "gun_width": 7,
                "melee": False,
                "grenade": False,
                "shotgun": True
            })
            # Auto-save after buying Shotgun
            self.save_progress()
            return True
        return False

    def unlock_rpg(self):
        if not self.has_rpg and self.coins >= 50:
            self.coins -= 50
            self.has_rpg = True
            # Add RPG to weapons
            self.weapons.append({
                "name": "RPG",
                "ammo": 1,
                "max_ammo": 1,
                "reloads": 10,
                "fire_rate": 60,  # Very slow
                "damage": 50,
                "bullet_speed": 10,
                "color": RED,
                "gun_length": 18,
                "gun_width": 8
            })
            # Auto-save after buying RPG
            self.save_progress()
            return True
        return False

    def unlock_sniper(self):
        if not self.has_sniper and self.coins >= 150:
            self.coins -= 100
            self.has_sniper = True
            # Add Sniper to weapons
            self.weapons.append({
                "name": "Sniper",
                "ammo": 5,
                "max_ammo": 5,
                "reloads": 3,
                "fire_rate": 60,
                "damage": 150,
                "bullet_speed": 30,
                "color": (0, 255, 255),
                "gun_length": 20,
                "gun_width": 4,
                "melee": False,
                "grenade": False
            })
            # Auto-save after buying Sniper
            self.save_progress()
            return True
        return False

    def unlock_flamethrower(self):
        if not self.has_flamethrower and self.coins >= 80:
            self.coins -= 80
            self.has_flamethrower = True
            self.weapons.append({
                "name": "Flamethrower",
                "ammo": 100,
                "max_ammo": 100,
                "reloads": 3,
                "fire_rate": 2,
                "damage": 8,
                "bullet_speed": 8,
                "color": (255, 100, 0),
                "gun_length": 16,
                "gun_width": 8,
                "melee": False,
                "grenade": False,
                "flamethrower": True
            })
            self.save_progress()
            return True
        return False

    def unlock_laser(self):
        if not self.has_laser and self.coins >= 120:
            self.coins -= 120
            self.has_laser = True
            self.weapons.append({
                "name": "Laser",
                "ammo": 50,
                "max_ammo": 50,
                "reloads": 4,
                "fire_rate": 3,
                "damage": 15,
                "bullet_speed": 40,
                "color": (0, 255, 0),
                "gun_length": 14,
                "gun_width": 5,
                "melee": False,
                "grenade": False,
                "laser": True
            })
            self.save_progress()
            return True
        return False

    def unlock_minigun(self):
        if not self.has_minigun and self.coins >= 200:
            self.coins -= 200
            self.has_minigun = True
            self.weapons.append({
                "name": "Minigun",
                "ammo": 200,
                "max_ammo": 200,
                "reloads": 2,
                "fire_rate": 3,
                "damage": 12,
                "bullet_speed": 18,
                "color": (180, 180, 180),
                "gun_length": 18,
                "gun_width": 10,
                "melee": False,
                "grenade": False,
                "minigun": True
            })
            self.save_progress()
            return True
        return False

    def unlock_crossbow(self):
        if not self.has_crossbow and self.coins >= 100:
            self.coins -= 100
            self.has_crossbow = True
            self.weapons.append({
                "name": "Crossbow",
                "ammo": 15,
                "max_ammo": 15,
                "reloads": 5,
                "fire_rate": 40,
                "damage": 80,
                "bullet_speed": 25,
                "color": (139, 69, 19),
                "gun_length": 16,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "crossbow": True
            })
            self.save_progress()
            return True
        return False

    def unlock_electric(self):
        if not self.has_electric and self.coins >= 140:
            self.coins -= 140
            self.has_electric = True
            self.weapons.append({
                "name": "Electric",
                "ammo": 30,
                "max_ammo": 30,
                "reloads": 4,
                "fire_rate": 15,
                "damage": 25,
                "bullet_speed": 20,
                "color": (100, 150, 255),
                "gun_length": 14,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "electric": True
            })
            self.save_progress()
            return True
        return False

    def unlock_freeze(self):
        if not self.has_freeze and self.coins >= 110:
            self.coins -= 110
            self.has_freeze = True
            self.weapons.append({
                "name": "Freeze",
                "ammo": 40,
                "max_ammo": 40,
                "reloads": 4,
                "fire_rate": 8,
                "damage": 10,
                "bullet_speed": 15,
                "color": (150, 220, 255),
                "gun_length": 14,
                "gun_width": 6,
                "melee": False,
                "grenade": False,
                "freeze": True
            })
            self.save_progress()
            return True
        return False

    def unlock_dual_pistols(self):
        if not self.has_dual_pistols and self.coins >= 60:
            self.coins -= 60
            self.has_dual_pistols = True
            self.weapons.append({
                "name": "Dual Pistols",
                "ammo": 60,
                "max_ammo": 60,
                "reloads": 5,
                "fire_rate": 4,
                "damage": 12,
                "bullet_speed": 20,
                "color": (255, 215, 0),
                "gun_length": 8,
                "gun_width": 4,
                "melee": False,
                "grenade": False,
                "dual_pistols": True
            })
            self.save_progress()
            return True
        return False

    def unlock_throwing_knives(self):
        if not self.has_throwing_knives and self.coins >= 70:
            self.coins -= 70
            self.has_throwing_knives = True
            self.weapons.append({
                "name": "Throwing Knives",
                "ammo": 20,
                "max_ammo": 20,
                "reloads": 6,
                "fire_rate": 12,
                "damage": 40,
                "bullet_speed": 22,
                "color": (192, 192, 192),
                "gun_length": 8,
                "gun_width": 3,
                "melee": False,
                "grenade": False,
                "throwing_knife": True
            })
            self.save_progress()
            return True
        return False

    def add_coin(self, amount=1):
        self.coins += amount
        self.save_progress()  # Auto-save when coins are added

    def save_progress(self):
        """Save coins, weapon unlocks, and avatar data"""
        return save_game(self.coins, self.has_rpg, self.has_shotgun, self.medkit_charges, self.has_sniper,
                        self.has_flamethrower, self.has_laser, self.has_minigun, self.has_crossbow,
                        self.has_electric, self.has_freeze, self.has_dual_pistols, self.has_throwing_knives,
                        self.avatar_type, self.owned_avatars)

    def use_medkit(self):
        """Use a medkit charge to heal to full HP"""
        if self.medkit_charges > 0 and self.health < self.max_health:
            self.medkit_charges -= 1
            self.health = self.max_health
            self.save_progress()
            return True
        return False

    def update(self, keys, mouse_pos, camera, obstacles):
        # Movement (WASD and Arrow keys)
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed

        # Normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Try to move
        new_x = self.x + dx
        new_y = self.y + dy

        # Check obstacle collision
        can_move_x = True
        can_move_y = True

        for obs in obstacles:
            if obs.collides_circle(new_x, self.y, self.radius):
                can_move_x = False
            if obs.collides_circle(self.x, new_y, self.radius):
                can_move_y = False

        if can_move_x:
            self.x = max(self.radius + 50, min(MAP_WIDTH - self.radius - 50, new_x))
        if can_move_y:
            self.y = max(self.radius + 50, min(MAP_HEIGHT - self.radius - 50, new_y))

        # Aim at mouse (convert screen mouse to world position)
        world_mouse_x = mouse_pos[0] + camera.x
        world_mouse_y = mouse_pos[1] + camera.y
        self.angle = math.atan2(world_mouse_y - self.y, world_mouse_x - self.x)

        # Cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        else:
            self.is_firing = False  # Reset firing state when cooldown ends
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Update animation timer
        self.anim_timer += 1

        # Calculate walk speed for avatar animation
        move_dist = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        self.walk_speed = move_dist
        self.last_x = self.x
        self.last_y = self.y

        # Update minigun barrel rotation when firing
        weapon = self.weapons[self.current_weapon]
        if weapon["name"] == "Minigun" and self.is_firing:
            self.minigun_rotation += 0.5  # Spin fast when firing
        elif weapon["name"] == "Minigun":
            self.minigun_rotation += 0.1  # Slow spin when idle

        # Handle deferred weapon switch (avoids event loop blocking)
        if getattr(self, '_want_switch', False):
            self._want_switch = False
            if len(self.weapons) > 1:
                self.current_weapon = (self.current_weapon + 1) % len(self.weapons)
                self.fire_cooldown = 15

    def shoot(self):
        if self.fire_cooldown > 0:
            return None

        # Can't shoot while reloading
        if self.reloading:
            return None

        # Knife doesn't use ammo
        if not self.weapon.get("melee", False):
            if self.ammo <= 0:
                return None
            self.ammo -= 1

        self.fire_cooldown = self.weapon["fire_rate"]
        self.is_firing = True  # Mark as firing for animations

        # Melee weapon (knife) - return special melee attack
        if self.weapon.get("melee", False):
            return {"melee": True, "damage": self.weapon["damage"], "x": self.x, "y": self.y, "angle": self.angle}

        # Grenade - return grenade data
        if self.weapon.get("grenade", False):
            return {
                "grenade": True,
                "x": self.x + math.cos(self.angle) * (self.radius + 10),
                "y": self.y + math.sin(self.angle) * (self.radius + 10),
                "angle": self.angle
            }

        # Apply weapon-specific recoil
        weapon_recoil = self.weapon.get("recoil", 2)
        self.apply_recoil(weapon_recoil)

        is_shotgun = self.weapon.get("shotgun", False)
        weapon_name = self.weapon["name"]
        bullet = Bullet(
            self.x + math.cos(self.angle) * (self.radius + 10),
            self.y + math.sin(self.angle) * (self.radius + 10),
            self.angle,
            True,
            is_shotgun,
            weapon_name
        )
        bullet.speed = self.weapon["bullet_speed"]
        bullet.base_damage = self.weapon["damage"]
        bullet.damage = self.weapon["damage"]
        bullet.color = self.weapon["color"]
        bullet.caliber = self.weapon.get("caliber", "")  # Store caliber for visuals
        return bullet

    def take_damage(self, damage):
        self.health -= damage
        self.hit_flash = 10
        return self.health <= 0

    def update_recoil(self):
        """Update recoil recovery"""
        self.recoil *= self.recoil_recovery
        if self.recoil < 0.1:
            self.recoil = 0

    def apply_recoil(self, amount):
        """Apply recoil when shooting"""
        self.recoil = min(self.recoil + amount, 15)  # Cap recoil

    def set_avatar(self, avatar_type):
        """Change the player's avatar"""
        if avatar_type in AVATAR_TYPES:
            self.avatar_type = avatar_type
            self.avatar = Avatar(avatar_type)

    def start_reload(self):
        """Start the reload animation"""
        if not self.reloading and not self.weapon.get("no_reload", False):
            reloads = self.weapon.get("reloads", 0)
            if reloads > 0 and self.ammo < self.max_ammo:
                self.reloading = True
                # Use weapon-specific reload time or default
                self.reload_duration = self.weapon.get("reload_time", 60)
                self.reload_timer = self.reload_duration
                self.reload_phase = 0
                return True
        return False

    def update_reload(self):
        """Update reload animation"""
        if self.reloading:
            self.reload_timer -= 1
            self.reload_phase = 1 - (self.reload_timer / self.reload_duration)

            # Reload complete
            if self.reload_timer <= 0:
                self.reloading = False
                self.reload_phase = 0
                self.weapon["reloads"] -= 1
                self.ammo = self.max_ammo
                return True  # Reload finished
        return False

    def get_reload_animation_offset(self):
        """Get the gun offset/rotation for reload animation"""
        if not self.reloading:
            return 0, 0, 0  # No offset

        phase = self.reload_phase
        weapon_name = self.weapon["name"]

        # Different animations for different weapons
        if weapon_name == "Rifle":
            # Rifle: tilt down, eject mag, insert new mag, tilt back up
            if phase < 0.3:
                # Tilt gun down
                tilt = (phase / 0.3) * 0.8
                offset_y = (phase / 0.3) * 10
                return 0, offset_y, tilt
            elif phase < 0.5:
                # Magazine out (gun stays tilted)
                return 0, 10, 0.8
            elif phase < 0.8:
                # Magazine in
                return 0, 10, 0.8
            else:
                # Tilt back up
                progress = (phase - 0.8) / 0.2
                tilt = 0.8 * (1 - progress)
                offset_y = 10 * (1 - progress)
                return 0, offset_y, tilt

        elif weapon_name == "Handgun":
            # Pistol: slide back animation
            if phase < 0.3:
                # Pull slide back
                offset_x = -(phase / 0.3) * 8
                return offset_x, 0, 0
            elif phase < 0.5:
                # Eject mag
                return -8, 5, 0.3
            elif phase < 0.7:
                # Insert mag
                return -8, 5, 0.3
            else:
                # Release slide
                progress = (phase - 0.7) / 0.3
                offset_x = -8 * (1 - progress)
                offset_y = 5 * (1 - progress)
                tilt = 0.3 * (1 - progress)
                return offset_x, offset_y, tilt

        elif weapon_name == "Shotgun":
            # Shotgun: pump action
            if phase < 0.4:
                # Pull pump back
                offset_x = -(phase / 0.4) * 12
                return offset_x, 0, 0
            elif phase < 0.6:
                # Hold
                return -12, 0, 0
            else:
                # Push pump forward
                progress = (phase - 0.6) / 0.4
                offset_x = -12 * (1 - progress)
                return offset_x, 0, 0

        elif weapon_name == "Sniper":
            # Sniper: bolt action
            if phase < 0.25:
                # Lift bolt
                tilt = (phase / 0.25) * 0.5
                return 0, 0, tilt
            elif phase < 0.5:
                # Pull bolt back
                progress = (phase - 0.25) / 0.25
                offset_x = -progress * 10
                return offset_x, 0, 0.5
            elif phase < 0.75:
                # Push bolt forward
                progress = (phase - 0.5) / 0.25
                offset_x = -10 * (1 - progress)
                return offset_x, 0, 0.5
            else:
                # Lower bolt
                progress = (phase - 0.75) / 0.25
                tilt = 0.5 * (1 - progress)
                return 0, 0, tilt

        elif weapon_name == "RPG":
            # RPG: open tube, insert rocket
            if phase < 0.3:
                # Lower launcher
                offset_y = (phase / 0.3) * 15
                tilt = (phase / 0.3) * 0.6
                return 0, offset_y, tilt
            elif phase < 0.7:
                # Insert rocket
                return 0, 15, 0.6
            else:
                # Raise launcher
                progress = (phase - 0.7) / 0.3
                offset_y = 15 * (1 - progress)
                tilt = 0.6 * (1 - progress)
                return 0, offset_y, tilt

        return 0, 0, 0

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Draw avatar body with articulated parts
        weapon_name = self.weapon["name"]
        self.avatar.draw(screen, sx, sy, self.angle,
                        is_firing=self.is_firing,
                        is_reloading=self.reloading,
                        reload_phase=self.reload_phase,
                        weapon_name=weapon_name,
                        walk_speed=self.walk_speed,
                        anim_timer=self.anim_timer)

        # Flash white overlay when hit
        if self.hit_flash > 0:
            flash_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 255, 100), (self.radius + 5, self.radius + 5), self.radius)
            screen.blit(flash_surf, (int(sx - self.radius - 5), int(sy - self.radius - 5)))

        # Calculate recoil offset (gun pulls back when shooting)
        recoil_offset = self.recoil

        # Get reload animation offsets
        reload_offset_x, reload_offset_y, reload_tilt = self.get_reload_animation_offset()

        if weapon_name == "Rifle":
            self.draw_rifle(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Handgun":
            self.draw_handgun(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Knife":
            self.draw_knife(screen, sx, sy)
        elif weapon_name == "Grenade":
            self.draw_grenade_weapon(screen, sx, sy)
        elif weapon_name == "Smoke":
            self.draw_smoke_grenade_weapon(screen, sx, sy)
        elif weapon_name == "Shotgun":
            self.draw_shotgun(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "RPG":
            self.draw_rpg(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Sniper":
            self.draw_sniper(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Minigun":
            self.draw_minigun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Flamethrower":
            self.draw_flamethrower(screen, sx, sy, recoil_offset)
        elif weapon_name == "Laser Gun":
            self.draw_laser_gun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Dual Pistols":
            self.draw_dual_pistols(screen, sx, sy, recoil_offset)
        elif weapon_name == "Crossbow":
            self.draw_crossbow(screen, sx, sy, recoil_offset)
        elif weapon_name == "Electric Gun":
            self.draw_electric_gun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Freeze Ray":
            self.draw_freeze_ray(screen, sx, sy, recoil_offset)
        elif weapon_name == "Throwing Knives":
            self.draw_throwing_knives(screen, sx, sy)
        else:
            # Fallback to simple gun
            gun_length = self.radius + self.weapon["gun_length"] - recoil_offset
            gun_x = sx + math.cos(self.angle) * gun_length
            gun_y = sy + math.sin(self.angle) * gun_length
            pygame.draw.line(screen, DARK_GRAY, (sx, sy), (gun_x, gun_y), 6)

        # Draw avatar hands holding the weapon
        self.avatar.draw_holding_hands(screen, sx, sy, self.angle, weapon_name,
                                       is_reloading=self.reloading,
                                       reload_phase=self.reload_phase,
                                       is_firing=self.is_firing,
                                       recoil=recoil_offset)

        # Draw reload indicator if reloading
        if self.reloading:
            # Draw reload progress bar above player
            bar_width = 40
            bar_height = 6
            bar_x = sx - bar_width // 2
            bar_y = sy - self.radius - 25  # Moved higher to account for avatar head
            # Background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Progress
            progress_width = int(bar_width * self.reload_phase)
            pygame.draw.rect(screen, (100, 200, 255), (bar_x, bar_y, progress_width, bar_height))
            # Border
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

    def draw_rifle(self, screen, sx, sy, recoil, reload_x=0, reload_y=0, reload_tilt=0):
        """Draw realistic assault rifle"""
        angle = self.angle + reload_tilt
        # Start gun from edge of player body, with reload offset
        gun_start_x = sx + math.cos(self.angle) * self.radius + reload_x
        gun_start_y = sy + math.sin(self.angle) * self.radius + reload_y

        # Barrel extends from body edge
        barrel_length = 25 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length

        # Main barrel (dark gray)
        pygame.draw.line(screen, (40, 40, 40),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 6)

        # Barrel highlight
        pygame.draw.line(screen, (80, 80, 80),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 3)

        # Body/receiver (slightly offset down, starts at body edge)
        body_offset_angle = angle + 0.2
        body_start_x = sx + math.cos(self.angle + 0.2) * self.radius + reload_x
        body_start_y = sy + math.sin(self.angle + 0.2) * self.radius + reload_y
        body_length = 15 - recoil
        body_end_x = body_start_x + math.cos(body_offset_angle) * body_length
        body_end_y = body_start_y + math.sin(body_offset_angle) * body_length
        pygame.draw.line(screen, (50, 50, 55),
                        (body_start_x, body_start_y),
                        (body_end_x, body_end_y), 10)

        # Magazine (animate during reload)
        mag_offset = 0
        if self.reloading and 0.3 <= self.reload_phase <= 0.5:
            mag_offset = 15  # Magazine drops out
        elif self.reloading and 0.5 < self.reload_phase <= 0.8:
            mag_offset = 15 * (1 - (self.reload_phase - 0.5) / 0.3)  # Magazine comes back

        mag_angle = angle + math.pi/2 + 0.3
        mag_x = gun_start_x + math.cos(angle) * (8 - recoil)
        mag_y = gun_start_y + math.sin(angle) * (8 - recoil)
        mag_end_x = mag_x + math.cos(mag_angle) * (8 + mag_offset)
        mag_end_y = mag_y + math.sin(mag_angle) * (8 + mag_offset)
        pygame.draw.line(screen, (60, 55, 50), (mag_x, mag_y), (mag_end_x, mag_end_y), 5)

        # Front sight
        sight_x = barrel_end_x - math.cos(angle) * 3
        sight_y = barrel_end_y - math.sin(angle) * 3
        pygame.draw.circle(screen, (30, 30, 30), (int(sight_x), int(sight_y)), 2)

        # Muzzle flash when firing
        if self.is_firing:
            flash_x = barrel_end_x + math.cos(angle) * 5
            flash_y = barrel_end_y + math.sin(angle) * 5
            flash_size = 6 + math.sin(self.anim_timer * 0.8) * 2
            pygame.draw.circle(screen, (255, 200, 100), (int(flash_x), int(flash_y)), int(flash_size))
            pygame.draw.circle(screen, (255, 255, 200), (int(flash_x), int(flash_y)), int(flash_size * 0.5))
            # Shell ejection
            if self.fire_cooldown > 3:
                eject_angle = angle + math.pi/2 + 0.3
                eject_dist = 8 + (6 - self.fire_cooldown) * 2
                shell_x = gun_start_x + math.cos(angle) * 10 + math.cos(eject_angle) * eject_dist
                shell_y = gun_start_y + math.sin(angle) * 10 + math.sin(eject_angle) * eject_dist
                pygame.draw.ellipse(screen, (200, 180, 100), (int(shell_x)-2, int(shell_y)-1, 4, 2))

    def draw_handgun(self, screen, sx, sy, recoil, reload_x=0, reload_y=0, reload_tilt=0):
        """Draw realistic pistol"""
        angle = self.angle + reload_tilt
        # Start gun from edge of player body
        gun_start_x = sx + math.cos(self.angle) * self.radius + reload_x
        gun_start_y = sy + math.sin(self.angle) * self.radius + reload_y

        # Slide (top part) - animate slide during reload
        slide_offset = 0
        if self.reloading and self.reload_phase < 0.3:
            slide_offset = (self.reload_phase / 0.3) * 6

        slide_length = 14 - recoil - slide_offset
        slide_end_x = gun_start_x + math.cos(angle) * slide_length
        slide_end_y = gun_start_y + math.sin(angle) * slide_length
        pygame.draw.line(screen, (45, 45, 50),
                        (gun_start_x, gun_start_y),
                        (slide_end_x, slide_end_y), 5)

        # Barrel (inside slide)
        pygame.draw.line(screen, (30, 30, 30),
                        (gun_start_x + math.cos(angle) * 2, gun_start_y + math.sin(angle) * 2),
                        (slide_end_x, slide_end_y), 2)

        # Grip
        grip_angle = angle + math.pi/2 + 0.4
        grip_x = gun_start_x
        grip_y = gun_start_y
        grip_end_x = grip_x + math.cos(grip_angle) * 10
        grip_end_y = grip_y + math.sin(grip_angle) * 10
        pygame.draw.line(screen, (60, 50, 40), (grip_x, grip_y), (grip_end_x, grip_end_y), 6)

        # Magazine (animate during reload)
        if self.reloading and 0.3 <= self.reload_phase <= 0.7:
            # Draw magazine falling/inserting
            mag_progress = (self.reload_phase - 0.3) / 0.4
            mag_drop = 20 * (1 - abs(mag_progress - 0.5) * 2)
            mag_x = grip_x + math.cos(grip_angle) * (5 + mag_drop)
            mag_y = grip_y + math.sin(grip_angle) * (5 + mag_drop)
            pygame.draw.rect(screen, (70, 60, 50), (mag_x - 3, mag_y - 3, 6, 10))

        # Trigger guard
        pygame.draw.circle(screen, (50, 50, 50), (int(grip_x), int(grip_y)), 3, 1)

        # Muzzle flash and slide animation when firing
        if self.is_firing:
            flash_x = slide_end_x + math.cos(angle) * 4
            flash_y = slide_end_y + math.sin(angle) * 4
            flash_size = 5 + math.sin(self.anim_timer * 0.9) * 1.5
            pygame.draw.circle(screen, (255, 220, 100), (int(flash_x), int(flash_y)), int(flash_size))
            # Shell eject
            if self.fire_cooldown > 4:
                eject_angle = angle - math.pi/2 - 0.2
                eject_dist = 6 + (8 - self.fire_cooldown) * 1.5
                shell_x = gun_start_x + math.cos(angle) * 6 + math.cos(eject_angle) * eject_dist
                shell_y = gun_start_y + math.sin(angle) * 6 + math.sin(eject_angle) * eject_dist
                pygame.draw.ellipse(screen, (200, 180, 100), (int(shell_x)-2, int(shell_y)-1, 4, 2))

    def draw_knife(self, screen, sx, sy):
        """Draw combat knife with gleam animation"""
        angle = self.angle
        # Start knife from edge of player body
        knife_start_x = sx + math.cos(angle) * self.radius
        knife_start_y = sy + math.sin(angle) * self.radius

        blade_length = 20

        # Blade
        blade_end_x = knife_start_x + math.cos(angle) * blade_length
        blade_end_y = knife_start_y + math.sin(angle) * blade_length

        # Blade shape (tapered) with animated sheen
        sheen = int(15 * math.sin(self.anim_timer * 0.15))
        pygame.draw.line(screen, (180 + sheen, 180 + sheen, 190 + sheen),
                        (knife_start_x, knife_start_y),
                        (blade_end_x, blade_end_y), 4)

        # Blade edge highlight with moving gleam
        gleam_pos = (self.anim_timer * 0.08) % 1.0  # 0 to 1 along blade
        gleam_x = knife_start_x + math.cos(angle) * (2 + gleam_pos * (blade_length - 4))
        gleam_y = knife_start_y + math.sin(angle) * (2 + gleam_pos * (blade_length - 4))
        pygame.draw.line(screen, (220, 220, 230),
                        (knife_start_x + math.cos(angle) * 2, knife_start_y + math.sin(angle) * 2),
                        (blade_end_x, blade_end_y), 2)
        # Gleam sparkle
        pygame.draw.circle(screen, (255, 255, 255), (int(gleam_x), int(gleam_y)), 2)

        # Guard at the start
        guard_angle = angle + math.pi/2
        guard_x1 = knife_start_x + math.cos(guard_angle) * 5
        guard_y1 = knife_start_y + math.sin(guard_angle) * 5
        guard_x2 = knife_start_x + math.cos(guard_angle + math.pi) * 5
        guard_y2 = knife_start_y + math.sin(guard_angle + math.pi) * 5
        pygame.draw.line(screen, (60, 60, 60), (guard_x1, guard_y1), (guard_x2, guard_y2), 3)

        # Slash effect when attacking
        if self.is_firing:
            slash_angle = angle + math.sin(self.anim_timer * 1.2) * 0.5
            slash_x = blade_end_x + math.cos(slash_angle) * 8
            slash_y = blade_end_y + math.sin(slash_angle) * 8
            pygame.draw.line(screen, (255, 255, 255), (int(blade_end_x), int(blade_end_y)), (int(slash_x), int(slash_y)), 2)

    def draw_grenade_weapon(self, screen, sx, sy):
        """Draw grenade in hand with ready-to-throw animation"""
        angle = self.angle
        # Hand position - outside player body with slight bob
        bob = math.sin(self.anim_timer * 0.12) * 2
        hand_x = sx + math.cos(angle) * (self.radius + 8 + bob)
        hand_y = sy + math.sin(angle) * (self.radius + 8 + bob)

        # Grenade body with pulsing danger glow
        glow = int(20 * abs(math.sin(self.anim_timer * 0.2)))
        pygame.draw.circle(screen, (60 + glow//3, 80, 60), (int(hand_x), int(hand_y)), 7)
        pygame.draw.circle(screen, (80 + glow//2, 100, 80), (int(hand_x), int(hand_y)), 7, 2)

        # Spoon/lever - slight wobble
        spoon_wobble = math.sin(self.anim_timer * 0.15) * 0.1
        spoon_end_x = hand_x + math.cos(angle - 0.5 + spoon_wobble) * 10
        spoon_end_y = hand_y + math.sin(angle - 0.5 + spoon_wobble) * 10
        pygame.draw.line(screen, (100, 100, 100), (hand_x, hand_y), (spoon_end_x, spoon_end_y), 2)

        # Pin ring with shine
        ring_shine = int(30 * abs(math.sin(self.anim_timer * 0.25)))
        pygame.draw.circle(screen, (150 + ring_shine, 140 + ring_shine, 50), (int(hand_x + 3), int(hand_y - 3)), 3, 1)

        # Fuse spark effect when throwing
        if self.is_firing:
            spark_x = hand_x - math.cos(angle) * 5 + math.sin(self.anim_timer * 1.5) * 3
            spark_y = hand_y - math.sin(angle) * 5 + math.cos(self.anim_timer * 1.5) * 3
            spark_color = (255, 200 + int(55 * math.sin(self.anim_timer)), 50)
            pygame.draw.circle(screen, spark_color, (int(spark_x), int(spark_y)), 3)
            pygame.draw.circle(screen, (255, 255, 200), (int(spark_x), int(spark_y)), 1)

    def draw_smoke_grenade_weapon(self, screen, sx, sy):
        """Draw smoke grenade in hand with ready-to-throw animation"""
        angle = self.angle
        # Hand position - outside player body with slight bob
        bob = math.sin(self.anim_timer * 0.12) * 2
        hand_x = sx + math.cos(angle) * (self.radius + 8 + bob)
        hand_y = sy + math.sin(angle) * (self.radius + 8 + bob)

        # Smoke grenade body - gray/silver color
        glow = int(15 * abs(math.sin(self.anim_timer * 0.15)))
        pygame.draw.circle(screen, (90 + glow, 90 + glow, 95 + glow), (int(hand_x), int(hand_y)), 7)
        pygame.draw.circle(screen, (120 + glow, 120 + glow, 130 + glow), (int(hand_x), int(hand_y)), 7, 2)

        # Spoon/lever - slight wobble
        spoon_wobble = math.sin(self.anim_timer * 0.15) * 0.1
        spoon_end_x = hand_x + math.cos(angle - 0.5 + spoon_wobble) * 10
        spoon_end_y = hand_y + math.sin(angle - 0.5 + spoon_wobble) * 10
        pygame.draw.line(screen, (80, 80, 85), (hand_x, hand_y), (spoon_end_x, spoon_end_y), 2)

        # Pin ring
        ring_shine = int(20 * abs(math.sin(self.anim_timer * 0.25)))
        pygame.draw.circle(screen, (140 + ring_shine, 140 + ring_shine, 145 + ring_shine), (int(hand_x + 3), int(hand_y - 3)), 3, 1)

        # Smoke wisps when throwing
        if self.is_firing:
            for i in range(3):
                wisp_offset = self.anim_timer * 0.5 + i * 1.0
                wisp_x = hand_x + math.sin(wisp_offset) * 5
                wisp_y = hand_y - abs(math.sin(wisp_offset * 0.7)) * 8 - i * 3
                wisp_alpha = 150 - i * 40
                pygame.draw.circle(screen, (wisp_alpha, wisp_alpha, wisp_alpha + 10), (int(wisp_x), int(wisp_y)), 2 - i//2)

    def draw_shotgun(self, screen, sx, sy, recoil, reload_x=0, reload_y=0, reload_tilt=0):
        """Draw pump-action shotgun"""
        angle = self.angle + reload_tilt
        # Start gun from edge of player body
        gun_start_x = sx + math.cos(self.angle) * self.radius + reload_x
        gun_start_y = sy + math.sin(self.angle) * self.radius + reload_y

        # Long barrel
        barrel_length = 28 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length

        # Main barrel
        pygame.draw.line(screen, (40, 40, 45),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 7)

        # Barrel inner
        pygame.draw.line(screen, (25, 25, 25),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 3)

        # Pump/forend - animate during reload
        pump_offset = 0
        if self.reloading:
            if self.reload_phase < 0.4:
                pump_offset = (self.reload_phase / 0.4) * 10  # Pull back
            elif self.reload_phase < 0.6:
                pump_offset = 10  # Hold back
            else:
                pump_offset = 10 * (1 - (self.reload_phase - 0.6) / 0.4)  # Push forward

        pump_pos = 10 - recoil - pump_offset
        pump_x = gun_start_x + math.cos(angle) * pump_pos
        pump_y = gun_start_y + math.sin(angle) * pump_pos
        pygame.draw.circle(screen, (90, 70, 50), (int(pump_x), int(pump_y)), 5)

        # Shell ejecting during reload
        if self.reloading and 0.35 <= self.reload_phase <= 0.45:
            shell_progress = (self.reload_phase - 0.35) / 0.1
            shell_x = pump_x + math.cos(angle + math.pi/2) * (5 + shell_progress * 15)
            shell_y = pump_y + math.sin(angle + math.pi/2) * (5 + shell_progress * 15)
            pygame.draw.ellipse(screen, (200, 50, 50), (shell_x - 3, shell_y - 2, 8, 4))

        # Massive muzzle flash for shotgun (spread pattern)
        if self.is_firing:
            flash_x = barrel_end_x + math.cos(angle) * 6
            flash_y = barrel_end_y + math.sin(angle) * 6
            # Multiple flash points for spread effect
            for spread in [-0.25, -0.12, 0, 0.12, 0.25]:
                spread_x = barrel_end_x + math.cos(angle + spread) * (8 + math.sin(self.anim_timer) * 2)
                spread_y = barrel_end_y + math.sin(angle + spread) * (8 + math.sin(self.anim_timer) * 2)
                pygame.draw.circle(screen, (255, 180, 80), (int(spread_x), int(spread_y)), 4)
            pygame.draw.circle(screen, (255, 220, 150), (int(flash_x), int(flash_y)), 8)
            # Smoke puff
            smoke_x = barrel_end_x + math.cos(angle) * 12
            smoke_y = barrel_end_y + math.sin(angle) * 12
            pygame.draw.circle(screen, (150, 150, 150), (int(smoke_x), int(smoke_y)), 6)

    def draw_rpg(self, screen, sx, sy, recoil, reload_x=0, reload_y=0, reload_tilt=0):
        """Draw RPG launcher"""
        angle = self.angle + reload_tilt
        # Start gun from edge of player body
        gun_start_x = sx + math.cos(self.angle) * self.radius + reload_x
        gun_start_y = sy + math.sin(self.angle) * self.radius + reload_y

        # Launcher tube
        tube_length = 30 - recoil
        tube_end_x = gun_start_x + math.cos(angle) * tube_length
        tube_end_y = gun_start_y + math.sin(angle) * tube_length

        # Main tube (olive drab)
        pygame.draw.line(screen, (70, 80, 50),
                        (gun_start_x, gun_start_y),
                        (tube_end_x, tube_end_y), 12)

        # Tube opening
        pygame.draw.circle(screen, (40, 40, 40), (int(tube_end_x), int(tube_end_y)), 5)

        # Rocket tip visible (animate during reload)
        if not self.reloading or self.reload_phase > 0.7:
            pygame.draw.circle(screen, (60, 60, 60), (int(tube_end_x), int(tube_end_y)), 3)
        elif self.reloading and 0.3 <= self.reload_phase <= 0.7:
            # Show rocket being inserted
            rocket_progress = (self.reload_phase - 0.3) / 0.4
            rocket_x = tube_end_x + math.cos(angle) * (15 * (1 - rocket_progress))
            rocket_y = tube_end_y + math.sin(angle) * (15 * (1 - rocket_progress))
            pygame.draw.circle(screen, (80, 80, 60), (int(rocket_x), int(rocket_y)), 4)

        # Grip/trigger
        grip_angle = angle + math.pi/2 + 0.3
        grip_x = gun_start_x + math.cos(angle) * 5
        grip_y = gun_start_y + math.sin(angle) * 5
        grip_end_x = grip_x + math.cos(grip_angle) * 12
        grip_end_y = grip_y + math.sin(grip_angle) * 12
        pygame.draw.line(screen, (50, 50, 45), (grip_x, grip_y), (grip_end_x, grip_end_y), 5)

        # Rear sight
        sight_x = gun_start_x + math.cos(angle) * 8
        sight_y = gun_start_y + math.sin(angle) * 8
        sight_up_x = sight_x + math.cos(angle - math.pi/2) * 6
        sight_up_y = sight_y + math.sin(angle - math.pi/2) * 6
        pygame.draw.line(screen, (60, 60, 55), (sight_x, sight_y), (sight_up_x, sight_up_y), 2)

        # Rocket ignition and backblast when firing
        if self.is_firing:
            # Front rocket flame
            flame_x = tube_end_x + math.cos(angle) * 8
            flame_y = tube_end_y + math.sin(angle) * 8
            flame_size = 10 + math.sin(self.anim_timer * 1.2) * 3
            pygame.draw.circle(screen, (255, 150, 50), (int(flame_x), int(flame_y)), int(flame_size))
            pygame.draw.circle(screen, (255, 220, 100), (int(flame_x), int(flame_y)), int(flame_size * 0.5))
            # Backblast smoke behind launcher
            for i in range(4):
                back_dist = 10 + i * 8 + math.sin(self.anim_timer * 0.5 + i) * 3
                back_x = gun_start_x + math.cos(angle + math.pi) * back_dist
                back_y = gun_start_y + math.sin(angle + math.pi) * back_dist
                smoke_size = 8 - i + math.sin(self.anim_timer * 0.4) * 2
                smoke_alpha = 200 - i * 40
                pygame.draw.circle(screen, (smoke_alpha, smoke_alpha, smoke_alpha), (int(back_x), int(back_y)), int(max(2, smoke_size)))
            # Smoke trail particles
            trail_x = flame_x + math.cos(angle) * 5
            trail_y = flame_y + math.sin(angle) * 5
            pygame.draw.circle(screen, (180, 180, 180), (int(trail_x), int(trail_y)), 5)

    def draw_sniper(self, screen, sx, sy, recoil, reload_x=0, reload_y=0, reload_tilt=0):
        """Draw sniper rifle with scope"""
        angle = self.angle + reload_tilt
        # Start gun from edge of player body
        gun_start_x = sx + math.cos(self.angle) * self.radius + reload_x
        gun_start_y = sy + math.sin(self.angle) * self.radius + reload_y

        # Long barrel
        barrel_length = 35 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length

        # Main barrel (dark)
        pygame.draw.line(screen, (35, 35, 40),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 5)

        # Barrel highlight
        pygame.draw.line(screen, (55, 55, 60),
                        (gun_start_x, gun_start_y),
                        (barrel_end_x, barrel_end_y), 2)

        # Scope (the defining feature)
        scope_x = gun_start_x + math.cos(angle) * (12 - recoil)
        scope_y = gun_start_y + math.sin(angle) * (12 - recoil)
        # Scope body
        scope_up_angle = angle - math.pi/2
        scope_top_x = scope_x + math.cos(scope_up_angle) * 8
        scope_top_y = scope_y + math.sin(scope_up_angle) * 8
        pygame.draw.line(screen, (20, 20, 25), (scope_x, scope_y), (scope_top_x, scope_top_y), 6)
        # Scope lens with animated glint
        lens_glint = int(50 * abs(math.sin(self.anim_timer * 0.1)))
        pygame.draw.circle(screen, (100 + lens_glint, 150 + lens_glint//2, 200 + lens_glint//3), (int(scope_top_x), int(scope_top_y)), 4)
        pygame.draw.circle(screen, (50, 80, 120), (int(scope_top_x), int(scope_top_y)), 4, 1)
        # Scope glint sparkle (appears periodically)
        if (self.anim_timer % 90) < 15:
            glint_intensity = 1 - abs((self.anim_timer % 90) - 7.5) / 7.5
            glint_size = int(3 * glint_intensity)
            pygame.draw.circle(screen, (255, 255, 255), (int(scope_top_x), int(scope_top_y)), glint_size)

        # Bipod hints
        bipod_x = gun_start_x + math.cos(angle) * (barrel_length - 8)
        bipod_y = gun_start_y + math.sin(angle) * (barrel_length - 8)
        bipod_angle = angle + math.pi/2 + 0.5
        bipod_end_x = bipod_x + math.cos(bipod_angle) * 6
        bipod_end_y = bipod_y + math.sin(bipod_angle) * 6
        pygame.draw.line(screen, (60, 60, 60), (bipod_x, bipod_y), (bipod_end_x, bipod_end_y), 2)

        # Powerful muzzle flash when firing
        if self.is_firing:
            flash_x = barrel_end_x + math.cos(angle) * 8
            flash_y = barrel_end_y + math.sin(angle) * 8
            # Large bright flash
            pygame.draw.circle(screen, (255, 240, 200), (int(flash_x), int(flash_y)), 10)
            pygame.draw.circle(screen, (255, 255, 230), (int(flash_x), int(flash_y)), 5)
            # Shell eject
            if self.fire_cooldown > 3:
                eject_angle = angle + math.pi/2 + 0.4
                eject_dist = 10 + (5 - min(5, self.fire_cooldown)) * 3
                shell_x = gun_start_x + math.cos(angle) * 15 + math.cos(eject_angle) * eject_dist
                shell_y = gun_start_y + math.sin(angle) * 15 + math.sin(eject_angle) * eject_dist
                pygame.draw.ellipse(screen, (180, 160, 80), (int(shell_x)-3, int(shell_y)-2, 6, 4))

    def draw_minigun(self, screen, sx, sy, recoil):
        """Draw multi-barrel minigun with spinning barrels animation"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        barrel_length = 32 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length
        # Main body
        pygame.draw.line(screen, (60, 60, 65), (gun_start_x, gun_start_y), (barrel_end_x, barrel_end_y), 12)
        # Spinning barrels - simplified to 3 visible barrels
        barrel_center_x = gun_start_x + math.cos(angle) * 18
        barrel_center_y = gun_start_y + math.sin(angle) * 18
        rot = self.minigun_rotation
        # Draw only 3 barrels for better performance
        for i in range(3):
            barrel_angle = rot + (i * math.pi * 2 / 3)
            perp_offset = 5 * math.sin(barrel_angle)
            bx = barrel_center_x + math.cos(angle + math.pi/2) * perp_offset
            by = barrel_center_y + math.sin(angle + math.pi/2) * perp_offset
            bex = bx + math.cos(angle) * 14
            bey = by + math.sin(angle) * 14
            pygame.draw.line(screen, (50, 50, 55), (bx, by), (bex, bey), 3)
        # Ammo drum - animate during reload
        drum_drop = 0
        if self.reloading:
            phase = self.reload_phase
            if phase < 0.3:
                drum_drop = phase / 0.3 * 20
            elif phase < 0.7:
                drum_drop = 20
            else:
                drum_drop = 20 * (1 - (phase - 0.7) / 0.3)
        drum_x = gun_start_x + math.cos(angle + math.pi/2) * (10 + drum_drop)
        drum_y = gun_start_y + math.sin(angle + math.pi/2) * (10 + drum_drop)
        pygame.draw.circle(screen, (80, 70, 60), (int(drum_x), int(drum_y)), 8)
        # Ammo belt
        if not self.reloading or self.reload_phase > 0.7:
            belt_x = gun_start_x + math.cos(angle + math.pi/2) * 5
            belt_y = gun_start_y + math.sin(angle + math.pi/2) * 5
            pygame.draw.line(screen, (70, 60, 50), (int(drum_x), int(drum_y)), (int(belt_x), int(belt_y)), 3)
        # Muzzle flash when firing
        if self.is_firing:
            flash_x = gun_start_x + math.cos(angle) * (barrel_length + 5)
            flash_y = gun_start_y + math.sin(angle) * (barrel_length + 5)
            pygame.draw.circle(screen, (255, 200, 100), (int(flash_x), int(flash_y)), 6)

    def draw_flamethrower(self, screen, sx, sy, recoil):
        """Draw flamethrower with flickering flame animation"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        tube_length = 28 - recoil
        tube_end_x = gun_start_x + math.cos(angle) * tube_length
        tube_end_y = gun_start_y + math.sin(angle) * tube_length
        # Main tube
        pygame.draw.line(screen, (70, 70, 75), (gun_start_x, gun_start_y), (tube_end_x, tube_end_y), 10)
        # Fuel tank on back
        tank_x = gun_start_x + math.cos(angle + math.pi) * 8
        tank_y = gun_start_y + math.sin(angle + math.pi) * 8
        tank_color = (200, 80, 30) if not self.reloading else (100, 50, 20)
        pygame.draw.circle(screen, tank_color, (int(tank_x), int(tank_y)), 8)
        # Pilot flame
        pygame.draw.circle(screen, (255, 150, 30), (int(tube_end_x), int(tube_end_y)), 5)
        # When firing, add flame
        if self.is_firing:
            flame_x = tube_end_x + math.cos(angle) * 12
            flame_y = tube_end_y + math.sin(angle) * 12
            pygame.draw.circle(screen, (255, 100, 30), (int(flame_x), int(flame_y)), 8)

    def draw_laser_gun(self, screen, sx, sy, recoil):
        """Draw laser gun (green) with pulsing energy coils"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        barrel_length = 24 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length
        # Body
        pygame.draw.line(screen, (40, 80, 40), (gun_start_x, gun_start_y), (barrel_end_x, barrel_end_y), 8)
        # Energy cell on back - animate during reload
        cell_brightness = 255
        if self.reloading:
            phase = self.reload_phase
            if phase < 0.5:
                cell_brightness = int(255 * (1 - phase * 1.6))
            else:
                cell_brightness = int(255 * (phase - 0.5) * 2)
        cell_x = gun_start_x + math.cos(angle + math.pi) * 5
        cell_y = gun_start_y + math.sin(angle + math.pi) * 5
        pygame.draw.rect(screen, (30, max(50, cell_brightness), 50), (int(cell_x) - 4, int(cell_y) - 3, 8, 6))
        # Single coil
        coil_x = gun_start_x + math.cos(angle) * 12
        coil_y = gun_start_y + math.sin(angle) * 12
        pygame.draw.circle(screen, (50, max(100, cell_brightness), 100), (int(coil_x), int(coil_y)), 3)
        # Emitter
        pygame.draw.circle(screen, (100, 255, 100), (int(barrel_end_x), int(barrel_end_y)), 5)
        # Firing beam glow
        if self.is_firing:
            pygame.draw.circle(screen, (150, 255, 150), (int(barrel_end_x), int(barrel_end_y)), 8)

    def draw_dual_pistols(self, screen, sx, sy, recoil):
        """Draw golden dual pistols with alternating fire animation"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        # Two pistols
        offsets = [-0.25, 0.25]
        for i, offset in enumerate(offsets):
            px = gun_start_x
            py = gun_start_y
            # Tilt during reload
            tilt = 0.3 if self.reloading else 0
            pex = px + math.cos(angle + offset + tilt) * (18 - recoil)
            pey = py + math.sin(angle + offset + tilt) * (18 - recoil)
            pygame.draw.line(screen, (220, 180, 50), (px, py), (pex, pey), 6)
            pygame.draw.circle(screen, (200, 160, 40), (int(pex), int(pey)), 3)
            # Muzzle flash
            if self.is_firing:
                flash_x = pex + math.cos(angle + offset) * 5
                flash_y = pey + math.sin(angle + offset) * 5
                pygame.draw.circle(screen, (255, 220, 100), (int(flash_x), int(flash_y)), 4)

    def draw_crossbow(self, screen, sx, sy, recoil):
        """Draw crossbow with string vibration animation"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        rail_length = 25 - recoil
        rail_end_x = gun_start_x + math.cos(angle) * rail_length
        rail_end_y = gun_start_y + math.sin(angle) * rail_length
        # Main rail (brown wood)
        pygame.draw.line(screen, (120, 80, 40), (gun_start_x, gun_start_y), (rail_end_x, rail_end_y), 6)
        # Limbs
        limb_x = gun_start_x + math.cos(angle) * 8
        limb_y = gun_start_y + math.sin(angle) * 8
        limb_flex = 0.15 if self.reloading else 0
        limb_l_x = limb_x + math.cos(angle - math.pi/2 - 0.4 + limb_flex) * 15
        limb_l_y = limb_y + math.sin(angle - math.pi/2 - 0.4 + limb_flex) * 15
        limb_r_x = limb_x + math.cos(angle + math.pi/2 + 0.4 - limb_flex) * 15
        limb_r_y = limb_y + math.sin(angle + math.pi/2 + 0.4 - limb_flex) * 15
        pygame.draw.line(screen, (100, 70, 35), (limb_x, limb_y), (limb_l_x, limb_l_y), 5)
        pygame.draw.line(screen, (100, 70, 35), (limb_x, limb_y), (limb_r_x, limb_r_y), 5)
        # String
        string_draw = 6 if self.reloading else 0
        string_mid_x = (limb_l_x + limb_r_x) / 2 - math.cos(angle) * string_draw
        string_mid_y = (limb_l_y + limb_r_y) / 2 - math.sin(angle) * string_draw
        pygame.draw.line(screen, (180, 170, 150), (limb_l_x, limb_l_y), (int(string_mid_x), int(string_mid_y)), 2)
        pygame.draw.line(screen, (180, 170, 150), (int(string_mid_x), int(string_mid_y)), (limb_r_x, limb_r_y), 2)
        # Bolt - only when not reloading or reload is finishing
        if not self.reloading or self.reload_phase > 0.7:
            pygame.draw.line(screen, (150, 140, 100), (limb_x, limb_y), (rail_end_x + math.cos(angle)*5, rail_end_y + math.sin(angle)*5), 3)
            pygame.draw.circle(screen, (180, 180, 180), (int(rail_end_x + math.cos(angle)*7), int(rail_end_y + math.sin(angle)*7)), 2)

    def draw_electric_gun(self, screen, sx, sy, recoil):
        """Draw electric/tesla gun (blue) with arcing electricity"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        barrel_length = 24 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length
        # Body
        pygame.draw.line(screen, (50, 50, 80), (gun_start_x, gun_start_y), (barrel_end_x, barrel_end_y), 9)
        # Capacitor on back - animate during reload
        cap_charge = 1.0
        if self.reloading:
            phase = self.reload_phase
            if phase < 0.5:
                cap_charge = 1 - phase * 1.8
            else:
                cap_charge = (phase - 0.5) * 2
        cap_x = gun_start_x + math.cos(angle + math.pi) * 6
        cap_y = gun_start_y + math.sin(angle + math.pi) * 6
        cap_brightness = int(255 * max(0.1, cap_charge))
        pygame.draw.circle(screen, (50, 100, cap_brightness), (int(cap_x), int(cap_y)), 6)
        # Single coil indicator
        coil_x = gun_start_x + math.cos(angle) * 12
        coil_y = gun_start_y + math.sin(angle) * 12
        pygame.draw.circle(screen, (100, 150, int(255 * cap_charge)), (int(coil_x), int(coil_y)), 4)
        # Emitter
        pygame.draw.circle(screen, (150, 200, 255), (int(barrel_end_x), int(barrel_end_y)), 5)
        # Sparks when firing
        if self.is_firing:
            spark_angle = angle + math.sin(self.anim_timer * 0.5) * 0.5
            spark_x = barrel_end_x + math.cos(spark_angle) * 10
            spark_y = barrel_end_y + math.sin(spark_angle) * 10
            pygame.draw.line(screen, (200, 230, 255), (int(barrel_end_x), int(barrel_end_y)), (int(spark_x), int(spark_y)), 2)

    def draw_freeze_ray(self, screen, sx, sy, recoil):
        """Draw freeze ray (ice blue) with floating ice crystals"""
        angle = self.angle
        gun_start_x = sx + math.cos(angle) * self.radius
        gun_start_y = sy + math.sin(angle) * self.radius
        barrel_length = 22 - recoil
        barrel_end_x = gun_start_x + math.cos(angle) * barrel_length
        barrel_end_y = gun_start_y + math.sin(angle) * barrel_length
        # Body (ice blue)
        pygame.draw.line(screen, (100, 180, 220), (gun_start_x, gun_start_y), (barrel_end_x, barrel_end_y), 8)
        pygame.draw.line(screen, (150, 210, 240), (gun_start_x, gun_start_y), (barrel_end_x, barrel_end_y), 4)
        # Coolant tank on back - animate during reload
        tank_level = 1.0
        if self.reloading:
            phase = self.reload_phase
            if phase < 0.5:
                tank_level = 1 - phase * 2
            else:
                tank_level = (phase - 0.5) * 2
        tank_x = gun_start_x + math.cos(angle + math.pi) * 6
        tank_y = gun_start_y + math.sin(angle + math.pi) * 6
        pygame.draw.circle(screen, (80, 130, 160), (int(tank_x), int(tank_y)), 7)
        if tank_level > 0:
            pygame.draw.circle(screen, (180, 230, 250), (int(tank_x), int(tank_y)), int(max(2, 5 * tank_level)))
        # Emitter
        pygame.draw.circle(screen, (180, 230, 255), (int(barrel_end_x), int(barrel_end_y)), 5)
        # Ice mist when firing
        if self.is_firing:
            mist_x = barrel_end_x + math.cos(angle) * 10
            mist_y = barrel_end_y + math.sin(angle) * 10
            pygame.draw.circle(screen, (220, 245, 255), (int(mist_x), int(mist_y)), 4)

    def draw_throwing_knives(self, screen, sx, sy):
        """Draw throwing knives (silver, fanned) with spinning ready-to-throw animation"""
        angle = self.angle
        hand_x = sx + math.cos(angle) * (self.radius + 5)
        hand_y = sy + math.sin(angle) * (self.radius + 5)
        # Knife count based on reload
        knives_visible = 3
        if self.reloading:
            knives_visible = int(self.reload_phase * 3)
        # Draw knives
        offsets = [-0.3, 0, 0.3]
        for i in range(knives_visible):
            offset = offsets[i]
            knife_len = 18
            kex = hand_x + math.cos(angle + offset) * knife_len
            key = hand_y + math.sin(angle + offset) * knife_len
            pygame.draw.line(screen, (180, 180, 190), (hand_x, hand_y), (kex, key), 3)
            pygame.draw.circle(screen, (200, 200, 210), (int(kex), int(key)), 2)
        # When throwing
        if self.is_firing and not self.reloading:
            throw_x = hand_x + math.cos(angle) * 25
            throw_y = hand_y + math.sin(angle) * 25
            pygame.draw.line(screen, (220, 220, 230), (int(hand_x + math.cos(angle) * 20), int(hand_y + math.sin(angle) * 20)), (int(throw_x), int(throw_y)), 3)


class Player2(Player):
    """Second player for PvP and Co-op modes - uses IJKL for movement, aims with numpad"""

    def __init__(self, x, y):
        super().__init__(x, y)
        # Player 2 uses dark blue color
        self.player_color = (30, 60, 150)  # Dark blue
        self.aim_direction = 0  # Aim angle controlled by numpad
        # Player 2 doesn't load saved progress (fresh start for fairness in PvP)
        self.coins = 0
        self.has_rpg = False
        self.has_shotgun = False
        self.has_sniper = False
        self.medkit_charges = 0
        # Remove extra weapons for fairness - base weapons only
        self.weapons = [
            # Rifle
            {"name": "Rifle", "ammo": 30, "max_ammo": 30, "reloads": 5, "fire_rate": 6, "damage": 28,
             "bullet_speed": 22, "color": (255, 220, 100), "gun_length": 24, "gun_width": 5,
             "melee": False, "grenade": False, "recoil": 3, "reload_time": 90},
            # Handgun
            {"name": "Handgun", "ammo": 17, "max_ammo": 17, "reloads": 6, "fire_rate": 8, "damage": 18,
             "bullet_speed": 20, "color": (255, 200, 100), "gun_length": 10, "gun_width": 4,
             "melee": False, "grenade": False, "recoil": 2, "reload_time": 60},
            # Knife (high damage, close range)
            {"name": "Knife", "ammo": 999, "max_ammo": 999, "reloads": 999, "fire_rate": 15,
             "damage": 75, "bullet_speed": 0, "color": WHITE, "gun_length": 12, "gun_width": 3,
             "melee": True, "grenade": False, "recoil": 0},
            # Grenade
            {"name": "Grenade", "ammo": 4, "max_ammo": 4, "reloads": 0, "fire_rate": 50, "damage": 150,
             "bullet_speed": 0, "color": (80, 100, 80), "gun_length": 6, "gun_width": 6,
             "melee": False, "grenade": True, "no_reload": True, "recoil": 0}
        ]

    def update(self, keys, target_pos, camera, obstacles):
        """Player 2 uses IJKL for movement and numpad for aiming"""
        # Movement (IJKL keys)
        dx, dy = 0, 0
        if keys[pygame.K_i]:
            dy -= self.speed
        if keys[pygame.K_k]:
            dy += self.speed
        if keys[pygame.K_j]:
            dx -= self.speed
        if keys[pygame.K_l]:
            dx += self.speed

        # Normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Try to move
        new_x = self.x + dx
        new_y = self.y + dy

        # Check obstacle collision
        can_move_x = True
        can_move_y = True

        for obs in obstacles:
            if obs.collides_circle(new_x, self.y, self.radius):
                can_move_x = False
            if obs.collides_circle(self.x, new_y, self.radius):
                can_move_y = False

        if can_move_x:
            self.x = max(self.radius + 50, min(MAP_WIDTH - self.radius - 50, new_x))
        if can_move_y:
            self.y = max(self.radius + 50, min(MAP_HEIGHT - self.radius - 50, new_y))

        # Aiming with numpad (8 directions) or target position (for Co-op/AI)
        if target_pos:
            # Aim at target position (like co-op mode aiming at enemies)
            self.angle = math.atan2(target_pos[1] - self.y, target_pos[0] - self.x)
        else:
            # Manual aiming with numpad
            if keys[pygame.K_KP8]:  # Up
                self.aim_direction = -math.pi/2
            elif keys[pygame.K_KP2]:  # Down
                self.aim_direction = math.pi/2
            elif keys[pygame.K_KP4]:  # Left
                self.aim_direction = math.pi
            elif keys[pygame.K_KP6]:  # Right
                self.aim_direction = 0
            elif keys[pygame.K_KP7]:  # Up-Left
                self.aim_direction = -3*math.pi/4
            elif keys[pygame.K_KP9]:  # Up-Right
                self.aim_direction = -math.pi/4
            elif keys[pygame.K_KP1]:  # Down-Left
                self.aim_direction = 3*math.pi/4
            elif keys[pygame.K_KP3]:  # Down-Right
                self.aim_direction = math.pi/4
            self.angle = self.aim_direction

        # Cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Handle deferred weapon switch (avoids event loop blocking)
        if getattr(self, '_want_switch', False):
            self._want_switch = False
            if len(self.weapons) > 1:
                self.current_weapon = (self.current_weapon + 1) % len(self.weapons)
                self.fire_cooldown = 15

    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)

        # Body (flash white when hit) - Player 2 is red/orange
        body_color = WHITE if self.hit_flash > 0 else self.player_color
        pygame.draw.circle(screen, body_color, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(screen, (255, 200, 200), (int(sx), int(sy)), self.radius, 2)

        # Calculate recoil offset (gun pulls back when shooting)
        recoil_offset = self.recoil

        # Get reload animation offsets
        reload_offset_x, reload_offset_y, reload_tilt = self.get_reload_animation_offset()

        # Draw realistic gun based on weapon type
        weapon_name = self.weapon["name"]

        if weapon_name == "Rifle":
            self.draw_rifle(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Handgun":
            self.draw_handgun(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Knife":
            self.draw_knife(screen, sx, sy)
        elif weapon_name == "Grenade":
            self.draw_grenade_weapon(screen, sx, sy)
        elif weapon_name == "Smoke":
            self.draw_smoke_grenade_weapon(screen, sx, sy)
        elif weapon_name == "Shotgun":
            self.draw_shotgun(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "RPG":
            self.draw_rpg(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Sniper":
            self.draw_sniper(screen, sx, sy, recoil_offset, reload_offset_x, reload_offset_y, reload_tilt)
        elif weapon_name == "Minigun":
            self.draw_minigun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Flamethrower":
            self.draw_flamethrower(screen, sx, sy, recoil_offset)
        elif weapon_name == "Laser Gun":
            self.draw_laser_gun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Dual Pistols":
            self.draw_dual_pistols(screen, sx, sy, recoil_offset)
        elif weapon_name == "Crossbow":
            self.draw_crossbow(screen, sx, sy, recoil_offset)
        elif weapon_name == "Electric Gun":
            self.draw_electric_gun(screen, sx, sy, recoil_offset)
        elif weapon_name == "Freeze Ray":
            self.draw_freeze_ray(screen, sx, sy, recoil_offset)
        elif weapon_name == "Throwing Knives":
            self.draw_throwing_knives(screen, sx, sy)
        else:
            # Fallback to simple gun
            gun_length = self.radius + self.weapon["gun_length"] - recoil_offset
            gun_x = sx + math.cos(self.angle) * gun_length
            gun_y = sy + math.sin(self.angle) * gun_length
            pygame.draw.line(screen, DARK_GRAY, (sx, sy), (gun_x, gun_y), 6)

        # Draw reload indicator if reloading
        if self.reloading:
            bar_width = 40
            bar_height = 6
            bar_x = sx - bar_width // 2
            bar_y = sy - self.radius - 20
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            progress_width = int(bar_width * self.reload_phase)
            pygame.draw.rect(screen, (255, 150, 150), (bar_x, bar_y, progress_width, bar_height))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

        # Draw "P2" label above player (use cached font and surface)
        if not hasattr(Player2, '_p2_label_font'):
            Player2._p2_label_font = pygame.font.Font(None, 24)
            Player2._p2_label = Player2._p2_label_font.render("P2", True, (255, 200, 200))
        screen.blit(Player2._p2_label, (sx - Player2._p2_label.get_width()//2, sy - self.radius - 35))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Arena Shooter 2D - Robot Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 32)

        # HUD text cache to avoid render() calls every frame
        self._hud_cache = {}
        self._hud_cache_keys = {}

        self.state = "login"  # login, menu, playing, gameover, shop, avatar_shop, online_menu, waiting
        self.difficulty = "medium"
        self.game_mode = "solo"  # "solo", "pvp", "coop", "online_coop", "online_pvp"
        self.selected_map = "random"  # Map selection: random, arena, corridors, fortress, open
        self.map_names = ["random", "arena", "corridors", "fortress", "open"]
        self.map_index = 0
        self.camera = Camera()
        self.camera2 = Camera()  # Second camera for split-screen
        self.split_screen = False  # Enable split-screen for local multiplayer
        self.shop_prompted = False  # Track if we already asked about RPG

        # Avatar shop state
        self.selected_avatar_index = 0  # Currently selected avatar in shop
        self.pvp_winner = None  # Track winner in PvP mode

        # Online multiplayer state
        self.online_room_code = ""
        self.online_input_code = ""
        self.online_status = "disconnected"  # disconnected, connecting, connected
        self.is_host = False
        self.online_message = ""
        self.last_sync_time = 0
        self.remote_player_data = None
        self.online_input_active = False
        self.online_hosting_started = False
        self.online_joining_started = False
        self.online_game_mode = "coop"  # "coop" or "pvp" for online games
        self.online_difficulty = "medium"  # Difficulty for online co-op
        self.online_difficulty_options = ["easy", "medium", "hard", "impossible"]
        self.online_difficulty_index = 1  # Default to medium
        self.player_name = ""  # Local player's display name
        self.remote_player_name = ""  # Remote player's display name
        self.remote_player3 = None  # For 2v2/2v1 modes (enemy team player 1)
        self.remote_player4 = None  # For 2v2/2v1 modes (enemy team player 2)

        # Login system
        self.username_input = ""
        self.passcode_input = ""
        self.login_mode = "login"  # "login" or "register"
        self.login_message = ""
        self.active_input = "username"  # "username" or "passcode"
        # Cloud login state
        self.cloud_login_pending = False
        self.cloud_login_promise = None
        self.cloud_login_username = ""
        self.cloud_login_passcode = ""

        # Login screen touch button rects (initialized in draw_login_screen)
        self.login_submit_btn = None
        self.login_toggle_btn = None
        self.login_guest_btn = None
        self.username_field_rect = None
        self.passcode_field_rect = None

        # Menu touch button rects (initialized in draw_menu)
        self.menu_buttons = {}  # Dictionary of button_name: pygame.Rect

        # Web version: disable music (too slow to generate in browser)
        self.boss_music = None
        self.menu_music = None
        self.current_music = None

        # Mobile touch controls
        self.mobile_controls = IS_MOBILE
        self.joystick = VirtualJoystick(100, SCREEN_HEIGHT - 120, 60)
        self.aim_joystick = VirtualJoystick(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 120, 60)
        self.shoot_btn = TouchButton(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 200, 35, "FIRE", (200, 60, 60))
        self.reload_btn = TouchButton(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 220, 30, "R", (60, 150, 200))
        self.switch_btn = TouchButton(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 140, 30, "Q", (150, 150, 60))
        self.medkit_btn = TouchButton(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 60, 30, "H", (60, 200, 60))
        self.touch_aim_angle = 0
        self.touch_shooting = False  # Track if touching screen (not on controls) for shooting

        self.reset_game()

    def play_boss_music(self):
        """Play intense boss battle music"""
        if self.boss_music and self.current_music != "boss":
            self.boss_music.play(loops=-1)
            self.current_music = "boss"

    def play_menu_music(self):
        """Play calm menu music"""
        if self.menu_music and self.current_music != "menu":
            pygame.mixer.stop()
            self.menu_music.play(loops=-1)
            self.current_music = "menu"

    def stop_music(self):
        """Stop all music"""
        try:
            pygame.mixer.stop()
        except:
            pass
        self.current_music = None

    def reset_game(self):
        # Player 1 starts on left side, Player 2 on right side (for PvP/coop)
        if self.game_mode == "online_pvp":
            # Online PvP - host spawns left, joiner spawns right
            if self.is_host:
                self.player = Player(MAP_WIDTH // 4, MAP_HEIGHT // 2)
                self.player2 = Player2(3 * MAP_WIDTH // 4, MAP_HEIGHT // 2)
            else:
                # Joiner spawns on right side, sees host on left
                self.player = Player(3 * MAP_WIDTH // 4, MAP_HEIGHT // 2)
                self.player2 = Player2(MAP_WIDTH // 4, MAP_HEIGHT // 2)
        elif self.game_mode == "pvp":
            # Local PvP - players on opposite sides
            self.player = Player(MAP_WIDTH // 4, MAP_HEIGHT // 2)
            self.player2 = Player2(3 * MAP_WIDTH // 4, MAP_HEIGHT // 2)
        elif self.game_mode in ["coop", "online_coop"]:
            self.player = Player(MAP_WIDTH // 2 - 100, MAP_HEIGHT // 2)
            # In online_coop, player2 is controlled by remote player
            self.player2 = Player2(MAP_WIDTH // 2 + 100, MAP_HEIGHT // 2)
        elif self.game_mode == "online_2v2":
            # 2v2: Two local players (left side) vs two remote players (right side)
            self.player = Player(MAP_WIDTH // 4 - 50, MAP_HEIGHT // 2)
            self.player2 = Player2(MAP_WIDTH // 4 + 50, MAP_HEIGHT // 2)
            # Remote players will be controlled via network (player3, player4)
            self.remote_player3 = Player(3 * MAP_WIDTH // 4 - 50, MAP_HEIGHT // 2)
            self.remote_player4 = Player2(3 * MAP_WIDTH // 4 + 50, MAP_HEIGHT // 2)
        elif self.game_mode == "online_2v1":
            # 2v1: Host has 2 players, joiner has 1
            if self.is_host:
                # Host team (2 players on left)
                self.player = Player(MAP_WIDTH // 4 - 50, MAP_HEIGHT // 2)
                self.player2 = Player2(MAP_WIDTH // 4 + 50, MAP_HEIGHT // 2)
                # Remote solo player (right)
                self.remote_player3 = Player(3 * MAP_WIDTH // 4, MAP_HEIGHT // 2)
                self.remote_player4 = None
            else:
                # Joiner is solo (right side)
                self.player = Player(3 * MAP_WIDTH // 4, MAP_HEIGHT // 2)
                self.player2 = None
                # Remote team (left) - 2 players
                self.remote_player3 = Player(MAP_WIDTH // 4 - 50, MAP_HEIGHT // 2)
                self.remote_player4 = Player2(MAP_WIDTH // 4 + 50, MAP_HEIGHT // 2)
        else:
            self.player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
            self.player2 = None

        # Enable split-screen for local multiplayer modes (pvp and coop)
        # Each player gets their own view with their own camera
        if self.game_mode in ["pvp", "coop"]:
            self.split_screen = True
            half_width = SCREEN_WIDTH // 2
            self.camera = Camera(half_width, SCREEN_HEIGHT)
            self.camera2 = Camera(half_width, SCREEN_HEIGHT)
        else:
            self.split_screen = False
            self.camera = Camera()
            self.camera2 = Camera()

        self.pvp_winner = None
        self.robots = []
        self.bullets = []
        self.grenades = []
        self.smoke_grenades = []  # Smoke grenades in flight
        self.smoke_clouds = []  # Active smoke clouds
        self.explosions = []
        self.obstacles = []
        self.shell_casings = []  # Shell casing particles
        self.muzzle_flashes = []  # Muzzle flash effects
        self.healing_effects = []  # Healing visual effects
        self.score = 0
        self.kills = 0
        self.shop_prompted = False
        self.show_save_message = 0  # Timer for save message display

        # Wave system for impossible mode
        self.current_wave = 1
        self.max_waves = 5
        self.boss = None
        self.wave_complete_timer = 0

        self.create_obstacles()

        # After obstacles are created, make sure players aren't stuck in walls
        self.ensure_safe_spawn()

    def ensure_safe_spawn(self):
        """Move players out of obstacles if they spawned inside one"""
        player_radius = 20

        # Check and fix player 1
        for obs in self.obstacles:
            if obs.collides_circle(self.player.x, self.player.y, player_radius):
                # Find a safe spot nearby
                self.player.x, self.player.y = self.find_safe_position(self.player.x, self.player.y, player_radius)
                break

        # Check and fix player 2
        if self.player2:
            for obs in self.obstacles:
                if obs.collides_circle(self.player2.x, self.player2.y, player_radius):
                    self.player2.x, self.player2.y = self.find_safe_position(self.player2.x, self.player2.y, player_radius)
                    break

    def find_safe_position(self, start_x, start_y, radius):
        """Find a position near start_x, start_y that doesn't collide with obstacles"""
        # Try positions in expanding circles
        for dist in range(50, 500, 50):
            for angle in range(0, 360, 45):
                test_x = start_x + dist * math.cos(math.radians(angle))
                test_y = start_y + dist * math.sin(math.radians(angle))

                # Keep in bounds
                test_x = max(100, min(MAP_WIDTH - 100, test_x))
                test_y = max(100, min(MAP_HEIGHT - 100, test_y))

                # Check if this position is safe
                safe = True
                for obs in self.obstacles:
                    if obs.collides_circle(test_x, test_y, radius):
                        safe = False
                        break

                if safe:
                    return test_x, test_y

        # Fallback - return original position
        return start_x, start_y

    def create_obstacles(self):
        self.obstacles = []

        # Border walls (always present)
        wall_thickness = 50
        self.obstacles.append(Obstacle(0, 0, MAP_WIDTH, wall_thickness))  # Top
        self.obstacles.append(Obstacle(0, MAP_HEIGHT - wall_thickness, MAP_WIDTH, wall_thickness))  # Bottom
        self.obstacles.append(Obstacle(0, 0, wall_thickness, MAP_HEIGHT))  # Left
        self.obstacles.append(Obstacle(MAP_WIDTH - wall_thickness, 0, wall_thickness, MAP_HEIGHT))  # Right

        # Create map based on selected map type
        map_type = getattr(self, 'selected_map', 'random')

        if map_type == 'random':
            self.create_random_map()
        elif map_type == 'arena':
            self.create_arena_map()
        elif map_type == 'corridors':
            self.create_corridors_map()
        elif map_type == 'fortress':
            self.create_fortress_map()
        elif map_type == 'open':
            self.create_open_map()
        else:
            self.create_random_map()

    def create_random_map(self):
        """Original random obstacle placement"""
        num_obstacles = 60
        for _ in range(num_obstacles):
            width = random.randint(60, 150)
            height = random.randint(60, 150)
            x = random.randint(100, MAP_WIDTH - 100 - width)
            y = random.randint(100, MAP_HEIGHT - 100 - height)

            # Don't place too close to center (player spawn)
            center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
            if abs(x + width/2 - center_x) > 200 or abs(y + height/2 - center_y) > 200:
                self.obstacles.append(Obstacle(x, y, width, height))

    def create_arena_map(self):
        """Circular arena with pillars"""
        center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2

        # Central pillar
        self.obstacles.append(Obstacle(center_x - 75, center_y - 75, 150, 150))

        # Ring of pillars around center
        ring_radius = 400
        num_pillars = 8
        for i in range(num_pillars):
            angle = (2 * math.pi * i) / num_pillars
            px = center_x + math.cos(angle) * ring_radius - 40
            py = center_y + math.sin(angle) * ring_radius - 40
            self.obstacles.append(Obstacle(int(px), int(py), 80, 80))

        # Outer ring
        outer_radius = 700
        for i in range(12):
            angle = (2 * math.pi * i) / 12 + 0.26  # Offset
            px = center_x + math.cos(angle) * outer_radius - 50
            py = center_y + math.sin(angle) * outer_radius - 50
            self.obstacles.append(Obstacle(int(px), int(py), 100, 100))

    def create_corridors_map(self):
        """Map with corridors and rooms"""
        # Vertical walls creating corridors
        corridor_width = 200
        wall_length = 600

        # Left corridor walls
        self.obstacles.append(Obstacle(400, 100, 60, wall_length))
        self.obstacles.append(Obstacle(400, MAP_HEIGHT - wall_length - 100, 60, wall_length))

        # Right corridor walls
        self.obstacles.append(Obstacle(MAP_WIDTH - 460, 100, 60, wall_length))
        self.obstacles.append(Obstacle(MAP_WIDTH - 460, MAP_HEIGHT - wall_length - 100, 60, wall_length))

        # Horizontal walls
        self.obstacles.append(Obstacle(100, 400, wall_length, 60))
        self.obstacles.append(Obstacle(MAP_WIDTH - wall_length - 100, 400, wall_length, 60))
        self.obstacles.append(Obstacle(100, MAP_HEIGHT - 460, wall_length, 60))
        self.obstacles.append(Obstacle(MAP_WIDTH - wall_length - 100, MAP_HEIGHT - 460, wall_length, 60))

        # Center room walls
        center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        room_size = 300
        wall_gap = 150  # Gap for entry

        # Top wall with gap
        self.obstacles.append(Obstacle(center_x - room_size, center_y - room_size, room_size - wall_gap//2, 40))
        self.obstacles.append(Obstacle(center_x + wall_gap//2, center_y - room_size, room_size - wall_gap//2, 40))
        # Bottom wall with gap
        self.obstacles.append(Obstacle(center_x - room_size, center_y + room_size - 40, room_size - wall_gap//2, 40))
        self.obstacles.append(Obstacle(center_x + wall_gap//2, center_y + room_size - 40, room_size - wall_gap//2, 40))
        # Left wall with gap
        self.obstacles.append(Obstacle(center_x - room_size, center_y - room_size, 40, room_size - wall_gap//2))
        self.obstacles.append(Obstacle(center_x - room_size, center_y + wall_gap//2, 40, room_size - wall_gap//2))
        # Right wall with gap
        self.obstacles.append(Obstacle(center_x + room_size - 40, center_y - room_size, 40, room_size - wall_gap//2))
        self.obstacles.append(Obstacle(center_x + room_size - 40, center_y + wall_gap//2, 40, room_size - wall_gap//2))

    def create_fortress_map(self):
        """Map with four corner fortresses"""
        fort_size = 250
        wall_thick = 50
        gap = 100  # Entry gap

        corners = [
            (150, 150),  # Top-left
            (MAP_WIDTH - 150 - fort_size, 150),  # Top-right
            (150, MAP_HEIGHT - 150 - fort_size),  # Bottom-left
            (MAP_WIDTH - 150 - fort_size, MAP_HEIGHT - 150 - fort_size)  # Bottom-right
        ]

        for fx, fy in corners:
            # Top wall
            self.obstacles.append(Obstacle(fx, fy, fort_size, wall_thick))
            # Bottom wall with gap
            self.obstacles.append(Obstacle(fx, fy + fort_size - wall_thick, (fort_size - gap)//2, wall_thick))
            self.obstacles.append(Obstacle(fx + (fort_size + gap)//2, fy + fort_size - wall_thick, (fort_size - gap)//2, wall_thick))
            # Left wall with gap
            self.obstacles.append(Obstacle(fx, fy, wall_thick, (fort_size - gap)//2))
            self.obstacles.append(Obstacle(fx, fy + (fort_size + gap)//2, wall_thick, (fort_size - gap)//2))
            # Right wall
            self.obstacles.append(Obstacle(fx + fort_size - wall_thick, fy, wall_thick, fort_size))

        # Center cross
        center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        cross_length = 300
        cross_thick = 60
        self.obstacles.append(Obstacle(center_x - cross_length//2, center_y - cross_thick//2, cross_length, cross_thick))
        self.obstacles.append(Obstacle(center_x - cross_thick//2, center_y - cross_length//2, cross_thick, cross_length))

    def create_open_map(self):
        """Very few obstacles - mostly open space"""
        center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2

        # Just 4 pillars near center
        pillar_dist = 350
        pillar_size = 80
        self.obstacles.append(Obstacle(center_x - pillar_dist, center_y - pillar_dist, pillar_size, pillar_size))
        self.obstacles.append(Obstacle(center_x + pillar_dist - pillar_size, center_y - pillar_dist, pillar_size, pillar_size))
        self.obstacles.append(Obstacle(center_x - pillar_dist, center_y + pillar_dist - pillar_size, pillar_size, pillar_size))
        self.obstacles.append(Obstacle(center_x + pillar_dist - pillar_size, center_y + pillar_dist - pillar_size, pillar_size, pillar_size))

    def spawn_robots(self):
        settings = DIFFICULTY[self.difficulty]
        self.robots = []
        total_count = settings["count"]

        # Simple spawn - just place robots at random positions far from player
        for i in range(total_count):
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)
            # Alternate bot types
            bot_type = ["gun", "knife", "throwing_knife", "dual_pistol"][i % 4]
            knife_only = (bot_type == "knife")
            self.robots.append(Robot(x, y, self.difficulty, knife_only=knife_only, bot_type=bot_type))

    def spawn_boss(self):
        """Spawn the boss for impossible mode"""
        # Spawn boss far from player
        while True:
            x = random.randint(200, MAP_WIDTH - 200)
            y = random.randint(200, MAP_HEIGHT - 200)
            dist_to_player = math.sqrt((x - self.player.x)**2 + (y - self.player.y)**2)
            if dist_to_player > 600:
                self.boss = Boss(x, y)
                break

    def next_wave(self):
        """Start the next wave in impossible mode"""
        self.current_wave += 1
        if self.current_wave <= self.max_waves:
            self.spawn_robots()
            # On final wave, spawn the boss too
            if self.current_wave == self.max_waves:
                self.spawn_boss()

    def start_cloud_login(self, username, passcode):
        """Start asynchronous cloud login check"""
        try:
            from platform import window
            if not hasattr(window, 'FirebaseDB'):
                self.login_message = "Cloud not available"
                return

            self.cloud_login_pending = True
            self.cloud_login_username = username
            self.cloud_login_passcode = passcode

            # Start the async verification
            self.cloud_login_promise = window.FirebaseDB.verifyLogin(username, passcode)
            print(f"Starting cloud login check for {username}")
        except Exception as e:
            self.login_message = f"Cloud error: {str(e)[:20]}"
            self.cloud_login_pending = False

    def check_cloud_login(self):
        """Check if cloud login has completed (called each frame)"""
        if not self.cloud_login_pending or not self.cloud_login_promise:
            return

        try:
            from platform import window

            # Check if promise has resolved by looking at its state
            # JavaScript promises have a [[PromiseState]] we can check
            promise = self.cloud_login_promise

            # Use a callback approach - attach handlers to the promise
            # We'll check via a flag set by the callback
            if not hasattr(self, 'cloud_login_result'):
                self.cloud_login_result = None
                self.cloud_login_done = False

                # Define callback functions
                def on_success(result):
                    self.cloud_login_result = result
                    self.cloud_login_done = True

                def on_error(error):
                    self.cloud_login_result = {"success": False, "error": str(error)}
                    self.cloud_login_done = True

                # Attach callbacks using JavaScript's then/catch
                promise.then(window.Function("result", f"""
                    window._cloud_login_result = result;
                    window._cloud_login_done = true;
                """))
                promise.catch(window.Function("error", f"""
                    window._cloud_login_result = {{"success": false, "error": String(error)}};
                    window._cloud_login_done = true;
                """))
                window._cloud_login_done = False

            # Check if JavaScript callback has been called
            if hasattr(window, '_cloud_login_done') and window._cloud_login_done:
                result = window._cloud_login_result
                self.cloud_login_pending = False

                # Clean up
                delattr(self, 'cloud_login_result') if hasattr(self, 'cloud_login_result') else None
                delattr(self, 'cloud_login_done') if hasattr(self, 'cloud_login_done') else None

                if result and result.get("success"):
                    # Cloud login successful - sync data locally
                    cloud_data = result.get("data", {})
                    login_from_cloud_data(self.cloud_login_username, self.cloud_login_passcode, cloud_data)
                    self.login_message = "Cloud login success!"
                    pygame.key.stop_text_input()
                    self.state = "menu"
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Login failed"
                    self.login_message = f"Not found: {error_msg}"

        except Exception as e:
            print(f"Cloud login check error: {e}")
            self.login_message = "Username not found"
            self.cloud_login_pending = False

    def start_game(self, difficulty):
        self.difficulty = difficulty
        # Minimal setup - just clear robots and set position
        self.robots = []
        self.bullets = []
        self.grenades = []
        self.explosions = []
        self.score = 0
        self.kills = 0
        # Reset player position
        self.player.x = MAP_WIDTH // 2
        self.player.y = MAP_HEIGHT // 2
        self.player.health = 100
        self.player.max_health = 100
        if difficulty == "impossible":
            self.player.health = 10000
            self.player.max_health = 10000
        self.state = "playing"

    def _precache_weapon_texts(self):
        """Pre-cache all weapon text renders to avoid stutters during gameplay"""
        # The HUD uses the "weapon" cache key with (text, color) as the lookup key
        # Pre-render the initial ammo for each weapon the player has
        # This warms up pygame's font subsystem to prevent first-switch stutter
        if self.player:
            for weapon in self.player.weapons:
                weapon_name = weapon["name"]
                weapon_color = weapon["color"]
                ammo = weapon["ammo"]
                max_ammo = weapon["max_ammo"]
                text = f"{weapon_name}: {ammo}/{max_ammo}"
                # Force render to warm up the font cache
                self.font.render(text, True, weapon_color)

    def handle_melee_attack(self, attack):
        """Handle knife melee attack - hit robots in close range"""
        melee_range = 50  # Close range for knife
        px, py = attack["x"], attack["y"]
        angle = attack["angle"]
        damage = attack["damage"]

        # Check all robots in melee range and in front of player
        for robot in self.robots[:]:
            dx = robot.x - px
            dy = robot.y - py
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < melee_range:
                # Check if robot is roughly in front of player
                angle_to_robot = math.atan2(dy, dx)
                angle_diff = abs(angle - angle_to_robot)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                if angle_diff < math.pi / 2:  # 90 degree cone in front
                    if robot.take_damage(damage):
                        self.robots.remove(robot)
                        self.kills += 1
                        self.score += DIFFICULTY[self.difficulty]["points"]
                        self.player.add_coin(DIFFICULTY[self.difficulty]["coins"])
                        if self.player.coins >= 10 and not self.player.has_shotgun and not self.shop_prompted:
                            self.state = "shop"
                        elif self.player.coins >= 50 and not self.player.has_rpg and self.player.has_shotgun and not self.shop_prompted:
                            self.state = "shop"

    def handle_player2_shoot(self):
        """Handle Player 2 shooting"""
        if not self.player2 or self.player2.health <= 0:
            return

        # Check weapon type
        if self.player2.weapon.get("grenade", False):
            # Throw grenade
            result = self.player2.shoot()
            if result:
                grenade = Grenade(result["x"], result["y"], result["angle"])
                self.grenades.append(grenade)
        elif self.player2.weapon.get("smoke_grenade", False):
            # Throw smoke grenade
            result = self.player2.shoot()
            if result:
                smoke = SmokeGrenade(result["x"], result["y"], result["angle"])
                self.smoke_grenades.append(smoke)
        elif self.player2.weapon.get("melee", False):
            # Melee attack
            result = self.player2.shoot()
            if result and isinstance(result, dict) and result.get("melee"):
                self.handle_melee_attack_p2(result)
        else:
            # Regular bullet
            result = self.player2.shoot()
            if result:
                # Mark bullet as from player 2 for PvP
                result.owner = "player2"
                self.bullets.append(result)
                self.shell_casings.append(ShellCasing(self.player2.x, self.player2.y, self.player2.angle))
                self.muzzle_flashes.append(MuzzleFlash(self.player2.x, self.player2.y, self.player2.angle))

    def handle_melee_attack_p2(self, attack):
        """Handle Player 2 knife melee attack"""
        melee_range = 50
        px, py = attack["x"], attack["y"]
        angle = attack["angle"]
        damage = attack["damage"]

        # In PvP mode, can hit player 1
        if self.game_mode in ["pvp", "online_pvp"] and self.player.health > 0:
            dx = self.player.x - px
            dy = self.player.y - py
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < melee_range:
                angle_to_target = math.atan2(dy, dx)
                angle_diff = abs(angle - angle_to_target)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                if angle_diff < math.pi / 2:
                    if self.player.take_damage(damage):
                        self.pvp_winner = "Player 2"
                        self.state = "gameover"
                        self.stop_music()
                    return

        # In co-op or if missed player 1, hit robots
        for robot in self.robots[:]:
            dx = robot.x - px
            dy = robot.y - py
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < melee_range:
                angle_to_robot = math.atan2(dy, dx)
                angle_diff = abs(angle - angle_to_robot)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                if angle_diff < math.pi / 2:
                    if robot.take_damage(damage):
                        self.robots.remove(robot)
                        self.kills += 1
                        if self.game_mode != "pvp":
                            self.score += DIFFICULTY[self.difficulty]["points"]

    def handle_touch_events(self, event):
        """Handle touch/mouse events for mobile controls"""
        # Handle login screen touch events (always, not just mobile_controls)
        if self.state == "login":
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                if event.type == pygame.FINGERDOWN:
                    x = event.x * SCREEN_WIDTH
                    y = event.y * SCREEN_HEIGHT
                else:
                    x, y = event.pos

                # Check if tapping on username field
                if self.username_field_rect and self.username_field_rect.collidepoint(x, y):
                    self.active_input = "username"
                    pygame.key.start_text_input()  # Show mobile keyboard
                    return

                # Check if tapping on passcode field
                if self.passcode_field_rect and self.passcode_field_rect.collidepoint(x, y):
                    self.active_input = "passcode"
                    pygame.key.start_text_input()  # Show mobile keyboard
                    return

                # Check submit button
                if self.login_submit_btn and self.login_submit_btn.collidepoint(x, y):
                    if self.login_mode == "register":
                        success, msg = register_user(self.username_input, self.passcode_input)
                        self.login_message = msg
                        if success:
                            login_user(self.username_input, self.passcode_input)
                            pygame.key.stop_text_input()
                            self.state = "menu"
                    else:
                        success, msg = login_user(self.username_input, self.passcode_input)
                        if success:
                            self.login_message = msg
                            pygame.key.stop_text_input()
                            self.state = "menu"
                        elif msg == "Checking cloud...":
                            # Try cloud login
                            self.login_message = "Checking cloud account..."
                            self.start_cloud_login(self.username_input, self.passcode_input)
                        else:
                            self.login_message = msg
                    return

                # Check toggle button (switch between login/register)
                if self.login_toggle_btn and self.login_toggle_btn.collidepoint(x, y):
                    self.login_mode = "register" if self.login_mode == "login" else "login"
                    self.login_message = ""
                    return

                # Check guest button
                if self.login_guest_btn and self.login_guest_btn.collidepoint(x, y):
                    pygame.key.stop_text_input()
                    self.state = "menu"
                    return
            return

        # Handle menu touch events
        if self.state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                if event.type == pygame.FINGERDOWN:
                    x = event.x * SCREEN_WIDTH
                    y = event.y * SCREEN_HEIGHT
                else:
                    x, y = event.pos

                # Check menu buttons
                for btn_name, btn_rect in self.menu_buttons.items():
                    if btn_rect and btn_rect.collidepoint(x, y):
                        # Solo modes - direct state change (no function call)
                        if btn_name == "easy":
                            self.game_mode = "solo"
                            self.difficulty = "easy"
                            self.state = "playing"
                        elif btn_name == "medium":
                            self.game_mode = "solo"
                            self.difficulty = "medium"
                            self.state = "playing"
                        elif btn_name == "hard":
                            self.game_mode = "solo"
                            self.difficulty = "hard"
                            self.state = "playing"
                        elif btn_name == "impossible":
                            self.game_mode = "solo"
                            self.difficulty = "impossible"
                            self.state = "playing"
                        # Online modes
                        elif btn_name == "online_coop":
                            self.online_game_mode = "coop"
                            self.state = "online_menu"
                            self.online_input_code = ""
                            self.online_message = ""
                        elif btn_name == "online_pvp":
                            self.online_game_mode = "pvp"
                            self.state = "online_menu"
                            self.online_input_code = ""
                            self.online_message = ""
                        elif btn_name == "online_2v2":
                            self.online_game_mode = "2v2"
                            self.state = "online_menu"
                            self.online_input_code = ""
                            self.online_message = ""
                        elif btn_name == "online_2v1":
                            self.online_game_mode = "2v1"
                            self.state = "online_menu"
                            self.online_input_code = ""
                            self.online_message = ""
                        # Local multiplayer - direct state change
                        elif btn_name == "local_pvp":
                            self.game_mode = "pvp"
                            self.difficulty = "pvp"
                            self.state = "playing"
                        elif btn_name == "coop_easy":
                            self.game_mode = "coop"
                            self.difficulty = "easy"
                            self.state = "playing"
                        elif btn_name == "coop_med":
                            self.game_mode = "coop"
                            self.difficulty = "medium"
                            self.state = "playing"
                        elif btn_name == "coop_hard":
                            self.game_mode = "coop"
                            self.difficulty = "hard"
                            self.state = "playing"
                        elif btn_name == "coop_imp":
                            self.game_mode = "coop"
                            self.difficulty = "impossible"
                            self.state = "playing"
                        # Map selection
                        elif btn_name == "map_left":
                            self.map_index = (self.map_index - 1) % len(self.map_names)
                            self.selected_map = self.map_names[self.map_index]
                        elif btn_name == "map_right":
                            self.map_index = (self.map_index + 1) % len(self.map_names)
                            self.selected_map = self.map_names[self.map_index]
                        # Login/logout
                        elif btn_name == "login":
                            if current_user:
                                logout_user()
                            else:
                                self.state = "login"
                                self.username_input = ""
                                self.passcode_input = ""
                                self.login_message = ""
                        # Touch toggle
                        elif btn_name == "touch_toggle":
                            self.mobile_controls = not self.mobile_controls
                        return
            return

        if not self.mobile_controls or self.state != "playing":
            return

        touch_id = getattr(event, 'finger_id', 0)

        if event.type == pygame.FINGERDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            if event.type == pygame.FINGERDOWN:
                x = event.x * SCREEN_WIDTH
                y = event.y * SCREEN_HEIGHT
            else:
                x, y = event.pos
                touch_id = 0

            # Check if touch is on any control
            on_joystick = self.joystick.contains_point(x, y) or self.aim_joystick.contains_point(x, y)
            on_button = (self.shoot_btn.contains_point(x, y) or self.reload_btn.contains_point(x, y) or
                        self.switch_btn.contains_point(x, y) or self.medkit_btn.contains_point(x, y))

            # If touch is NOT on any control, it's a shooting touch
            if not on_joystick and not on_button:
                self.touch_shooting = True

            # Check joystick
            self.joystick.handle_touch_down(x, y, touch_id)
            # Check aim joystick
            self.aim_joystick.handle_touch_down(x, y, touch_id + 100)
            # Check buttons
            self.shoot_btn.handle_touch_down(x, y, touch_id)
            self.reload_btn.handle_touch_down(x, y, touch_id)
            self.switch_btn.handle_touch_down(x, y, touch_id)
            self.medkit_btn.handle_touch_down(x, y, touch_id)

        elif event.type == pygame.FINGERMOTION or event.type == pygame.MOUSEMOTION:
            if event.type == pygame.FINGERMOTION:
                x = event.x * SCREEN_WIDTH
                y = event.y * SCREEN_HEIGHT
            else:
                x, y = event.pos
                touch_id = 0
                if not pygame.mouse.get_pressed()[0]:
                    return

            self.joystick.handle_touch_move(x, y, touch_id)
            self.aim_joystick.handle_touch_move(x, y, touch_id + 100)

        elif event.type == pygame.FINGERUP or event.type == pygame.MOUSEBUTTONUP:
            self.joystick.handle_touch_up(touch_id)
            self.aim_joystick.handle_touch_up(touch_id + 100)
            # Reset touch shooting
            self.touch_shooting = False
            # Handle button releases and actions
            if self.reload_btn.pressed and self.reload_btn.touch_id == touch_id:
                if not self.player.reloading:
                    self.player.start_reload()
            if self.switch_btn.pressed and self.switch_btn.touch_id == touch_id:
                self.player.switch_weapon()
            if self.medkit_btn.pressed and self.medkit_btn.touch_id == touch_id:
                if self.player.use_medkit():
                    self.healing_effects.append(HealingEffect(self.player.x, self.player.y))
            self.shoot_btn.handle_touch_up(touch_id)
            self.reload_btn.handle_touch_up(touch_id)
            self.switch_btn.handle_touch_up(touch_id)
            self.medkit_btn.handle_touch_up(touch_id)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Handle touch events for mobile
            if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP,
                              pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                self.handle_touch_events(event)

            if event.type == pygame.KEYDOWN:
                if self.state == "login":
                    if event.key == pygame.K_TAB:
                        # Switch between username and passcode
                        self.active_input = "passcode" if self.active_input == "username" else "username"
                    elif event.key == pygame.K_r:
                        # Toggle between login and register mode
                        self.login_mode = "register" if self.login_mode == "login" else "login"
                        self.login_message = ""
                    elif event.key == pygame.K_RETURN:
                        # Submit login/register
                        if self.login_mode == "register":
                            success, msg = register_user(self.username_input, self.passcode_input)
                            self.login_message = msg
                            if success:
                                # Auto-login after register
                                login_user(self.username_input, self.passcode_input)
                                pygame.key.stop_text_input()
                                self.state = "menu"
                        else:
                            success, msg = login_user(self.username_input, self.passcode_input)
                            if success:
                                self.login_message = msg
                                pygame.key.stop_text_input()
                                self.state = "menu"
                            else:
                                # Show error, don't try cloud (causes freeze)
                                self.login_message = msg if msg != "Checking cloud..." else "User not found"
                    elif event.key == pygame.K_ESCAPE:
                        # Play as guest (skip login)
                        pygame.key.stop_text_input()
                        self.state = "menu"
                    elif event.key == pygame.K_BACKSPACE:
                        # Delete character
                        if self.active_input == "username":
                            self.username_input = self.username_input[:-1]
                        else:
                            self.passcode_input = self.passcode_input[:-1]
                    else:
                        # Add character to input
                        char = event.unicode
                        if char.isalnum() or char == "_":
                            if self.active_input == "username" and len(self.username_input) < 20:
                                self.username_input += char
                            elif self.active_input == "passcode" and len(self.passcode_input) < 20:
                                self.passcode_input += char

                elif self.state == "menu":
                    if event.key == pygame.K_1:
                        self.game_mode = "solo"
                        self.difficulty = "easy"
                        self.state = "playing"
                    elif event.key == pygame.K_2:
                        self.game_mode = "solo"
                        self.difficulty = "medium"
                        self.state = "playing"
                    elif event.key == pygame.K_3:
                        self.game_mode = "solo"
                        self.difficulty = "hard"
                        self.state = "playing"
                    elif event.key == pygame.K_4:
                        self.game_mode = "solo"
                        self.difficulty = "impossible"
                        self.state = "playing"
                    elif event.key == pygame.K_5:
                        self.game_mode = "pvp"
                        self.difficulty = "pvp"
                        self.state = "playing"
                    elif event.key == pygame.K_6:
                        self.game_mode = "coop"
                        self.difficulty = "easy"
                        self.state = "playing"
                    elif event.key == pygame.K_7:
                        self.game_mode = "coop"
                        self.difficulty = "medium"
                        self.state = "playing"
                    elif event.key == pygame.K_8:
                        self.game_mode = "coop"
                        self.difficulty = "hard"
                        self.state = "playing"
                    elif event.key == pygame.K_9:
                        self.game_mode = "coop"
                        self.difficulty = "impossible"
                        self.state = "playing"
                    elif event.key == pygame.K_0:
                        # Online CO-OP menu
                        self.online_game_mode = "coop"
                        self.state = "online_menu"
                        self.online_input_code = ""
                        self.online_message = ""
                    elif event.key == pygame.K_p:
                        # Online PVP menu
                        self.online_game_mode = "pvp"
                        self.state = "online_menu"
                        self.online_input_code = ""
                        self.online_message = ""
                    elif event.key == pygame.K_l:
                        # L key - Login/Logout
                        if current_user:
                            logout_user()
                        else:
                            self.state = "login"
                            self.username_input = ""
                            self.passcode_input = ""
                            self.login_message = ""
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_COMMA:
                        # Previous map (< key or left arrow)
                        self.map_index = (self.map_index - 1) % len(self.map_names)
                        self.selected_map = self.map_names[self.map_index]
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_PERIOD:
                        # Next map (> key or right arrow)
                        self.map_index = (self.map_index + 1) % len(self.map_names)
                        self.selected_map = self.map_names[self.map_index]
                    elif event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_t:
                        # Toggle touch controls
                        self.mobile_controls = not self.mobile_controls

                elif self.state == "playing":
                    # Player 1 controls
                    if event.key == pygame.K_r:
                        # Start reload animation (don't instant reload)
                        if not self.player.reloading:
                            self.player.start_reload()
                    elif event.key == pygame.K_q:
                        # Q to switch to next weapon
                        if self.player and len(self.player.weapons) > 1:
                            self.player.current_weapon = (self.player.current_weapon + 1) % len(self.player.weapons)
                    elif event.key == pygame.K_e:
                        # E to switch to previous weapon
                        if self.player and len(self.player.weapons) > 1:
                            self.player.current_weapon = (self.player.current_weapon - 1) % len(self.player.weapons)
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                                       pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                        # Direct weapon selection with number keys
                        weapon_idx = event.key - pygame.K_1  # 0-8
                        if self.player and weapon_idx < len(self.player.weapons):
                            self.player.current_weapon = weapon_idx
                            self.player.fire_cooldown = 15
                    elif event.key == pygame.K_RETURN:
                        # Knife attack with Enter key
                        if self.player.weapon.get("melee", False):
                            result = self.player.shoot()
                            if result and isinstance(result, dict) and result.get("melee"):
                                self.handle_melee_attack(result)
                    elif event.key == pygame.K_h:
                        # Use medkit
                        if self.player.use_medkit():
                            self.healing_effects.append(HealingEffect(self.player.x, self.player.y))
                    elif event.key == pygame.K_TAB:
                        # Open shop (only in solo/coop)
                        if self.game_mode != "pvp":
                            self.state = "shop"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.game_mode = "solo"
                        self.play_menu_music()
                    elif event.key == pygame.K_t:
                        # Toggle touch controls
                        self.mobile_controls = not self.mobile_controls

                    # Player 2 controls (only in multiplayer modes)
                    if self.player2 and self.player2.health > 0:
                        if event.key == pygame.K_p:
                            # P key - Player 2 reload
                            if not self.player2.reloading:
                                self.player2.start_reload()
                        elif event.key == pygame.K_u:
                            # U key - Player 2 switch weapon
                            self.player2.switch_weapon()
                        elif event.key == pygame.K_o:
                            # O key - Player 2 shoot
                            self.handle_player2_shoot()

                elif self.state == "gameover":
                    if event.key == pygame.K_r:
                        self.start_game(self.difficulty)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.play_menu_music()

                elif self.state == "shop":
                    if event.key == pygame.K_1:
                        # Buy Shotgun
                        if not self.player.has_shotgun and self.player.coins >= 10:
                            self.player.unlock_shotgun()
                        self.state = "playing"
                    elif event.key == pygame.K_2:
                        # Buy RPG
                        if not self.player.has_rpg and self.player.coins >= 50:
                            self.player.unlock_rpg()
                        self.state = "playing"
                    elif event.key == pygame.K_3:
                        # Buy Medkit (one-time purchase only)
                        if self.player.coins >= 90 and self.player.medkit_charges == 0:
                            self.player.coins -= 90
                            self.player.medkit_charges = 3
                            self.player.save_progress()
                        self.state = "playing"
                    elif event.key == pygame.K_4:
                        # Buy Sniper
                        if not self.player.has_sniper and self.player.coins >= 150:
                            self.player.unlock_sniper()
                        self.state = "playing"
                    elif event.key == pygame.K_5:
                        # Buy Dual Pistols
                        if not self.player.has_dual_pistols and self.player.coins >= 60:
                            self.player.unlock_dual_pistols()
                        self.state = "playing"
                    elif event.key == pygame.K_6:
                        # Buy Throwing Knives
                        if not self.player.has_throwing_knives and self.player.coins >= 70:
                            self.player.unlock_throwing_knives()
                        self.state = "playing"
                    elif event.key == pygame.K_7:
                        # Buy Flamethrower
                        if not self.player.has_flamethrower and self.player.coins >= 80:
                            self.player.unlock_flamethrower()
                        self.state = "playing"
                    elif event.key == pygame.K_8:
                        # Buy Crossbow
                        if not self.player.has_crossbow and self.player.coins >= 100:
                            self.player.unlock_crossbow()
                        self.state = "playing"
                    elif event.key == pygame.K_9:
                        # Buy Freeze Ray
                        if not self.player.has_freeze and self.player.coins >= 110:
                            self.player.unlock_freeze()
                        self.state = "playing"
                    elif event.key == pygame.K_0:
                        # Buy Laser Gun
                        if not self.player.has_laser and self.player.coins >= 120:
                            self.player.unlock_laser()
                        self.state = "playing"
                    elif event.key == pygame.K_e:
                        # Buy Electric Gun
                        if not self.player.has_electric and self.player.coins >= 140:
                            self.player.unlock_electric()
                        self.state = "playing"
                    elif event.key == pygame.K_m:
                        # Buy Minigun
                        if not self.player.has_minigun and self.player.coins >= 200:
                            self.player.unlock_minigun()
                        self.state = "playing"
                    elif event.key == pygame.K_a:
                        # Open Avatar Shop
                        self.state = "avatar_shop"
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_n:
                        # Close shop - stop auto-prompting
                        self.shop_prompted = True
                        self.state = "playing"

                elif self.state == "avatar_shop":
                    avatar_keys = list(AVATAR_TYPES.keys())
                    if event.key == pygame.K_LEFT:
                        self.selected_avatar_index = (self.selected_avatar_index - 1) % len(avatar_keys)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_avatar_index = (self.selected_avatar_index + 1) % len(avatar_keys)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Buy or equip the selected avatar
                        selected_type = avatar_keys[self.selected_avatar_index]
                        avatar_data = AVATAR_TYPES[selected_type]

                        if selected_type in self.player.owned_avatars:
                            # Already owned - equip it
                            self.player.set_avatar(selected_type)
                            self.player.save_progress()
                        elif self.player.coins >= avatar_data["price"]:
                            # Buy it
                            self.player.coins -= avatar_data["price"]
                            self.player.owned_avatars.append(selected_type)
                            self.player.set_avatar(selected_type)
                            self.player.save_progress()
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        # Go back to weapon shop
                        self.state = "shop"

                elif self.state == "online_menu":
                    if event.key == pygame.K_1 and not self.online_input_active:
                        # Select Co-op mode (only when not entering room code)
                        self.online_game_mode = "coop"
                        self.online_message = "CO-OP mode selected"
                    elif event.key == pygame.K_2 and not self.online_input_active:
                        # Select PvP mode (only when not entering room code)
                        self.online_game_mode = "pvp"
                        self.online_message = "1v1 PVP mode selected"
                    elif event.key == pygame.K_3 and not self.online_input_active:
                        # Select 2v2 mode
                        self.online_game_mode = "2v2"
                        self.online_message = "2v2 TEAM mode selected"
                    elif event.key == pygame.K_4 and not self.online_input_active:
                        # Select 2v1 mode
                        self.online_game_mode = "2v1"
                        self.online_message = "2v1 mode selected"
                    elif event.key == pygame.K_LEFT and self.online_game_mode in ["coop", "2v2", "2v1"]:
                        # Previous difficulty
                        self.online_difficulty_index = (self.online_difficulty_index - 1) % len(self.online_difficulty_options)
                        self.online_difficulty = self.online_difficulty_options[self.online_difficulty_index]
                        self.online_message = f"Difficulty: {self.online_difficulty.upper()}"
                    elif event.key == pygame.K_RIGHT and self.online_game_mode in ["coop", "2v2", "2v1"]:
                        # Next difficulty
                        self.online_difficulty_index = (self.online_difficulty_index + 1) % len(self.online_difficulty_options)
                        self.online_difficulty = self.online_difficulty_options[self.online_difficulty_index]
                        self.online_message = f"Difficulty: {self.online_difficulty.upper()}"
                    elif event.key == pygame.K_h:
                        # Host a game
                        mode_names = {"coop": "CO-OP", "pvp": "1v1 PVP", "2v2": "2v2 TEAM", "2v1": "2v1"}
                        mode_name = mode_names.get(self.online_game_mode, "")
                        self.online_message = f"Creating {mode_name} room..."
                        self.is_host = True
                        self.state = "waiting"
                        # Will call JS to host game in update loop
                    elif event.key == pygame.K_j:
                        # Join a game - switch to input mode
                        self.online_message = "Enter room code:"
                        self.online_input_active = True
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.online_message = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.online_input_code = self.online_input_code[:-1]
                    elif event.key == pygame.K_RETURN and len(self.online_input_code) == 4:
                        # Join with entered code
                        self.online_message = f"Joining room {self.online_input_code}..."
                        self.is_host = False
                        self.state = "waiting"
                    elif event.unicode.isdigit() and len(self.online_input_code) < 4 and self.online_input_active:
                        # Add digit to room code when in input mode
                        self.online_input_code += event.unicode

                elif self.state == "waiting":
                    if event.key == pygame.K_ESCAPE:
                        # Cancel and disconnect
                        self.state = "menu"
                        self.online_status = "disconnected"
                        self.online_message = ""
                        self.online_room_code = ""

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.state == "login":
                    # Handle clicks on login input fields
                    mouse_pos = pygame.mouse.get_pos()
                    box_width = 450
                    box_x = SCREEN_WIDTH // 2 - box_width // 2
                    box_y = 200
                    # Username field area
                    username_rect = pygame.Rect(box_x + 25, box_y + 95, box_width - 50, 35)
                    # Passcode field area
                    passcode_rect = pygame.Rect(box_x + 25, box_y + 175, box_width - 50, 35)
                    if username_rect.collidepoint(mouse_pos):
                        self.active_input = "username"
                        pygame.key.start_text_input()
                    elif passcode_rect.collidepoint(mouse_pos):
                        self.active_input = "passcode"
                        pygame.key.start_text_input()
                elif event.button == 1 and self.state == "playing":
                    # Check if shop button clicked
                    mouse_pos = pygame.mouse.get_pos()
                    if hasattr(self, 'shop_btn_rect') and self.shop_btn_rect.collidepoint(mouse_pos):
                        self.state = "shop"
                    # Check weapon type
                    elif self.player.weapon.get("grenade", False):
                        # Throw grenade
                        result = self.player.shoot()
                        if result:
                            grenade = Grenade(result["x"], result["y"], result["angle"])
                            self.grenades.append(grenade)
                    elif self.player.weapon.get("smoke_grenade", False):
                        # Throw smoke grenade
                        result = self.player.shoot()
                        if result:
                            smoke = SmokeGrenade(result["x"], result["y"], result["angle"])
                            self.smoke_grenades.append(smoke)
                    elif self.player.weapon.get("melee", False):
                        # Knife melee attack
                        result = self.player.shoot()
                        if result and isinstance(result, dict) and result.get("melee"):
                            self.handle_melee_attack(result)
                    else:
                        result = self.player.shoot()
                        if result:
                            self.bullets.append(result)
                elif event.button == 1 and self.state == "online_menu":
                    # Handle touch/click on online menu buttons
                    mouse_pos = pygame.mouse.get_pos()
                    # Mode selection buttons
                    if hasattr(self, 'online_coop_btn') and self.online_coop_btn.collidepoint(mouse_pos):
                        self.online_game_mode = "coop"
                        self.online_message = "CO-OP mode selected"
                    elif hasattr(self, 'online_pvp_btn') and self.online_pvp_btn.collidepoint(mouse_pos):
                        self.online_game_mode = "pvp"
                        self.online_message = "1v1 PVP mode selected"
                    elif hasattr(self, 'online_2v2_btn') and self.online_2v2_btn.collidepoint(mouse_pos):
                        self.online_game_mode = "2v2"
                        self.online_message = "2v2 TEAM mode selected"
                    elif hasattr(self, 'online_2v1_btn') and self.online_2v1_btn.collidepoint(mouse_pos):
                        self.online_game_mode = "2v1"
                        self.online_message = "2v1 mode selected"
                    # Difficulty buttons
                    elif hasattr(self, 'online_diff_left_btn') and self.online_diff_left_btn.collidepoint(mouse_pos):
                        self.online_difficulty_index = (self.online_difficulty_index - 1) % len(self.online_difficulty_options)
                        self.online_difficulty = self.online_difficulty_options[self.online_difficulty_index]
                        self.online_message = f"Difficulty: {self.online_difficulty.upper()}"
                    elif hasattr(self, 'online_diff_right_btn') and self.online_diff_right_btn.collidepoint(mouse_pos):
                        self.online_difficulty_index = (self.online_difficulty_index + 1) % len(self.online_difficulty_options)
                        self.online_difficulty = self.online_difficulty_options[self.online_difficulty_index]
                        self.online_message = f"Difficulty: {self.online_difficulty.upper()}"
                    # Host/Join buttons
                    elif hasattr(self, 'online_host_btn') and self.online_host_btn.collidepoint(mouse_pos):
                        mode_names = {"coop": "CO-OP", "pvp": "1v1 PVP", "2v2": "2v2 TEAM", "2v1": "2v1"}
                        mode_name = mode_names.get(self.online_game_mode, "")
                        self.online_message = f"Creating {mode_name} room..."
                        self.is_host = True
                        self.state = "waiting"
                    elif hasattr(self, 'online_join_btn') and self.online_join_btn.collidepoint(mouse_pos):
                        self.online_message = "Enter room code:"
                        self.online_input_active = True
                    # Back button
                    elif hasattr(self, 'online_back_btn') and self.online_back_btn.collidepoint(mouse_pos):
                        self.state = "menu"
                        self.online_message = ""

        # Continuous shooting while mouse held (not for melee or grenade)
        # On mobile: only shoot if touching screen (not on joystick/buttons) OR shoot button pressed
        if self.state == "playing":
            should_shoot = False
            if self.mobile_controls:
                # On mobile: shoot if touching outside controls OR fire button pressed
                should_shoot = self.touch_shooting or self.shoot_btn.pressed
            else:
                # On desktop: use mouse click
                should_shoot = pygame.mouse.get_pressed()[0]

            if should_shoot and not self.player.weapon.get("melee", False) and not self.player.weapon.get("grenade", False) and not self.player.weapon.get("smoke_grenade", False):
                result = self.player.shoot()
                if result:
                    self.bullets.append(result)
                    # Add realistic gun effects
                    self.add_gun_effects()

        return True

    def add_gun_effects(self):
        """Add muzzle flash, shell casing, and recoil when shooting"""
        weapon_name = self.player.weapon["name"]

        # Calculate muzzle position (end of gun barrel)
        gun_lengths = {"Rifle": 28, "Handgun": 16, "Shotgun": 32, "Sniper": 40, "RPG": 35}
        gun_length = gun_lengths.get(weapon_name, 20)
        muzzle_x = self.player.x + math.cos(self.player.angle) * gun_length
        muzzle_y = self.player.y + math.sin(self.player.angle) * gun_length

        # Add muzzle flash (not for RPG - it has backblast)
        if weapon_name != "RPG":
            flash_size = {"Rifle": 1.0, "Handgun": 0.7, "Shotgun": 1.5, "Sniper": 1.2}.get(weapon_name, 1.0)
            self.muzzle_flashes.append(MuzzleFlash(muzzle_x, muzzle_y, self.player.angle, flash_size))

        # Add shell casing (not for RPG or Shotgun pump)
        if weapon_name in ["Rifle", "Handgun", "Sniper"]:
            # Shell ejects from ejection port (side of gun)
            eject_x = self.player.x + math.cos(self.player.angle) * (self.player.radius + 8)
            eject_y = self.player.y + math.sin(self.player.angle) * (self.player.radius + 8)
            self.shell_casings.append(ShellCasing(eject_x, eject_y, self.player.angle))

        # Apply recoil based on weapon
        recoil_amounts = {"Rifle": 3, "Handgun": 2, "Shotgun": 8, "Sniper": 6, "RPG": 10}
        recoil = recoil_amounts.get(weapon_name, 2)
        self.player.apply_recoil(recoil)

    def update_online_connection(self):
        """Handle online multiplayer connection state"""
        try:
            import platform
            window = platform.window
        except:
            self.online_message = "Online only available in web version"
            return

        # Check if MP (multiplayer) object exists
        if not hasattr(window, 'MP'):
            self.online_message = "Multiplayer loading..."
            return

        # Host game
        if self.is_host and not self.online_hosting_started:
            self.online_hosting_started = True
            self.online_status = "connecting"
            self.online_message = "Creating room..."
            # Call JavaScript to host
            try:
                result = window.MP.hostGame()
                # Result is a promise, we'll check status each frame
            except Exception as e:
                self.online_message = f"Error: {str(e)}"

        # Join game
        elif not self.is_host and not self.online_joining_started and self.online_input_code:
            self.online_joining_started = True
            self.online_status = "connecting"
            self.online_message = f"Joining room {self.online_input_code}..."
            try:
                window.MP.joinGame(self.online_input_code)
            except Exception as e:
                self.online_message = f"Error: {str(e)}"

        # Check connection status from JavaScript
        try:
            status = window.MP.getConnectionStatus()
            self.online_status = status

            if self.is_host:
                room_code = window.MP.getRoomCode()
                if room_code:
                    self.online_room_code = room_code
                    self.online_message = "Waiting for player to join..."

            if status == "connected":
                self.online_message = "Connected! Starting game..."
                # Set player name from login username
                self.player_name = self.username_input if self.username_input else "Player"
                # Start the game in selected online mode
                if self.online_game_mode == "pvp":
                    self.game_mode = "online_pvp"
                    self.start_game("medium")  # PvP doesn't need difficulty
                elif self.online_game_mode == "2v2":
                    self.game_mode = "online_2v2"
                    self.start_game(self.online_difficulty)
                elif self.online_game_mode == "2v1":
                    self.game_mode = "online_2v1"
                    self.start_game(self.online_difficulty)
                else:
                    self.game_mode = "online_coop"
                    self.start_game(self.online_difficulty)  # Use selected difficulty
                # Reset online state flags for next time
                self.online_hosting_started = False
                self.online_joining_started = False
        except Exception as e:
            pass  # Status check failed, will retry next frame

    def disconnect_online(self):
        """Disconnect from online multiplayer"""
        try:
            import platform
            window = platform.window
            if hasattr(window, 'MP'):
                window.MP.disconnect()
        except:
            pass
        self.online_status = "disconnected"
        self.online_room_code = ""
        self.remote_player_name = ""

    def send_game_state(self):
        """Send local player state to remote player"""
        try:
            import platform
            import json
            window = platform.window

            if not hasattr(window, 'MP'):
                return

            # In online co-op, both players control self.player with WASD/mouse
            # We send OUR player data to the other person (shows as player2 on their screen)
            player = self.player

            if not player:
                return

            # Build state to send
            state = {
                "x": player.x,
                "y": player.y,
                "angle": player.angle,
                "health": player.health,
                "weapon_idx": player.weapon_idx if hasattr(player, 'weapon_idx') else 0,
                "shooting": pygame.mouse.get_pressed()[0],
                "name": self.player_name if self.player_name else self.username_input,
                "gameover": self.state == "gameover",
                "i_won": self.pvp_winner == "Player 1" if self.pvp_winner else False
            }

            window.MP.sendData(json.dumps(state))
        except Exception as e:
            pass

    def receive_game_state(self):
        """Receive remote player state and update"""
        try:
            import platform
            import json
            window = platform.window

            if not hasattr(window, 'MP'):
                return

            # Get received data from JavaScript
            data_list = window.MP.getReceivedData()

            if not data_list:
                return

            # Process latest state (skip older states)
            for data_str in data_list:
                try:
                    state = json.loads(data_str)

                    # Remote player's data shows as player2 on our screen
                    remote = self.player2

                    if remote:
                        remote.x = state.get("x", remote.x)
                        remote.y = state.get("y", remote.y)
                        remote.angle = state.get("angle", remote.angle)
                        # Don't sync health directly, let damage happen locally

                        # Get remote player name and check for duplicate
                        if state.get("name"):
                            remote_name = state.get("name")
                            # Check if remote player has same username as local player
                            if remote_name.lower() == self.player_name.lower():
                                # Duplicate account detected - kick back to menu
                                self.online_message = "ERROR: Someone with same username already in game!"
                                self.state = "online_menu"
                                self.disconnect_online()
                                return
                            self.remote_player_name = remote_name

                        # Handle remote shooting
                        if state.get("shooting") and hasattr(remote, 'shoot'):
                            if not remote.weapon.get("melee", False):
                                result = remote.shoot()
                                if result:
                                    # Mark bullet as from player2 for PvP collision detection
                                    result.owner = "player2"
                                    self.bullets.append(result)

                        # Handle gameover sync for online PvP
                        if self.game_mode == "online_pvp" and state.get("gameover"):
                            if state.get("i_won"):
                                # Remote player won, so we lost
                                self.pvp_winner = "Player 2"
                                self.state = "gameover"
                                self.stop_music()

                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass

    def update(self):
        # Deferred game start (avoids freeze in event handler)
        if getattr(self, '_need_start_game', False):
            self._need_start_game = False
            self.start_game(self.difficulty)
            return

        # Check for pending cloud login
        if self.cloud_login_pending:
            self.check_cloud_login()

        # Handle waiting state for online multiplayer
        if self.state == "waiting":
            self.update_online_connection()
            return

        # Handle online multiplayer sync (even during gameover to sync winner/loser)
        if self.game_mode in ["online_coop", "online_pvp", "online_2v2", "online_2v1"]:
            self.send_game_state()
            self.receive_game_state()

        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Handle mobile joystick movement
        if self.mobile_controls and self.joystick.active:
            # Use module-level FakeKeys class (faster than defining class inside function)
            keys = FakeKeys(self.joystick.dx, self.joystick.dy)

        # Handle mobile aim joystick
        if self.mobile_controls and self.aim_joystick.active:
            # Calculate aim angle from joystick
            if abs(self.aim_joystick.dx) > 0.1 or abs(self.aim_joystick.dy) > 0.1:
                self.touch_aim_angle = math.atan2(self.aim_joystick.dy, self.aim_joystick.dx)
                # Convert angle to screen position for player aim
                aim_x = self.player.x - self.camera.x + math.cos(self.touch_aim_angle) * 100
                aim_y = self.player.y - self.camera.y + math.sin(self.touch_aim_angle) * 100
                mouse_pos = (aim_x, aim_y)

        # Handle mobile shooting (FIRE button or touch screen outside controls)
        # Note: main shooting logic is in handle_events, this handles melee and effects
        if self.mobile_controls and (self.shoot_btn.pressed or self.touch_shooting):
            if self.player.weapon.get("melee", False):
                result = self.player.shoot()
                if result and isinstance(result, dict) and result.get("melee"):
                    self.handle_melee_attack(result)

        # Update player
        self.player.update(keys, mouse_pos, self.camera, self.obstacles)
        self.player.update_recoil()  # Update recoil recovery
        self.player.update_reload()  # Update reload animation
        self.player.update_switch_cooldown()  # Update weapon switch cooldown

        # Update Player 2 (in multiplayer modes)
        # In online modes, player2 is controlled by network data, not local input
        if self.player2 and self.player2.health > 0 and self.game_mode not in ["online_coop", "online_pvp"]:
            # In co-op, Player 2 aims at nearest robot; in PvP, aim at Player 1
            target_pos = None
            if self.game_mode == "coop" and self.robots:
                # Find nearest robot
                nearest_dist = float('inf')
                for robot in self.robots:
                    dist = math.sqrt((robot.x - self.player2.x)**2 + (robot.y - self.player2.y)**2)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        target_pos = (robot.x, robot.y)
            # In PvP, numpad controls aim (no auto-aim at player 1)

            self.player2.update(keys, target_pos, self.camera, self.obstacles)
            self.player2.update_recoil()
            self.player2.update_reload()
            self.player2.update_switch_cooldown()

        # Update camera(s)
        if self.split_screen:
            # Split-screen: each camera follows its player
            self.camera.update(self.player.x, self.player.y)
            if self.player2:
                self.camera2.update(self.player2.x, self.player2.y)
        elif self.game_mode == "online_pvp":
            # Online PvP: camera follows only your own player (no split-screen needed)
            self.camera.update(self.player.x, self.player.y)
        elif self.game_mode == "online_coop" and self.player2 and self.player2.health > 0 and self.player.health > 0:
            # Online co-op: focus on midpoint between players
            mid_x = (self.player.x + self.player2.x) // 2
            mid_y = (self.player.y + self.player2.y) // 2
            self.camera.update(mid_x, mid_y)
        elif self.game_mode == "coop" and self.player2 and self.player2.health > 0 and self.player.health > 0:
            # Local co-op: focus on midpoint between players
            mid_x = (self.player.x + self.player2.x) // 2
            mid_y = (self.player.y + self.player2.y) // 2
            self.camera.update(mid_x, mid_y)
        else:
            self.camera.update(self.player.x, self.player.y)

        # Update shell casings
        for casing in self.shell_casings[:]:
            if not casing.update():
                self.shell_casings.remove(casing)

        # Update muzzle flashes
        for flash in self.muzzle_flashes[:]:
            if not flash.update():
                self.muzzle_flashes.remove(flash)

        # Update healing effects
        for effect in self.healing_effects[:]:
            if not effect.update(self.player.x, self.player.y):
                self.healing_effects.remove(effect)

        # Update bullets (simple - no collision)
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.lifetime <= 0:
                self.bullets.remove(bullet)

        # Update robots (simple - no collision)
        for robot in self.robots[:]:
            robot.update(self.player, self.obstacles)

        # TEST: Return before complex collision detection
        return

        # Update bullets (FULL - with collision)
        for bullet in self.bullets[:]:
            bullet.update()

            if bullet.lifetime <= 0:
                self.bullets.remove(bullet)
                continue

            # Check obstacle collision
            for obs in self.obstacles:
                if obs.collides_point(bullet.x, bullet.y):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

            if bullet not in self.bullets:
                continue

            # Player bullets hit robots (and other player in PvP)
            if bullet.is_player:
                hit_something = False
                bullet_owner = getattr(bullet, 'owner', 'player1')

                # In PvP mode, check if bullet hits the OTHER player
                if self.game_mode in ["pvp", "online_pvp"]:
                    if bullet_owner == "player2" and self.player.health > 0:
                        # Player 2's bullet can hit Player 1
                        dist = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
                        if dist < self.player.radius + bullet.radius:
                            if self.player.take_damage(bullet.get_damage()):
                                self.pvp_winner = "Player 2"
                                self.state = "gameover"
                                self.stop_music()
                            hit_something = True
                    elif bullet_owner != "player2" and self.player2 and self.player2.health > 0:
                        # Player 1's bullet can hit Player 2
                        dist = math.sqrt((bullet.x - self.player2.x)**2 + (bullet.y - self.player2.y)**2)
                        if dist < self.player2.radius + bullet.radius:
                            if self.player2.take_damage(bullet.get_damage()):
                                self.pvp_winner = "Player 1"
                                self.state = "gameover"
                                self.stop_music()
                            hit_something = True

                # Check robots (co-op and solo modes)
                if not hit_something:
                    for robot in self.robots[:]:
                        # Check for sniper headshot first
                        is_headshot = False
                        if bullet.weapon_type == "Sniper" and robot.check_headshot(bullet.x, bullet.y):
                            is_headshot = True

                        # Check body hit
                        dist = math.sqrt((bullet.x - robot.x)**2 + (bullet.y - robot.y)**2)
                        body_hit = dist < robot.radius + bullet.radius

                        if is_headshot or body_hit:
                            # Sniper: 150 damage for headshot, 50 for body
                            if bullet.weapon_type == "Sniper":
                                damage = 150 if is_headshot else 50
                            else:
                                damage = bullet.get_damage()

                            # Special effects for certain weapon types
                            if bullet.weapon_type == "Freeze":
                                robot.freeze_timer = 120  # Slow for 2 seconds
                            elif bullet.weapon_type == "Electric":
                                # Chain lightning - damage nearby robots too
                                for other_robot in self.robots:
                                    if other_robot != robot:
                                        other_dist = math.sqrt((robot.x - other_robot.x)**2 + (robot.y - other_robot.y)**2)
                                        if other_dist < 150:  # Chain range
                                            other_robot.take_damage(damage // 2)
                                            other_robot.hit_flash = 10

                            if robot.take_damage(damage):
                                self.robots.remove(robot)
                                self.kills += 1
                                if self.game_mode != "pvp":
                                    # Bonus score for headshot
                                    bonus = 2 if is_headshot else 1
                                    self.score += DIFFICULTY[self.difficulty]["points"] * bonus
                                    self.player.add_coin(DIFFICULTY[self.difficulty]["coins"])  # Add coins for kill
                                    # Check if player has 10 coins for shotgun or 50 for RPG
                                    if self.player.coins >= 10 and not self.player.has_shotgun and not self.shop_prompted:
                                        self.state = "shop"
                                    elif self.player.coins >= 50 and not self.player.has_rpg and self.player.has_shotgun and not self.shop_prompted:
                                        self.state = "shop"
                            hit_something = True
                            break

                # Check boss
                if not hit_something and self.boss:
                    # Check for sniper headshot first
                    is_headshot = False
                    if bullet.weapon_type == "Sniper" and self.boss.check_headshot(bullet.x, bullet.y):
                        is_headshot = True

                    dist = math.sqrt((bullet.x - self.boss.x)**2 + (bullet.y - self.boss.y)**2)
                    body_hit = dist < self.boss.radius + bullet.radius

                    if is_headshot or body_hit:
                        # Sniper: 150 damage for headshot, 50 for body
                        if bullet.weapon_type == "Sniper":
                            damage = 150 if is_headshot else 50
                        else:
                            damage = bullet.get_damage()

                        if self.boss.take_damage(damage):
                            # Boss defeated!
                            self.boss = None
                            self.kills += 1
                            self.score += 5000  # Big bonus for boss
                            self.player.add_coin(100)  # Big coin reward
                        hit_something = True

                if hit_something and bullet in self.bullets:
                    self.bullets.remove(bullet)

            # Robot bullets hit players
            else:
                hit_player = False
                # Check Player 1
                dist = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
                if dist < self.player.radius + bullet.radius:
                    if self.player.take_damage(bullet.damage):
                        if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                            pass  # Player 2 still alive, continue
                        else:
                            self.state = "gameover"
                            self.stop_music()
                    hit_player = True

                # Check Player 2 (in co-op)
                if not hit_player and (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                    dist = math.sqrt((bullet.x - self.player2.x)**2 + (bullet.y - self.player2.y)**2)
                    if dist < self.player2.radius + bullet.radius:
                        if self.player2.take_damage(bullet.damage):
                            if self.player.health > 0:
                                pass  # Player 1 still alive, continue
                            else:
                                self.state = "gameover"
                                self.stop_music()
                        hit_player = True

                if hit_player and bullet in self.bullets:
                    self.bullets.remove(bullet)

        # Update grenades
        for grenade in self.grenades[:]:
            grenade.update()

            if grenade.should_explode():
                # Create explosion
                explosion = Explosion(grenade.x, grenade.y, grenade.explosion_radius)
                self.explosions.append(explosion)

                # Damage robots in explosion radius
                for robot in self.robots[:]:
                    dist = math.sqrt((grenade.x - robot.x)**2 + (grenade.y - robot.y)**2)
                    if dist < grenade.explosion_radius:
                        # Damage falls off with distance
                        damage_mult = 1 - (dist / grenade.explosion_radius) * 0.5
                        damage = int(grenade.damage * damage_mult)
                        if robot.take_damage(damage):
                            self.robots.remove(robot)
                            self.kills += 1
                            self.score += DIFFICULTY[self.difficulty]["points"]
                            self.player.add_coin(DIFFICULTY[self.difficulty]["coins"])
                            if self.player.coins >= 10 and not self.player.has_shotgun and not self.shop_prompted:
                                self.state = "shop"
                            elif self.player.coins >= 50 and not self.player.has_rpg and self.player.has_shotgun and not self.shop_prompted:
                                self.state = "shop"

                # Damage player 1 if in explosion radius
                dist = math.sqrt((grenade.x - self.player.x)**2 + (grenade.y - self.player.y)**2)
                if dist < grenade.explosion_radius:
                    damage_mult = 1 - (dist / grenade.explosion_radius) * 0.5
                    damage = int(grenade.damage * damage_mult * 0.5)  # Player takes less self-damage
                    if self.player.take_damage(damage):
                        # In co-op, only game over if both players dead
                        if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                            pass  # Player 2 still alive, continue
                        else:
                            self.state = "gameover"
                            self.stop_music()

                # Damage player 2 if in explosion radius (co-op)
                if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                    dist2 = math.sqrt((grenade.x - self.player2.x)**2 + (grenade.y - self.player2.y)**2)
                    if dist2 < grenade.explosion_radius:
                        damage_mult = 1 - (dist2 / grenade.explosion_radius) * 0.5
                        damage = int(grenade.damage * damage_mult * 0.5)
                        if self.player2.take_damage(damage):
                            if self.player.health > 0:
                                pass  # Player 1 still alive, continue
                            else:
                                self.state = "gameover"
                                self.stop_music()

                grenade.exploded = True
                self.grenades.remove(grenade)

        # Update explosions
        for explosion in self.explosions[:]:
            explosion.update()
            if explosion.is_done():
                self.explosions.remove(explosion)

        # Update smoke grenades
        for smoke in self.smoke_grenades[:]:
            smoke.update()
            if smoke.should_pop():
                # Create smoke cloud
                cloud = SmokeCloud(smoke.x, smoke.y)
                self.smoke_clouds.append(cloud)
                smoke.popped = True
                self.smoke_grenades.remove(smoke)

        # Update smoke clouds
        for cloud in self.smoke_clouds[:]:
            cloud.update()
            if cloud.is_done():
                self.smoke_clouds.remove(cloud)

        # Update robots
        for robot in self.robots:
            # In co-op, robots target the nearest player
            target_x, target_y = self.player.x, self.player.y
            if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                dist_to_p1 = math.sqrt((robot.x - self.player.x)**2 + (robot.y - self.player.y)**2)
                dist_to_p2 = math.sqrt((robot.x - self.player2.x)**2 + (robot.y - self.player2.y)**2)
                if self.player.health <= 0 or (self.player2.health > 0 and dist_to_p2 < dist_to_p1):
                    target_x, target_y = self.player2.x, self.player2.y

            robot.update(target_x, target_y, self.obstacles)

            # Robot uses knife when close, otherwise shoots
            # Check player 1
            if robot.can_knife(self.player.x, self.player.y):
                damage = robot.knife_attack()
                if self.player.take_damage(damage):
                    # In co-op, only game over if both players dead
                    if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                        pass  # Player 2 still alive, continue
                    else:
                        self.state = "gameover"
                        self.stop_music()
            # Check player 2 in co-op
            elif (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                if robot.can_knife(self.player2.x, self.player2.y):
                    damage = robot.knife_attack()
                    if self.player2.take_damage(damage):
                        if self.player.health > 0:
                            pass  # Player 1 still alive, continue
                        else:
                            self.state = "gameover"
                            self.stop_music()
            elif robot.can_shoot():
                # Check if smoke is blocking line of sight - simplified for performance
                can_see_target = True
                for cloud in self.smoke_clouds:
                    # Just check if target or robot is in smoke (skip expensive line check)
                    if cloud.point_in_smoke(target_x, target_y) or cloud.point_in_smoke(robot.x, robot.y):
                        can_see_target = False
                        break

                if can_see_target:
                    # Shoot at nearest player
                    result = robot.shoot(target_x, target_y)
                    # Handle single bullet or list of bullets (dual pistol bots)
                    if isinstance(result, list):
                        for bullet in result:
                            bullet.damage = DIFFICULTY[self.difficulty]["damage"]
                        self.bullets.extend(result)
                    else:
                        result.damage = DIFFICULTY[self.difficulty]["damage"]
                        self.bullets.append(result)

        # Update boss (impossible mode)
        if self.boss:
            # In co-op, boss targets nearest player
            boss_target_x, boss_target_y = self.player.x, self.player.y
            if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                dist_to_p1 = math.sqrt((self.boss.x - self.player.x)**2 + (self.boss.y - self.player.y)**2)
                dist_to_p2 = math.sqrt((self.boss.x - self.player2.x)**2 + (self.boss.y - self.player2.y)**2)
                if self.player.health <= 0 or (self.player2.health > 0 and dist_to_p2 < dist_to_p1):
                    boss_target_x, boss_target_y = self.player2.x, self.player2.y

            self.boss.update(boss_target_x, boss_target_y, self.obstacles)

            # Boss shoots multiple bullets at nearest player
            if self.boss.can_shoot():
                bullets = self.boss.shoot(boss_target_x, boss_target_y)
                self.bullets.extend(bullets)

            # Check boss collision with player 1 (charge attack damage)
            dist_to_boss = math.sqrt((self.boss.x - self.player.x)**2 + (self.boss.y - self.player.y)**2)
            if dist_to_boss < self.boss.radius + self.player.radius:
                if self.player.take_damage(20):
                    # In co-op, only game over if both players dead
                    if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                        pass  # Player 2 still alive, continue
                    else:
                        self.state = "gameover"
                        self.stop_music()

            # Check boss collision with player 2 in co-op
            if (self.game_mode == "coop" or self.game_mode == "online_coop") and self.player2 and self.player2.health > 0:
                dist_to_boss2 = math.sqrt((self.boss.x - self.player2.x)**2 + (self.boss.y - self.player2.y)**2)
                if dist_to_boss2 < self.boss.radius + self.player2.radius:
                    if self.player2.take_damage(20):
                        if self.player.health > 0:
                            pass  # Player 1 still alive, continue
                        else:
                            self.state = "gameover"
                            self.stop_music()

        # Check win conditions
        # Skip robot-based win condition in PvP (no robots in PvP)
        if self.game_mode in ["pvp", "online_pvp"]:
            pass  # PvP win is determined by player death, not robot count
        elif self.difficulty == "impossible":
            # Wave-based win condition
            if len(self.robots) == 0 and self.boss is None:
                if self.current_wave < self.max_waves:
                    # Start next wave
                    self.wave_complete_timer += 1
                    if self.wave_complete_timer > 120:  # 2 second delay
                        self.wave_complete_timer = 0
                        self.next_wave()
                else:
                    # All waves complete and boss dead
                    self.state = "gameover"
                    self.stop_music()
        else:
            # Normal win condition
            if len(self.robots) == 0:
                self.state = "gameover"
                self.stop_music()

    def draw_background(self):
        # Fill with floor color
        self.screen.fill(FLOOR_COLOR)

        # Draw grid
        grid_size = 100
        for x in range(0, MAP_WIDTH, grid_size):
            sx, _ = self.camera.apply(x, 0)
            if 0 <= sx <= SCREEN_WIDTH:
                pygame.draw.line(self.screen, (60, 65, 70), (sx, 0), (sx, SCREEN_HEIGHT))

        for y in range(0, MAP_HEIGHT, grid_size):
            _, sy = self.camera.apply(0, y)
            if 0 <= sy <= SCREEN_HEIGHT:
                pygame.draw.line(self.screen, (60, 65, 70), (0, sy), (SCREEN_WIDTH, sy))

    def draw_world_to_surface(self, surface, camera):
        """Draw the game world to a surface using the specified camera"""
        width = surface.get_width()
        height = surface.get_height()

        # Fill with floor color
        surface.fill(FLOOR_COLOR)

        # Draw grid
        grid_size = 100
        for x in range(0, MAP_WIDTH, grid_size):
            sx, _ = camera.apply(x, 0)
            if 0 <= sx <= width:
                pygame.draw.line(surface, (60, 65, 70), (sx, 0), (sx, height))

        for y in range(0, MAP_HEIGHT, grid_size):
            _, sy = camera.apply(0, y)
            if 0 <= sy <= height:
                pygame.draw.line(surface, (60, 65, 70), (0, sy), (width, sy))

        # Draw obstacles
        for obs in self.obstacles:
            obs.draw(surface, camera)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(surface, camera)

        # Draw grenades
        for grenade in self.grenades:
            grenade.draw(surface, camera)

        # Draw smoke grenades
        for smoke in self.smoke_grenades:
            smoke.draw(surface, camera)

        # Draw smoke clouds (behind explosions but in front of grenades)
        for cloud in self.smoke_clouds:
            cloud.draw(surface, camera)

        # Draw explosions
        for explosion in self.explosions:
            explosion.draw(surface, camera)

        # Draw robots - set sniper target visibility based on player's current weapon
        player1_has_sniper = self.player.weapon["name"] == "Sniper"
        player2_has_sniper = self.player2 and self.player2.weapon["name"] == "Sniper"
        has_sniper = player1_has_sniper or player2_has_sniper
        for robot in self.robots:
            robot.show_sniper_target = has_sniper
            robot.draw(surface, camera)

        # Draw boss
        if self.boss:
            self.boss.show_sniper_target = has_sniper
            self.boss.draw(surface, camera)

        # Draw shell casings
        for casing in self.shell_casings:
            casing.draw(surface, camera)

        # Draw players
        self.player.draw(surface, camera)
        if self.player2 and self.player2.health > 0:
            self.player2.draw(surface, camera)
        # Draw enemy team players (for 2v2 and 2v1 modes)
        if self.remote_player3 and self.remote_player3.health > 0:
            self.remote_player3.draw(surface, camera)
        if self.remote_player4 and self.remote_player4.health > 0:
            self.remote_player4.draw(surface, camera)

        # Draw player names in online multiplayer
        if self.game_mode in ["online_coop", "online_pvp", "online_2v2", "online_2v1"]:
            self.draw_player_names(surface, camera)

        # Draw muzzle flashes
        for flash in self.muzzle_flashes:
            flash.draw(surface, camera)

        # Draw healing effects
        for effect in self.healing_effects:
            effect.draw(surface, camera)

    def draw_player_names(self, surface, camera):
        """Draw player names above players in online multiplayer"""
        # Use cached font for performance
        if not hasattr(self, '_name_font'):
            self._name_font = pygame.font.Font(None, 20)
            # Pre-cache common labels
            self._name_cache = {}
        name_font = self._name_font

        def draw_name_label(player, text, color):
            if player and player.health > 0:
                sx, sy = camera.apply(player.x, player.y)
                # Use cached surface for common labels
                cache_key = (text, color)
                if cache_key not in self._name_cache:
                    self._name_cache[cache_key] = name_font.render(text, True, color)
                name_surface = self._name_cache[cache_key]
                name_x = sx - name_surface.get_width() // 2
                name_y = sy - player.radius - 30
                bg_rect = pygame.Rect(name_x - 4, name_y - 2, name_surface.get_width() + 8, name_surface.get_height() + 4)
                pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=4)
                surface.blit(name_surface, (name_x, name_y))

        # Draw "YOU" above local player
        draw_name_label(self.player, "YOU", (100, 200, 255))

        # For team modes (2v2, 2v1), show teammate and enemies
        if self.game_mode in ["online_2v2", "online_2v1"]:
            # Local teammate (player2)
            draw_name_label(self.player2, "ALLY", (100, 255, 150))
            # Enemy players
            draw_name_label(self.remote_player3, "ENEMY", (255, 100, 100))
            draw_name_label(self.remote_player4, "ENEMY", (255, 100, 100))
        else:
            # Regular online modes - show remote player's username
            display_name = self.remote_player_name if self.remote_player_name else "Player 2"
            draw_name_label(self.player2, display_name, (255, 150, 100))

    def draw_split_screen_hud(self, surface, player, is_player1, width):
        """Draw HUD for one player in split-screen mode"""
        bar_width = min(150, width - 20)
        bar_height = 20
        bar_x = 10
        bar_y = 35

        # Big player label at top center of each half
        if is_player1:
            title = self._cached_text("split_p1_title", "PLAYER 1", self.font, LIGHT_BLUE)
        else:
            title = self._cached_text("split_p2_title", "PLAYER 2", self.font, (100, 150, 255))
        surface.blit(title, (width // 2 - title.get_width() // 2, 5))

        # Small P1/P2 label next to health bar
        if is_player1:
            label = self._cached_text("split_p1_label", "P1", self.small_font, LIGHT_BLUE)
        else:
            label = self._cached_text("split_p2_label", "P2", self.small_font, (100, 150, 255))
        surface.blit(label, (bar_x, bar_y - 5))

        # Health bar
        pygame.draw.rect(surface, DARK_GRAY, (bar_x + 30, bar_y, bar_width, bar_height))
        health_width = int((max(0, player.health) / player.max_health) * bar_width)
        health_color = GREEN if player.health > 50 else YELLOW if player.health > 25 else RED
        pygame.draw.rect(surface, health_color, (bar_x + 30, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x + 30, bar_y, bar_width, bar_height), 2)

        cache_key = "split_p1_hp" if is_player1 else "split_p2_hp"
        hp_text = self._cached_text(cache_key, f"{int(max(0, player.health))}", self.small_font, WHITE)
        surface.blit(hp_text, (bar_x + 35, bar_y + 2))

        # Weapon info
        weapon_name = player.weapon["name"]
        cache_key = "split_p1_weapon" if is_player1 else "split_p2_weapon"
        weapon_text = self._cached_text(cache_key, f"{weapon_name}: {player.ammo}", self.small_font, player.weapon["color"])
        surface.blit(weapon_text, (bar_x, bar_y + 28))

    def draw_minimap(self):
        # Minimap in corner
        map_size = 200
        map_x = SCREEN_WIDTH - map_size - 20
        map_y = 20

        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (map_x, map_y, map_size, map_size))
        pygame.draw.rect(self.screen, WHITE, (map_x, map_y, map_size, map_size), 2)

        # Scale factor
        scale = map_size / MAP_WIDTH

        # Draw obstacles
        for obs in self.obstacles:
            ox = map_x + int(obs.x * scale)
            oy = map_y + int(obs.y * scale)
            ow = max(2, int(obs.width * scale))
            oh = max(2, int(obs.height * scale))
            pygame.draw.rect(self.screen, BROWN, (ox, oy, ow, oh))

        # Draw robots with different colors by type
        for robot in self.robots:
            rx = map_x + int(robot.x * scale)
            ry = map_y + int(robot.y * scale)
            # Color by bot type
            if robot.bot_type == "knife":
                robot_color = WHITE
            elif robot.bot_type == "throwing_knife":
                robot_color = GRAY  # Gray for throwing knife bots
            elif robot.bot_type == "dual_pistol":
                robot_color = (255, 215, 0)  # Gold for dual pistol bots
            else:  # gun bots
                robot_color = RED
            pygame.draw.circle(self.screen, robot_color, (rx, ry), 3)

        # Draw player
        px = map_x + int(self.player.x * scale)
        py = map_y + int(self.player.y * scale)
        pygame.draw.circle(self.screen, LIGHT_BLUE, (px, py), 4)

        # Draw boss on minimap (purple, bigger)
        if self.boss:
            bx = map_x + int(self.boss.x * scale)
            by = map_y + int(self.boss.y * scale)
            pygame.draw.circle(self.screen, (150, 0, 150), (bx, by), 6)

        # Draw camera view box
        cx = map_x + int(self.camera.x * scale)
        cy = map_y + int(self.camera.y * scale)
        cw = int(SCREEN_WIDTH * scale)
        ch = int(SCREEN_HEIGHT * scale)
        pygame.draw.rect(self.screen, WHITE, (cx, cy, cw, ch), 1)

    def _cached_text(self, cache_key, text, font, color):
        """Get cached text surface, only re-render if text/color changed"""
        key = (text, color)
        if cache_key not in self._hud_cache or self._hud_cache_keys.get(cache_key) != key:
            self._hud_cache[cache_key] = font.render(text, True, color)
            self._hud_cache_keys[cache_key] = key
        return self._hud_cache[cache_key]

    def draw_hud(self):
        # Player 1 Health bar
        bar_width = 250
        bar_height = 25
        bar_x = 20
        bar_y = 20

        # P1 label in multiplayer
        if self.player2:
            p1_label = self._cached_text("p1_label", "P1", self.small_font, LIGHT_BLUE)
            self.screen.blit(p1_label, (bar_x, bar_y - 18))

        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        health_width = int((max(0, self.player.health) / self.player.max_health) * bar_width)
        health_color = GREEN if self.player.health > 50 else YELLOW if self.player.health > 25 else RED
        pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        hp_text = self._cached_text("hp", f"HP: {int(max(0, self.player.health))}", self.small_font, WHITE)
        self.screen.blit(hp_text, (bar_x + 5, bar_y + 3))

        # Player 2 Health bar (in multiplayer modes)
        if self.player2:
            p2_bar_x = SCREEN_WIDTH - bar_width - 20
            p2_bar_y = 20

            p2_label = self._cached_text("p2_label", "P2", self.small_font, (255, 150, 150))
            self.screen.blit(p2_label, (p2_bar_x, p2_bar_y - 18))

            pygame.draw.rect(self.screen, DARK_GRAY, (p2_bar_x, p2_bar_y, bar_width, bar_height))
            p2_health_width = int((max(0, self.player2.health) / self.player2.max_health) * bar_width)
            p2_health_color = GREEN if self.player2.health > 50 else YELLOW if self.player2.health > 25 else RED
            pygame.draw.rect(self.screen, p2_health_color, (p2_bar_x, p2_bar_y, p2_health_width, bar_height))
            pygame.draw.rect(self.screen, (255, 200, 200), (p2_bar_x, p2_bar_y, bar_width, bar_height), 2)

            p2_hp_text = self._cached_text("p2_hp", f"HP: {int(max(0, self.player2.health))}", self.small_font, WHITE)
            self.screen.blit(p2_hp_text, (p2_bar_x + 5, p2_bar_y + 3))

            # P2 weapon info
            p2_weapon_text = self._cached_text("p2_weapon", f"{self.player2.weapon['name']}: {self.player2.ammo}", self.small_font, (255, 150, 150))
            self.screen.blit(p2_weapon_text, (p2_bar_x, p2_bar_y + 30))

        # Weapon and Ammo with reloads on the right
        weapon_name = self.player.weapon["name"]
        weapon_color = self.player.weapon["color"]
        reloads = self.player.weapon.get("reloads", 0)

        # Show reloads (infinite for knife, none for grenade)
        if self.player.weapon.get("melee", False):
            reload_str = "INF"
        elif self.player.weapon.get("no_reload", False):
            reload_str = "N/A"
        else:
            reload_str = str(reloads)

        weapon_text = self._cached_text("weapon", f"{weapon_name}: {self.player.ammo}/{self.player.max_ammo}", self.font, weapon_color)
        self.screen.blit(weapon_text, (20, 55))

        # Reloads display on the right of ammo
        reload_color = GREEN if reloads > 2 or self.player.weapon.get("melee", False) else YELLOW if reloads > 0 else RED
        reload_text = self._cached_text("reloads", f"[{reload_str}]", self.small_font, reload_color)
        self.screen.blit(reload_text, (20 + weapon_text.get_width() + 10, 60))

        # Switch weapon hint
        switch_text = self._cached_text("switch", "[Q/E] Switch", self.small_font, GRAY)
        self.screen.blit(switch_text, (20, 95))

        # Coins display (top right corner)
        coin_color = YELLOW if self.player.coins < 10 else GREEN
        coin_text = self._cached_text("coins", f"Coins: {self.player.coins}", self.font, coin_color)
        self.screen.blit(coin_text, (SCREEN_WIDTH - 220 - coin_text.get_width()//2, 230))

        # Shotgun status
        shotgun_txt = "Shotgun OK" if self.player.has_shotgun else "Shotgun: 10"
        shotgun_color = GREEN if self.player.has_shotgun else GRAY
        shotgun_text = self._cached_text("shotgun", shotgun_txt, self.small_font, shotgun_color)
        self.screen.blit(shotgun_text, (SCREEN_WIDTH - 220 - shotgun_text.get_width()//2, 265))

        # RPG status
        rpg_txt = "RPG OK" if self.player.has_rpg else "RPG: 50"
        rpg_color = GREEN if self.player.has_rpg else GRAY
        rpg_text = self._cached_text("rpg", rpg_txt, self.small_font, rpg_color)
        self.screen.blit(rpg_text, (SCREEN_WIDTH - 220 - rpg_text.get_width()//2, 290))

        # Medkit charges
        medkit_color = GREEN if self.player.medkit_charges > 0 else GRAY
        medkit_text = self._cached_text("medkit", f"Med: {self.player.medkit_charges} [H]", self.small_font, medkit_color)
        self.screen.blit(medkit_text, (SCREEN_WIDTH - 220 - medkit_text.get_width()//2, 315))

        # Score and kills
        score_text = self._cached_text("score", f"Score: {self.score} | K: {self.kills}", self.small_font, YELLOW)
        self.screen.blit(score_text, (20, SCREEN_HEIGHT - 40))

        # Robots remaining
        robots_text = self._cached_text("robots", f"Bots: {len(self.robots)}", self.small_font, ORANGE)
        self.screen.blit(robots_text, (20, SCREEN_HEIGHT - 70))

        # Wave info for impossible mode
        if self.difficulty == "impossible":
            wave_text = self._cached_text("wave", f"Wave {self.current_wave}/{self.max_waves}", self.font, (150, 0, 150))
            self.screen.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 10))

            # Wave complete message
            if len(self.robots) == 0 and self.boss is None and self.current_wave < self.max_waves:
                next_wave_text = self._cached_text("wave_complete", "Wave Complete!", self.font, GREEN)
                self.screen.blit(next_wave_text, (SCREEN_WIDTH // 2 - next_wave_text.get_width() // 2, 130))

        # Show game mode (simplified)
        if self.game_mode in ["online_coop", "online_pvp", "coop", "pvp"]:
            mode_map = {"online_coop": ("ONLINE CO-OP", (100, 200, 255)),
                       "online_pvp": ("ONLINE PVP", (255, 100, 100)),
                       "coop": ("LOCAL CO-OP", (100, 255, 100)),
                       "pvp": ("LOCAL PVP", (255, 150, 100))}
            mode_txt, mode_color = mode_map[self.game_mode]
            mode_text = self._cached_text("mode", mode_txt, self.small_font, mode_color)
            self.screen.blit(mode_text, (SCREEN_WIDTH // 2 - mode_text.get_width() // 2, 50))

        # Reload hint
        if self.player.ammo == 0:
            reload_hint = self._cached_text("reload_hint", "Press R to Reload!", self.font, RED)
            self.screen.blit(reload_hint, (SCREEN_WIDTH // 2 - reload_hint.get_width() // 2, 100))

        # Save message
        if self.show_save_message > 0:
            save_text = self._cached_text("saved", "Game Saved!", self.font, GREEN)
            self.screen.blit(save_text, (SCREEN_WIDTH // 2 - save_text.get_width() // 2, 140))
            self.show_save_message -= 1

        # Shop button on middle left side with shopping cart icon
        shop_btn_width = 60
        shop_btn_height = 70
        shop_btn_x = 20
        shop_btn_y = SCREEN_HEIGHT // 2 - shop_btn_height // 2
        self.shop_btn_rect = pygame.Rect(shop_btn_x, shop_btn_y, shop_btn_width, shop_btn_height)

        pygame.draw.rect(self.screen, DARK_GRAY, self.shop_btn_rect)
        pygame.draw.rect(self.screen, YELLOW, self.shop_btn_rect, 3)

        # "SHOP" text above cart
        shop_label = self._cached_text("shop_label", "SHOP", self.small_font, YELLOW)
        self.screen.blit(shop_label, (shop_btn_x + shop_btn_width // 2 - shop_label.get_width() // 2, shop_btn_y + 5))

        # Draw shopping cart icon
        cart_x = shop_btn_x + shop_btn_width // 2
        cart_y = shop_btn_y + 45

        # Cart body (trapezoid shape)
        cart_points = [
            (cart_x - 15, cart_y - 12),  # Top left
            (cart_x + 15, cart_y - 12),  # Top right
            (cart_x + 12, cart_y + 5),   # Bottom right
            (cart_x - 12, cart_y + 5),   # Bottom left
        ]
        pygame.draw.polygon(self.screen, YELLOW, cart_points, 2)

        # Cart handle
        pygame.draw.line(self.screen, YELLOW, (cart_x - 15, cart_y - 12), (cart_x - 20, cart_y - 20), 2)

        # Cart wheels
        pygame.draw.circle(self.screen, YELLOW, (cart_x - 8, cart_y + 10), 4)
        pygame.draw.circle(self.screen, YELLOW, (cart_x + 8, cart_y + 10), 4)

    def draw_login_screen(self):
        """Draw login/register screen"""
        # Enable text input for mobile keyboard
        pygame.key.start_text_input()
        self.screen.fill(DARK_GRAY)

        # Title
        title = self.big_font.render("ARENA SHOOTER 2D", True, RED)
        subtitle = self.font.render("ROBOT BATTLE", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 150))

        # Login box
        box_width = 450
        box_height = 340
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = 200

        pygame.draw.rect(self.screen, (40, 40, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, LIGHT_BLUE, (box_x, box_y, box_width, box_height), 3)

        # Mode title
        mode_text = "LOGIN" if self.login_mode == "login" else "REGISTER"
        mode_render = self.font.render(mode_text, True, LIGHT_BLUE)
        self.screen.blit(mode_render, (SCREEN_WIDTH // 2 - mode_render.get_width() // 2, box_y + 15))

        # Username field
        username_y = box_y + 70
        username_label = self.small_font.render("Username:", True, WHITE)
        self.screen.blit(username_label, (box_x + 25, username_y))

        username_box_color = GREEN if self.active_input == "username" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 40), (box_x + 25, username_y + 25, box_width - 50, 35))
        pygame.draw.rect(self.screen, username_box_color, (box_x + 25, username_y + 25, box_width - 50, 35), 2)

        username_text = self.font.render(self.username_input, True, WHITE)
        self.screen.blit(username_text, (box_x + 35, username_y + 28))

        # Cursor for username
        if self.active_input == "username":
            cursor_x = box_x + 35 + username_text.get_width()
            pygame.draw.line(self.screen, WHITE, (cursor_x, username_y + 28), (cursor_x, username_y + 52), 2)

        # Passcode field
        passcode_y = box_y + 150
        passcode_label = self.small_font.render("Passcode:", True, WHITE)
        self.screen.blit(passcode_label, (box_x + 25, passcode_y))

        passcode_box_color = GREEN if self.active_input == "passcode" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 40), (box_x + 25, passcode_y + 25, box_width - 50, 35))
        pygame.draw.rect(self.screen, passcode_box_color, (box_x + 25, passcode_y + 25, box_width - 50, 35), 2)

        # Show passcode as asterisks
        passcode_display = "*" * len(self.passcode_input)
        passcode_text = self.font.render(passcode_display, True, WHITE)
        self.screen.blit(passcode_text, (box_x + 35, passcode_y + 28))

        # Cursor for passcode
        if self.active_input == "passcode":
            cursor_x = box_x + 35 + passcode_text.get_width()
            pygame.draw.line(self.screen, WHITE, (cursor_x, passcode_y + 28), (cursor_x, passcode_y + 52), 2)

        # Message (success/error)
        if self.login_message:
            msg_color = GREEN if "success" in self.login_message.lower() or "created" in self.login_message.lower() else RED
            msg_render = self.small_font.render(self.login_message, True, msg_color)
            self.screen.blit(msg_render, (SCREEN_WIDTH // 2 - msg_render.get_width() // 2, box_y + 235))

        # Touch-friendly buttons
        btn_y = box_y + 230
        btn_height = 40
        btn_margin = 10

        # Submit button
        submit_btn_x = box_x + 25
        submit_btn_width = (box_width - 60) // 2
        pygame.draw.rect(self.screen, (50, 150, 50), (submit_btn_x, btn_y, submit_btn_width, btn_height))
        pygame.draw.rect(self.screen, GREEN, (submit_btn_x, btn_y, submit_btn_width, btn_height), 2)
        submit_text = self.font.render("SUBMIT", True, WHITE)
        self.screen.blit(submit_text, (submit_btn_x + submit_btn_width // 2 - submit_text.get_width() // 2, btn_y + 8))
        self.login_submit_btn = pygame.Rect(submit_btn_x, btn_y, submit_btn_width, btn_height)

        # Register/Login toggle button
        toggle_btn_x = box_x + 25 + submit_btn_width + btn_margin
        toggle_text_str = "REGISTER" if self.login_mode == "login" else "LOGIN"
        pygame.draw.rect(self.screen, (100, 100, 150), (toggle_btn_x, btn_y, submit_btn_width, btn_height))
        pygame.draw.rect(self.screen, LIGHT_BLUE, (toggle_btn_x, btn_y, submit_btn_width, btn_height), 2)
        toggle_text = self.font.render(toggle_text_str, True, WHITE)
        self.screen.blit(toggle_text, (toggle_btn_x + submit_btn_width // 2 - toggle_text.get_width() // 2, btn_y + 8))
        self.login_toggle_btn = pygame.Rect(toggle_btn_x, btn_y, submit_btn_width, btn_height)

        # Guest button (full width below)
        guest_btn_y = btn_y + btn_height + btn_margin
        guest_btn_width = box_width - 50
        pygame.draw.rect(self.screen, (150, 100, 50), (box_x + 25, guest_btn_y, guest_btn_width, btn_height))
        pygame.draw.rect(self.screen, ORANGE, (box_x + 25, guest_btn_y, guest_btn_width, btn_height), 2)
        guest_text = self.font.render("PLAY AS GUEST", True, WHITE)
        self.screen.blit(guest_text, (SCREEN_WIDTH // 2 - guest_text.get_width() // 2, guest_btn_y + 8))
        self.login_guest_btn = pygame.Rect(box_x + 25, guest_btn_y, guest_btn_width, btn_height)

        # Store input field rects for touch
        self.username_field_rect = pygame.Rect(box_x + 25, username_y + 25, box_width - 50, 35)
        self.passcode_field_rect = pygame.Rect(box_x + 25, passcode_y + 25, box_width - 50, 35)

        # Message (success/error)
        if self.login_message:
            msg_color = GREEN if "success" in self.login_message.lower() or "created" in self.login_message.lower() else RED
            msg_render = self.small_font.render(self.login_message, True, msg_color)
            self.screen.blit(msg_render, (SCREEN_WIDTH // 2 - msg_render.get_width() // 2, guest_btn_y + btn_height + 10))

        # Show current user if logged in
        if current_user:
            user_text = self.small_font.render(f"Logged in as: {current_user}", True, GREEN)
            self.screen.blit(user_text, (SCREEN_WIDTH // 2 - user_text.get_width() // 2, box_y + box_height + 30))

    def draw_menu(self):
        self.screen.fill((25, 25, 35))  # Darker background

        # Title area with decorative line
        title = self.big_font.render("ARENA SHOOTER 2D", True, RED)
        subtitle = self.font.render("ROBOT BATTLE", True, (200, 200, 200))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 85))

        # Decorative line under title
        pygame.draw.line(self.screen, (60, 60, 80), (SCREEN_WIDTH // 2 - 200, 115), (SCREEN_WIDTH // 2 + 200, 115), 2)

        # Version in corner
        version = self.small_font.render("v3.0", True, (100, 100, 100))
        self.screen.blit(version, (SCREEN_WIDTH - version.get_width() - 10, 10))

        # Two column layout
        left_col = SCREEN_WIDTH // 2 - 160
        right_col = SCREEN_WIDTH // 2 + 10
        btn_w = 150
        btn_h = 32

        def draw_btn(text, x, y, color, bg_color, btn_name, width=btn_w):
            pygame.draw.rect(self.screen, bg_color, (x, y, width, btn_h), border_radius=4)
            pygame.draw.rect(self.screen, color, (x, y, width, btn_h), 2, border_radius=4)
            txt = self.small_font.render(text, True, color)
            self.screen.blit(txt, (x + width // 2 - txt.get_width() // 2, y + 6))
            self.menu_buttons[btn_name] = pygame.Rect(x, y, width, btn_h)

        def draw_section(text, x, y, color, width=btn_w):
            header = self.small_font.render(text, True, color)
            self.screen.blit(header, (x + width // 2 - header.get_width() // 2, y))
            pygame.draw.line(self.screen, (50, 50, 60), (x, y + 22), (x + width, y + 22), 1)

        # ===== SOLO MODE (Left Column) =====
        draw_section("SOLO", left_col, 135, LIGHT_BLUE)
        draw_btn("Easy", left_col, 160, GREEN, (20, 50, 20), "easy")
        draw_btn("Medium", left_col, 198, YELLOW, (50, 50, 20), "medium")
        draw_btn("Hard", left_col, 236, ORANGE, (50, 35, 10), "hard")
        draw_btn("Impossible", left_col, 274, RED, (50, 20, 20), "impossible")

        # ===== ONLINE MODE (Right Column) =====
        draw_section("ONLINE", right_col, 135, (0, 200, 255))
        draw_btn("Co-op", right_col, 160, (0, 255, 200), (0, 40, 35), "online_coop")
        draw_btn("PvP", right_col, 198, (255, 100, 150), (40, 20, 30), "online_pvp")
        draw_btn("2v2", right_col, 236, (255, 200, 50), (50, 40, 10), "online_2v2")
        draw_btn("2v1", right_col, 274, (200, 100, 255), (40, 20, 50), "online_2v1")

        # ===== LOCAL 2-PLAYER =====
        draw_section("LOCAL 2P", left_col, 330, ORANGE, right_col + btn_w - left_col)
        draw_btn("PvP 1v1", left_col, 355, (255, 100, 100), (50, 20, 20), "local_pvp")
        draw_btn("Co-op Easy", right_col, 355, GREEN, (20, 50, 20), "coop_easy")
        draw_btn("Co-op Med", left_col, 393, YELLOW, (50, 50, 20), "coop_med")
        draw_btn("Co-op Hard", right_col, 393, ORANGE, (50, 35, 10), "coop_hard")
        draw_btn("Co-op Imp", left_col, 431, RED, (50, 20, 20), "coop_imp")

        # ===== MAP SELECTION =====
        draw_section("MAP", left_col, 475, (100, 180, 255), right_col + btn_w - left_col)
        map_y = 500
        # Left arrow
        draw_btn("<", left_col, map_y, (100, 180, 255), (30, 40, 60), "map_left", 40)
        # Map name (centered)
        map_name = self.font.render(self.selected_map.upper(), True, (100, 180, 255))
        self.screen.blit(map_name, (SCREEN_WIDTH // 2 - map_name.get_width() // 2, map_y + 4))
        # Right arrow
        draw_btn(">", right_col + btn_w - 40, map_y, (100, 180, 255), (30, 40, 60), "map_right", 40)

        # ===== SETTINGS ROW =====
        settings_y = 555
        pygame.draw.line(self.screen, (50, 50, 60), (left_col, settings_y - 10), (right_col + btn_w, settings_y - 10), 1)

        # Touch controls toggle
        touch_status = "ON" if self.mobile_controls else "OFF"
        touch_color = GREEN if self.mobile_controls else (100, 100, 100)
        touch_bg = (20, 50, 20) if self.mobile_controls else (35, 35, 40)
        draw_btn(f"Touch: {touch_status}", left_col, settings_y, touch_color, touch_bg, "touch_toggle")

        # Login/Account
        if current_user:
            draw_btn(f"{current_user[:8]}", right_col, settings_y, GREEN, (20, 50, 20), "login")
        else:
            draw_btn("Login", right_col, settings_y, (150, 150, 150), (35, 35, 40), "login")

        # Controls hint (only on desktop)
        if not IS_MOBILE:
            controls_hint = self.small_font.render("P1: WASD+Mouse | P2: IJKL+NumPad", True, GRAY)
            self.screen.blit(controls_hint, (SCREEN_WIDTH // 2 - controls_hint.get_width() // 2, 690))

    def draw_gameover(self):
        # Darken screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # Result - different for PvP mode
        if self.game_mode in ["pvp", "online_pvp"] and self.pvp_winner:
            if self.game_mode == "online_pvp":
                # For online PvP, show YOU WIN! or YOU LOSE! based on who won
                if self.pvp_winner == "Player 1":
                    result = self.big_font.render("YOU WIN!", True, GREEN)
                    subtitle = self.font.render("You defeated your opponent!", True, GREEN)
                else:
                    result = self.big_font.render("YOU LOSE!", True, RED)
                    subtitle = self.font.render("Your opponent won the battle!", True, RED)
            else:
                # Local PvP shows Player 1/2 wins
                result = self.big_font.render(f"{self.pvp_winner} WINS!", True, GREEN)
                subtitle = self.font.render("PvP Battle Complete", True, YELLOW)
            self.screen.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, 280))
            self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 360))
        elif self.game_mode == "coop" or self.game_mode == "online_coop":
            # Co-op mode (local or online)
            if len(self.robots) == 0:
                result = self.big_font.render("VICTORY!", True, GREEN)
                if self.game_mode == "online_coop":
                    subtitle = self.font.render("Online Team Win!", True, GREEN)
                else:
                    subtitle = self.font.render("Team Win! Great Teamwork!", True, GREEN)
            else:
                result = self.big_font.render("GAME OVER", True, RED)
                subtitle = self.font.render("Both players defeated!", True, RED)
            self.screen.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, 280))
            self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 360))
            # Score
            score = self.font.render(f"Score: {self.score} | Kills: {self.kills}", True, WHITE)
            self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 410))
        else:
            # Solo mode
            if len(self.robots) == 0:
                result = self.big_font.render("VICTORY!", True, GREEN)
            else:
                result = self.big_font.render("GAME OVER", True, RED)
            self.screen.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, 300))
            # Score
            score = self.font.render(f"Score: {self.score} | Kills: {self.kills}", True, WHITE)
            self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 400))

        # Options
        retry = self.small_font.render("[R] Play Again | [ESC] Menu", True, GRAY)
        self.screen.blit(retry, (SCREEN_WIDTH // 2 - retry.get_width() // 2, 500))

    def draw_online_menu(self):
        # Background
        self.screen.fill((20, 20, 40))

        # Title
        title = self.big_font.render("ONLINE MULTIPLAYER", True, (0, 200, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # Box
        box_width = 550
        box_height = 480
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = 100

        pygame.draw.rect(self.screen, (40, 40, 60), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (0, 200, 255), (box_x, box_y, box_width, box_height), 3)

        # Game mode selection - with touch buttons
        mode_label = self.font.render("Game Mode:", True, WHITE)
        self.screen.blit(mode_label, (box_x + 30, box_y + 15))

        # Row 1: Co-op, PvP - as buttons
        btn_w = 120
        btn_h = 35

        # CO-OP button
        coop_rect = pygame.Rect(box_x + 30, box_y + 50, btn_w, btn_h)
        coop_color = GREEN if self.online_game_mode == "coop" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 50), coop_rect)
        pygame.draw.rect(self.screen, coop_color, coop_rect, 2)
        coop_text = self.small_font.render("CO-OP", True, coop_color)
        self.screen.blit(coop_text, (coop_rect.centerx - coop_text.get_width()//2, coop_rect.centery - coop_text.get_height()//2))
        self.online_coop_btn = coop_rect

        # PVP button
        pvp_rect = pygame.Rect(box_x + 170, box_y + 50, btn_w, btn_h)
        pvp_color = RED if self.online_game_mode == "pvp" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 50), pvp_rect)
        pygame.draw.rect(self.screen, pvp_color, pvp_rect, 2)
        pvp_text = self.small_font.render("PVP", True, pvp_color)
        self.screen.blit(pvp_text, (pvp_rect.centerx - pvp_text.get_width()//2, pvp_rect.centery - pvp_text.get_height()//2))
        self.online_pvp_btn = pvp_rect

        # 2v2 button
        btn_2v2_rect = pygame.Rect(box_x + 310, box_y + 50, btn_w, btn_h)
        color_2v2 = (255, 200, 50) if self.online_game_mode == "2v2" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 50), btn_2v2_rect)
        pygame.draw.rect(self.screen, color_2v2, btn_2v2_rect, 2)
        text_2v2 = self.small_font.render("2v2", True, color_2v2)
        self.screen.blit(text_2v2, (btn_2v2_rect.centerx - text_2v2.get_width()//2, btn_2v2_rect.centery - text_2v2.get_height()//2))
        self.online_2v2_btn = btn_2v2_rect

        # 2v1 button
        btn_2v1_rect = pygame.Rect(box_x + 440, box_y + 50, btn_w - 20, btn_h)
        color_2v1 = (200, 100, 255) if self.online_game_mode == "2v1" else GRAY
        pygame.draw.rect(self.screen, (30, 30, 50), btn_2v1_rect)
        pygame.draw.rect(self.screen, color_2v1, btn_2v1_rect, 2)
        text_2v1 = self.small_font.render("2v1", True, color_2v1)
        self.screen.blit(text_2v1, (btn_2v1_rect.centerx - text_2v1.get_width()//2, btn_2v1_rect.centery - text_2v1.get_height()//2))
        self.online_2v1_btn = btn_2v1_rect

        # Separator after mode selection
        pygame.draw.line(self.screen, GRAY, (box_x + 20, box_y + 95), (box_x + box_width - 20, box_y + 95), 1)

        # Difficulty selection (for co-op and 2v2/2v1 modes)
        if self.online_game_mode in ["coop", "2v2", "2v1"]:
            diff_label = self.font.render("Difficulty:", True, WHITE)
            self.screen.blit(diff_label, (box_x + 30, box_y + 105))

            # Arrow buttons and difficulty display
            diff_name = self.online_difficulty.upper()
            diff_colors = {"easy": GREEN, "medium": YELLOW, "hard": ORANGE, "impossible": RED}
            diff_color = diff_colors.get(self.online_difficulty, WHITE)

            # Left arrow button
            left_btn = pygame.Rect(box_x + 200, box_y + 105, 40, 35)
            pygame.draw.rect(self.screen, (30, 30, 50), left_btn)
            pygame.draw.rect(self.screen, YELLOW, left_btn, 2)
            left_arrow = self.font.render("<", True, YELLOW)
            self.screen.blit(left_arrow, (left_btn.centerx - left_arrow.get_width()//2, left_btn.centery - left_arrow.get_height()//2))
            self.online_diff_left_btn = left_btn

            # Difficulty text
            diff_text = self.font.render(diff_name, True, diff_color)
            self.screen.blit(diff_text, (box_x + 260, box_y + 108))

            # Right arrow button
            right_btn = pygame.Rect(box_x + 260 + diff_text.get_width() + 15, box_y + 105, 40, 35)
            pygame.draw.rect(self.screen, (30, 30, 50), right_btn)
            pygame.draw.rect(self.screen, YELLOW, right_btn, 2)
            right_arrow = self.font.render(">", True, YELLOW)
            self.screen.blit(right_arrow, (right_btn.centerx - right_arrow.get_width()//2, right_btn.centery - right_arrow.get_height()//2))
            self.online_diff_right_btn = right_btn

            # Second separator
            pygame.draw.line(self.screen, GRAY, (box_x + 20, box_y + 150), (box_x + box_width - 20, box_y + 150), 1)
            options_start_y = box_y + 160
        else:
            # PvP mode - no difficulty selector
            options_start_y = box_y + 105

        # HOST GAME button
        host_btn = pygame.Rect(box_x + 30, options_start_y, box_width - 60, 55)
        pygame.draw.rect(self.screen, (20, 60, 20), host_btn)
        pygame.draw.rect(self.screen, GREEN, host_btn, 2)
        host_text = self.font.render("HOST GAME", True, GREEN)
        host_desc = self.small_font.render("Create a room and share code", True, GRAY)
        self.screen.blit(host_text, (host_btn.centerx - host_text.get_width()//2, host_btn.y + 5))
        self.screen.blit(host_desc, (host_btn.centerx - host_desc.get_width()//2, host_btn.y + 32))
        self.online_host_btn = host_btn

        # JOIN GAME button
        join_btn = pygame.Rect(box_x + 30, options_start_y + 65, box_width - 60, 55)
        pygame.draw.rect(self.screen, (60, 60, 20), join_btn)
        pygame.draw.rect(self.screen, YELLOW, join_btn, 2)
        join_text = self.font.render("JOIN GAME", True, YELLOW)
        join_desc = self.small_font.render("Enter 4-digit room code", True, GRAY)
        self.screen.blit(join_text, (join_btn.centerx - join_text.get_width()//2, join_btn.y + 5))
        self.screen.blit(join_desc, (join_btn.centerx - join_desc.get_width()//2, join_btn.y + 32))
        self.online_join_btn = join_btn

        # Room code input (if joining)
        if self.online_input_active or len(self.online_input_code) > 0:
            code_label = self.font.render("Room Code:", True, WHITE)
            self.screen.blit(code_label, (box_x + 30, options_start_y + 135))

            # Code input box
            code_box = pygame.Rect(box_x + 200, options_start_y + 130, 150, 40)
            pygame.draw.rect(self.screen, (60, 60, 80), code_box)
            pygame.draw.rect(self.screen, YELLOW, code_box, 2)

            code_text = self.big_font.render(self.online_input_code, True, WHITE)
            self.screen.blit(code_text, (code_box.x + 20, code_box.y + 5))

            if len(self.online_input_code) == 4:
                enter_hint = self.small_font.render("Press ENTER to join", True, GREEN)
                self.screen.blit(enter_hint, (box_x + 200, options_start_y + 175))

        # Message
        if self.online_message:
            msg = self.font.render(self.online_message, True, ORANGE)
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, options_start_y + 210))

        # Back button
        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, options_start_y + 250, 200, 40)
        pygame.draw.rect(self.screen, (60, 20, 20), back_btn)
        pygame.draw.rect(self.screen, RED, back_btn, 2)
        back_text = self.small_font.render("Back to Menu", True, RED)
        self.screen.blit(back_text, (back_btn.centerx - back_text.get_width()//2, back_btn.centery - back_text.get_height()//2))
        self.online_back_btn = back_btn

        # Version
        version = self.small_font.render("v3.0", True, WHITE)
        self.screen.blit(version, (10, 10))

    def draw_waiting_screen(self):
        # Background
        self.screen.fill((20, 20, 40))

        # Title
        if self.is_host:
            title = self.big_font.render("HOSTING GAME", True, GREEN)
        else:
            title = self.big_font.render("JOINING GAME", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        # Room code display (for host)
        if self.is_host and self.online_room_code:
            code_label = self.font.render("Room Code:", True, WHITE)
            self.screen.blit(code_label, (SCREEN_WIDTH // 2 - code_label.get_width() // 2, 200))

            code_text = self.big_font.render(self.online_room_code, True, (0, 255, 200))
            self.screen.blit(code_text, (SCREEN_WIDTH // 2 - code_text.get_width() // 2, 240))

            share_text = self.small_font.render("Share this code with your friend!", True, GRAY)
            self.screen.blit(share_text, (SCREEN_WIDTH // 2 - share_text.get_width() // 2, 300))

        # Status message
        status_text = self.font.render(self.online_message, True, ORANGE)
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 360))

        # Connection status indicator
        if self.online_status == "connecting":
            # Animated dots
            dots = "." * ((pygame.time.get_ticks() // 500) % 4)
            waiting = self.font.render(f"Waiting{dots}", True, YELLOW)
            self.screen.blit(waiting, (SCREEN_WIDTH // 2 - waiting.get_width() // 2, 420))
        elif self.online_status == "connected":
            connected = self.font.render("Connected! Starting game...", True, GREEN)
            self.screen.blit(connected, (SCREEN_WIDTH // 2 - connected.get_width() // 2, 420))

        # Cancel option
        cancel_text = self.small_font.render("[ESC] Cancel", True, RED)
        self.screen.blit(cancel_text, (SCREEN_WIDTH // 2 - cancel_text.get_width() // 2, 500))

    def draw_shop(self):
        # Darken screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        # Shop box - 2 columns layout
        box_width = 1100
        box_height = 650
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2

        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, YELLOW, (box_x, box_y, box_width, box_height), 4)

        # Title
        title = self.big_font.render("SHOP", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, box_y + 10))

        # Coins
        coins = self.font.render(f"Your Coins: {self.player.coins}", True, GREEN)
        self.screen.blit(coins, (SCREEN_WIDTH // 2 - coins.get_width() // 2, box_y + 50))

        # Column settings
        col1_x = box_x + 25
        col2_x = box_x + box_width // 2 + 15
        item_height = 48
        start_y = box_y + 90

        # Left column items
        item_y = start_y

        # Item 1: Shotgun
        if not self.player.has_shotgun:
            color = WHITE if self.player.coins >= 10 else GRAY
            text = self.small_font.render("[1] Shotgun - 10c", True, color)
            desc = self.small_font.render("Spread shot | 8 shells | High damage", True, ORANGE)
        else:
            text = self.small_font.render("[1] Shotgun - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Item 2: RPG
        item_y += item_height
        if not self.player.has_rpg:
            color = WHITE if self.player.coins >= 50 else GRAY
            text = self.small_font.render("[2] RPG - 50c", True, color)
            desc = self.small_font.render("Explosive | 200 Dmg | 8 rockets", True, RED)
        else:
            text = self.small_font.render("[2] RPG - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Item 3: Medkit
        item_y += item_height
        if self.player.medkit_charges > 0:
            text = self.small_font.render(f"[3] First Aid Kit - {self.player.medkit_charges} uses", True, GREEN)
            desc = self.small_font.render("Press H to heal to full", True, GREEN)
        else:
            color = WHITE if self.player.coins >= 90 else GRAY
            text = self.small_font.render("[3] First Aid Kit - 90c", True, color)
            desc = self.small_font.render("3 uses | Full heal | Press H", True, (0, 200, 0))
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Item 4: Sniper
        item_y += item_height
        if not self.player.has_sniper:
            color = WHITE if self.player.coins >= 150 else GRAY
            text = self.small_font.render("[4] Sniper - 150c", True, color)
            desc = self.small_font.render("180 Dmg | Headshot bonus | 10 rounds", True, (0, 255, 255))
        else:
            text = self.small_font.render("[4] Sniper - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Item 5: Dual Pistols
        item_y += item_height
        if not self.player.has_dual_pistols:
            color = WHITE if self.player.coins >= 60 else GRAY
            text = self.small_font.render("[5] Dual Pistols - 60c", True, color)
            desc = self.small_font.render("35 Dmg x2 | Fast fire | 14 rounds", True, (255, 215, 0))
        else:
            text = self.small_font.render("[5] Dual Pistols - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Item 6: Throwing Knives
        item_y += item_height
        if not self.player.has_throwing_knives:
            color = WHITE if self.player.coins >= 70 else GRAY
            text = self.small_font.render("[6] Throwing Knives - 70c", True, color)
            desc = self.small_font.render("50 Dmg | Silent | 16 knives", True, (192, 192, 192))
        else:
            text = self.small_font.render("[6] Throwing Knives - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col1_x, item_y))
        self.screen.blit(desc, (col1_x, item_y + 20))

        # Right column items
        item_y = start_y

        # Item 7: Flamethrower
        if not self.player.has_flamethrower:
            color = WHITE if self.player.coins >= 80 else GRAY
            text = self.small_font.render("[7] Flamethrower - 80c", True, color)
            desc = self.small_font.render("Continuous fire | 100 fuel", True, (255, 100, 0))
        else:
            text = self.small_font.render("[7] Flamethrower - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Item 8: Crossbow
        item_y += item_height
        if not self.player.has_crossbow:
            color = WHITE if self.player.coins >= 100 else GRAY
            text = self.small_font.render("[8] Crossbow - 100c", True, color)
            desc = self.small_font.render("90 Dmg | Slow | 12 bolts", True, (139, 69, 19))
        else:
            text = self.small_font.render("[8] Crossbow - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Item 9: Freeze Ray
        item_y += item_height
        if not self.player.has_freeze:
            color = WHITE if self.player.coins >= 110 else GRAY
            text = self.small_font.render("[9] Freeze Ray - 110c", True, color)
            desc = self.small_font.render("Slows enemies | 40 shots", True, (150, 220, 255))
        else:
            text = self.small_font.render("[9] Freeze Ray - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Item 0: Laser Gun
        item_y += item_height
        if not self.player.has_laser:
            color = WHITE if self.player.coins >= 120 else GRAY
            text = self.small_font.render("[0] Laser Gun - 120c", True, color)
            desc = self.small_font.render("Fast beam | 50 charge", True, (0, 255, 0))
        else:
            text = self.small_font.render("[0] Laser Gun - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Item E: Electric Gun
        item_y += item_height
        if not self.player.has_electric:
            color = WHITE if self.player.coins >= 140 else GRAY
            text = self.small_font.render("[E] Electric Gun - 140c", True, color)
            desc = self.small_font.render("Chain lightning | 30 Dmg | 30 shots", True, (100, 150, 255))
        else:
            text = self.small_font.render("[E] Electric Gun - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Item M: Minigun
        item_y += item_height
        if not self.player.has_minigun:
            color = WHITE if self.player.coins >= 200 else GRAY
            text = self.small_font.render("[M] Minigun - 200c", True, color)
            desc = self.small_font.render("Very fast fire | 200 rounds", True, (180, 180, 180))
        else:
            text = self.small_font.render("[M] Minigun - OWNED", True, GREEN)
            desc = self.small_font.render("Unlocked!", True, GREEN)
        self.screen.blit(text, (col2_x, item_y))
        self.screen.blit(desc, (col2_x, item_y + 20))

        # Avatar shop link
        avatar_text = self.font.render("[A] Avatar Shop", True, (150, 200, 255))
        self.screen.blit(avatar_text, (box_x + 30, box_y + box_height - 45))

        # Close option
        close_text = self.font.render("[ESC] Close Shop", True, RED)
        self.screen.blit(close_text, (SCREEN_WIDTH // 2 - close_text.get_width() // 2 + 100, box_y + box_height - 45))

    def draw_avatar_shop(self):
        """Draw the avatar shop screen"""
        # Darken screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        # Shop box
        box_width = 900
        box_height = 550
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2

        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (150, 200, 255), (box_x, box_y, box_width, box_height), 4)

        # Title
        title = self.big_font.render("AVATAR SHOP", True, (150, 200, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, box_y + 15))

        # Coins
        coins = self.font.render(f"Your Coins: {self.player.coins}", True, GREEN)
        self.screen.blit(coins, (SCREEN_WIDTH // 2 - coins.get_width() // 2, box_y + 60))

        # Get avatar list
        avatar_keys = list(AVATAR_TYPES.keys())
        selected_type = avatar_keys[self.selected_avatar_index]
        selected_data = AVATAR_TYPES[selected_type]

        # Avatar preview area (large, centered)
        preview_x = SCREEN_WIDTH // 2
        preview_y = box_y + 180

        # Create a temporary avatar to draw preview
        preview_avatar = Avatar(selected_type)

        # Animate preview avatar
        anim_angle = math.sin(pygame.time.get_ticks() * 0.002) * 0.5
        preview_avatar.draw(self.screen, preview_x, preview_y, anim_angle,
                           walk_speed=2, anim_timer=pygame.time.get_ticks() // 16)

        # Draw preview hands holding a rifle
        preview_avatar.draw_holding_hands(self.screen, preview_x, preview_y, anim_angle,
                                         "Rifle", is_reloading=False, reload_phase=0)

        # Avatar name and info
        name_text = self.big_font.render(selected_data["name"], True, WHITE)
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, preview_y + 60))

        # Description
        desc_text = self.small_font.render(selected_data["description"], True, (200, 200, 200))
        self.screen.blit(desc_text, (SCREEN_WIDTH // 2 - desc_text.get_width() // 2, preview_y + 100))

        # Price / Owned status
        if selected_type in self.player.owned_avatars:
            if self.player.avatar_type == selected_type:
                status_text = self.font.render("EQUIPPED", True, GREEN)
            else:
                status_text = self.font.render("OWNED - Press ENTER to Equip", True, (100, 255, 100))
        else:
            price = selected_data["price"]
            color = GREEN if self.player.coins >= price else RED
            status_text = self.font.render(f"Price: {price} coins - Press ENTER to Buy", True, color)
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, preview_y + 135))

        # Navigation arrows and avatar carousel
        arrow_y = preview_y
        left_arrow = self.big_font.render("<", True, WHITE)
        right_arrow = self.big_font.render(">", True, WHITE)
        self.screen.blit(left_arrow, (box_x + 50, arrow_y - 20))
        self.screen.blit(right_arrow, (box_x + box_width - 80, arrow_y - 20))

        # Show mini previews of adjacent avatars
        for offset in [-2, -1, 1, 2]:
            idx = (self.selected_avatar_index + offset) % len(avatar_keys)
            mini_type = avatar_keys[idx]
            mini_data = AVATAR_TYPES[mini_type]

            # Position based on offset
            mini_x = preview_x + offset * 120
            mini_y = preview_y

            # Draw mini avatar (smaller scale indicated by position)
            mini_avatar = Avatar(mini_type)
            mini_avatar.head_radius = 5
            mini_avatar.torso_width = 9
            mini_avatar.torso_height = 8
            mini_avatar.arm_length = 8
            mini_avatar.leg_length = 7
            mini_avatar.hand_radius = 3

            # Dim non-selected avatars
            if offset != 0:
                mini_avatar.draw(self.screen, mini_x, mini_y, 0, anim_timer=0)

                # Show owned indicator
                if mini_type in self.player.owned_avatars:
                    owned_dot = pygame.Surface((10, 10), pygame.SRCALPHA)
                    pygame.draw.circle(owned_dot, GREEN, (5, 5), 5)
                    self.screen.blit(owned_dot, (int(mini_x - 5), int(mini_y + 25)))

        # Instructions
        nav_text = self.small_font.render("LEFT/RIGHT: Browse | ENTER: Buy/Equip | ESC: Back to Weapons", True, (180, 180, 180))
        self.screen.blit(nav_text, (SCREEN_WIDTH // 2 - nav_text.get_width() // 2, box_y + box_height - 35))

        # Show avatar index
        index_text = self.small_font.render(f"{self.selected_avatar_index + 1} / {len(avatar_keys)}", True, (150, 150, 150))
        self.screen.blit(index_text, (SCREEN_WIDTH // 2 - index_text.get_width() // 2, box_y + box_height - 60))

    def draw(self):

        if self.state == "login":
            self.draw_login_screen()

        elif self.state == "menu":
            self.draw_menu()

        elif self.state == "online_menu":
            self.draw_online_menu()

        elif self.state == "waiting":
            self.draw_waiting_screen()

        elif self.state == "playing" or self.state == "gameover" or self.state == "shop" or self.state == "avatar_shop":
            if self.split_screen and self.player2:
                # Split-screen rendering for local multiplayer
                half_width = SCREEN_WIDTH // 2

                # Create surfaces for each player's view
                surface1 = pygame.Surface((half_width, SCREEN_HEIGHT))
                surface2 = pygame.Surface((half_width, SCREEN_HEIGHT))

                # Draw world from player 1's perspective
                self.draw_world_to_surface(surface1, self.camera)
                self.draw_split_screen_hud(surface1, self.player, True, half_width)

                # Draw world from player 2's perspective
                self.draw_world_to_surface(surface2, self.camera2)
                self.draw_split_screen_hud(surface2, self.player2, False, half_width)

                # Blit both surfaces to screen
                self.screen.blit(surface1, (0, 0))
                self.screen.blit(surface2, (half_width, 0))

                # Draw divider line
                pygame.draw.line(self.screen, WHITE, (half_width, 0), (half_width, SCREEN_HEIGHT), 4)

                # Draw score/kills in center bottom
                score_text = self.small_font.render(f"Score: {self.score} | Kills: {self.kills}", True, YELLOW)
                self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT - 30))

                # Draw robots remaining
                robots_text = self.small_font.render(f"Robots: {len(self.robots)}", True, ORANGE)
                self.screen.blit(robots_text, (SCREEN_WIDTH // 2 - robots_text.get_width() // 2, SCREEN_HEIGHT - 55))
            else:
                # Standard single-screen rendering
                self.draw_background()

                # Draw obstacles
                for obs in self.obstacles:
                    obs.draw(self.screen, self.camera)

                # Draw bullets
                for bullet in self.bullets:
                    bullet.draw(self.screen, self.camera)

                # Draw grenades
                for grenade in self.grenades:
                    grenade.draw(self.screen, self.camera)

                # Draw smoke grenades
                for smoke in self.smoke_grenades:
                    smoke.draw(self.screen, self.camera)

                # Draw smoke clouds
                for cloud in self.smoke_clouds:
                    cloud.draw(self.screen, self.camera)

                # Draw explosions
                for explosion in self.explosions:
                    explosion.draw(self.screen, self.camera)

                # Draw robots - set sniper target visibility based on player's current weapon
                player1_has_sniper = self.player.weapon["name"] == "Sniper"
                player2_has_sniper = self.player2 and self.player2.weapon["name"] == "Sniper"
                has_sniper = player1_has_sniper or player2_has_sniper
                for robot in self.robots:
                    robot.show_sniper_target = has_sniper
                    robot.draw(self.screen, self.camera)

                # Draw boss
                if self.boss:
                    self.boss.show_sniper_target = has_sniper
                    self.boss.draw(self.screen, self.camera)

                # Draw shell casings (on ground, behind player)
                for casing in self.shell_casings:
                    casing.draw(self.screen, self.camera)

                # Draw player
                self.player.draw(self.screen, self.camera)

                # Draw Player 2 (in multiplayer modes)
                if self.player2 and self.player2.health > 0:
                    self.player2.draw(self.screen, self.camera)

                # Draw muzzle flashes (in front of player)
                for flash in self.muzzle_flashes:
                    flash.draw(self.screen, self.camera)

                # Draw healing effects
                for effect in self.healing_effects:
                    effect.draw(self.screen, self.camera)

                # Draw HUD
                self.draw_hud()

                # Draw minimap
                self.draw_minimap()

            # Draw mobile controls
            if self.mobile_controls and self.state == "playing":
                self.joystick.draw(self.screen)
                self.aim_joystick.draw(self.screen)
                self.shoot_btn.draw(self.screen)
                self.reload_btn.draw(self.screen)
                self.switch_btn.draw(self.screen)
                self.medkit_btn.draw(self.screen)

            if self.state == "gameover":
                self.draw_gameover()
            elif self.state == "shop":
                self.draw_shop()
            elif self.state == "avatar_shop":
                self.draw_avatar_shop()

        pygame.display.flip()

    async def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)  # Required for Pygbag

        pygame.quit()


async def main():
    print("=" * 50)
    print("   ARENA SHOOTER 2D - ROBOT BATTLE")
    print("=" * 50)
    print(f"\nMap Size: {MAP_WIDTH}x{MAP_HEIGHT}")
    print("Starting game...")

    game = Game()
    await game.run()


# Pygbag entry point
asyncio.run(main())
