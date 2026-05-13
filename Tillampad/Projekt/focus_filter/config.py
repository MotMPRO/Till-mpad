# ============================================================
# File        : config.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Alla inställningar för Focus Filter.
#               Ändra värden här för att justera mjukhet,
#               hold-frames och detektionsupplösning.
# ============================================================

# --- kamera ---
CAM_WIDTH   = 640
CAM_HEIGHT  = 480
CAM_FPS     = 30
WINDOW_NAME = "Focus Filter"

# --- handspårning ---
# interpolationsfaktor för EMA-utjämning (0 = ingen, 1 = ingen rörelse)
# sänk värdet för snabbare respons
SMOOTH_ALPHA          = 0.7

# minsta confidence för vänster/höger-klassning av handen
HANDEDNESS_MIN_SCORE  = 0.8

# antal frames resize-gesten måste hållas innan den aktiveras
# förhindrar oavsiktlig resize vid snabba rörelser
RESIZE_HOLD_FRAMES    = 3

# upplösning som mediapipe detection körs på
# lägre = snabbare men kan missa händer långt bort
DETECT_WIDTH          = 320
