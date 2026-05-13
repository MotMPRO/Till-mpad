# ============================================================
# File        : config.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Alla konstanter för Body Word Game samlade
#               på ett ställe. Ändra värden här istället för
#               att leta i game.py eller renderer.py.
# ============================================================

import cv2
import mediapipe as mp

# --- kamerainställningar ---
CAM_WIDTH  = 960   # önskad bredd i pixlar
CAM_HEIGHT = 540   # önskad höjd i pixlar
CAM_FPS    = 30    # bildfrekvens

# --- spelbalans ---
BASE_SPEED        = 130.0  # px/sek vid referensavstånd
BASE_INTERVAL     = 2.0    # sekunder mellan nytt ord
BASE_CATCH_RADIUS = 58     # fångstradie i px

# --- avståndskalibrering ---
# normaliserad axelbredd som mediapipe rapporterar på "bra" avstånd
# ju närmre kameran desto bredare axlar → högre dfactor → snabbare spel
REF_SHOULDER_WIDTH = 0.27

# --- skelett-rendering ---
BONE_COLOR     = (255, 255, 255)  # vit (BGR)
BONE_THICKNESS = 2                # linjetjocklek i px
JOINT_R        = 6                # ledkulornas radier i px

# --- ordtypsfärger (BGR) ---
# nycklarna måste matcha nycklarna i words.py
TYPE_COLOR = {
    "ADJECTIVE" : (80, 200, 255),   # ljusblå
    "NOUN"      : (80, 255, 160),   # mintgrön
    "VERB"      : (80, 130, 255),   # lila-blå
}

# --- fångstpunkter ---
# vilka kroppspunkter som fångar ord
# handleder, armbågar och vrister ger en naturlig rörelseyta
_PL = mp.solutions.pose.PoseLandmark
CATCH_LM_IDS = [
    _PL.LEFT_WRIST,
    _PL.RIGHT_WRIST,
    _PL.LEFT_ELBOW,
    _PL.RIGHT_ELBOW,
    _PL.LEFT_ANKLE,
    _PL.RIGHT_ANKLE,
]

# --- typsnitt ---
FONT = cv2.FONT_HERSHEY_DUPLEX
