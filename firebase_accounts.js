// Firebase Realtime Database - Account Cloud Sync
const FIREBASE_CONFIG = {
    apiKey: "AIzaSyDavHMhsNt2cXtCSG9nHHeXr88C4GBk6TE",
    databaseURL: "https://d-shooter-game-f5021-default-rtdb.firebaseio.com"
};

// Simple hash function for passcode (not cryptographically secure, but good enough for a game)
function hashPasscode(passcode) {
    let hash = 0;
    for (let i = 0; i < passcode.length; i++) {
        const char = passcode.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(16);
}

// Firebase REST API wrapper
const FirebaseDB = {
    baseURL: FIREBASE_CONFIG.databaseURL,

    // Get user data by username
    async getUser(username) {
        try {
            const safeName = username.toLowerCase().replace(/[^a-z0-9]/g, '_');
            const response = await fetch(`${this.baseURL}/users/${safeName}.json`);
            if (!response.ok) return null;
            const data = await response.json();
            return data;
        } catch (error) {
            console.error("Firebase getUser error:", error);
            return null;
        }
    },

    // Create new user account
    async createUser(username, passcode, initialData = {}) {
        try {
            const safeName = username.toLowerCase().replace(/[^a-z0-9]/g, '_');
            const userData = {
                username: username,
                passcodeHash: hashPasscode(passcode),
                coins: initialData.coins || 0,
                has_shotgun: initialData.has_shotgun || false,
                has_rpg: initialData.has_rpg || false,
                has_sniper: initialData.has_sniper || false,
                has_flamethrower: initialData.has_flamethrower || false,
                has_laser: initialData.has_laser || false,
                has_minigun: initialData.has_minigun || false,
                has_crossbow: initialData.has_crossbow || false,
                has_freeze_ray: initialData.has_freeze_ray || false,
                has_electric: initialData.has_electric || false,
                has_dual_pistols: initialData.has_dual_pistols || false,
                has_throwing_knives: initialData.has_throwing_knives || false,
                medkit_charges: initialData.medkit_charges || 0,
                current_avatar: initialData.current_avatar || "default",
                owned_avatars: initialData.owned_avatars || ["default"],
                created_at: Date.now(),
                last_login: Date.now()
            };

            const response = await fetch(`${this.baseURL}/users/${safeName}.json`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error("Firebase createUser error:", error);
            return null;
        }
    },

    // Verify login credentials
    async verifyLogin(username, passcode) {
        const user = await this.getUser(username);
        if (!user) return { success: false, error: "User not found" };

        if (user.passcodeHash !== hashPasscode(passcode)) {
            return { success: false, error: "Wrong passcode" };
        }

        // Update last login
        const safeName = username.toLowerCase().replace(/[^a-z0-9]/g, '_');
        await fetch(`${this.baseURL}/users/${safeName}/last_login.json`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Date.now())
        });

        return { success: true, data: user };
    },

    // Save user progress
    async saveProgress(username, progressData) {
        try {
            const safeName = username.toLowerCase().replace(/[^a-z0-9]/g, '_');

            // Only update specific fields, not entire user object
            const updates = {
                coins: progressData.coins || 0,
                has_shotgun: progressData.has_shotgun || false,
                has_rpg: progressData.has_rpg || false,
                has_sniper: progressData.has_sniper || false,
                has_flamethrower: progressData.has_flamethrower || false,
                has_laser: progressData.has_laser || false,
                has_minigun: progressData.has_minigun || false,
                has_crossbow: progressData.has_crossbow || false,
                has_freeze_ray: progressData.has_freeze_ray || false,
                has_electric: progressData.has_electric || false,
                has_dual_pistols: progressData.has_dual_pistols || false,
                has_throwing_knives: progressData.has_throwing_knives || false,
                medkit_charges: progressData.medkit_charges || 0,
                current_avatar: progressData.current_avatar || "default",
                owned_avatars: progressData.owned_avatars || ["default"],
                last_save: Date.now()
            };

            // Update each field
            for (const [key, value] of Object.entries(updates)) {
                await fetch(`${this.baseURL}/users/${safeName}/${key}.json`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(value)
                });
            }

            console.log("Progress saved to cloud for:", username);
            return true;
        } catch (error) {
            console.error("Firebase saveProgress error:", error);
            return false;
        }
    },

    // Check if username exists
    async userExists(username) {
        const user = await this.getUser(username);
        return user !== null;
    }
};

// Expose to window for Python access
window.FirebaseDB = FirebaseDB;

console.log("Firebase Accounts module loaded");
