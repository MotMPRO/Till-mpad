# ============================================================
# File        : words.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Ordbanker sorterade per ordklass.
#               Lägg till fler ord direkt i listorna.
#               Nycklarna måste matcha TYPE_COLOR i config.py.
# ============================================================

WORDS = {
    "ADJECTIVE": [
        "fast", "big", "small", "cold", "warm", "happy", "sad",
        "strong", "weak", "soft", "hard", "young", "old", "new",
        "funny", "quiet", "bright", "dark", "heavy", "lazy",
        "brave", "clever", "sharp", "smooth", "wild",
    ],
    "NOUN": [
        "dog", "cat", "house", "car", "sun", "moon", "book", "tree",
        "flower", "water", "fire", "air", "earth", "child", "city",
        "bird", "lake", "mountain", "bridge", "school", "door",
        "window", "table", "chair", "storm",
    ],
    "VERB": [
        "run", "jump", "sing", "dance", "write", "read",
        "eat", "sleep", "play", "work", "fly", "swim", "talk",
        "listen", "see", "hear", "think", "laugh", "cry", "smile",
        "rest", "fight", "win", "fall", "move",
    ],
}

# uppdateras automatiskt om nya klasser läggs till i WORDS
ALL_TYPES = list(WORDS.keys())
