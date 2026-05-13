# ============================================================
# File        : hands.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Handdetektering med MediaPipe för Focus Filter.
#               Kör detection på nedskalad bild för prestanda.
#               Koordinater mjukas ut med EMA mot skakighet.
# ============================================================

import cv2
import mediapipe as mp

from config import DETECT_WIDTH, HANDEDNESS_MIN_SCORE, SMOOTH_ALPHA

_mp_hands = mp.solutions.hands


# ------------------------------------------------------------
# kollar om ett finger är utsträckt
# fingerspetsen ska vara ovanför mellanleden (lägre y = högre upp)
# margin = extra buffert för att undvika falska positiver
# ------------------------------------------------------------
def finger_extended(lm, tip, pip, margin=0.02):
    return lm.landmark[tip].y < lm.landmark[pip].y - margin


# ============================================================
# HandDetector – kapslar in mediapipe Hands
# main.py anropar detect(frame) varje frame
# ============================================================
class HandDetector:

    # ----------------------------------------------------------
    # skapar mediapipe Hands-sessionen med optimerade inställningar
    # model_complexity=0 för snabbast möjliga detection
    # ----------------------------------------------------------
    def __init__(self):
        self._hands = _mp_hands.Hands(
            max_num_hands            = 2,
            model_complexity         = 0,
            min_detection_confidence = 0.5,
            min_tracking_confidence  = 0.3,
        )
        self._smooth = {}  # EMA-historik per hand (nyckel = "Label_i")

    # ----------------------------------------------------------
    # frigör mediapipe-resurser
    # anropas av main.py i finally-blocket vid avslut
    # ----------------------------------------------------------
    def close(self):
        self._hands.close()

    # ----------------------------------------------------------
    # kör handdetektering och returnerar lista med hand-dicts
    # varje dict innehåller: idx_ext, mid_ext, idx, mid, idx_n, mid_n
    # ----------------------------------------------------------
    def detect(self, frame):
        h, w = frame.shape[:2]

        # skala ned för snabbare detection
        if w > DETECT_WIDTH:
            scale = DETECT_WIDTH / w
            small = cv2.resize(frame, (DETECT_WIDTH, int(h * scale)), interpolation=cv2.INTER_AREA)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        rgb.flags.writeable = False
        result = self._hands.process(rgb)

        hands_data = []
        seen_keys  = set()

        if result.multi_hand_landmarks and result.multi_handedness:
            for i in range(len(result.multi_hand_landmarks)):
                lm   = result.multi_hand_landmarks[i]
                info = result.multi_handedness[i]
                cls  = info.classification[0]

                # hoppa över osäkra klassningar
                if cls.score < HANDEDNESS_MIN_SCORE:
                    continue

                key   = cls.label + "_" + str(i)
                idx_n = (lm.landmark[8].x,  lm.landmark[8].y)   # pekfinger normaliserat
                mid_n = (lm.landmark[12].x, lm.landmark[12].y)  # långfinger normaliserat

                # EMA-utjämning: smoothed = alpha * previous + (1-alpha) * current
                # ger mjukare rörelse utan fördröjning vid snabba gester
                prev = self._smooth.get(key)
                if prev is not None:
                    pi, pm = prev
                    idx_n = (
                        SMOOTH_ALPHA * pi[0] + (1 - SMOOTH_ALPHA) * idx_n[0],
                        SMOOTH_ALPHA * pi[1] + (1 - SMOOTH_ALPHA) * idx_n[1],
                    )
                    mid_n = (
                        SMOOTH_ALPHA * pm[0] + (1 - SMOOTH_ALPHA) * mid_n[0],
                        SMOOTH_ALPHA * pm[1] + (1 - SMOOTH_ALPHA) * mid_n[1],
                    )

                self._smooth[key] = (idx_n, mid_n)
                seen_keys.add(key)

                hands_data.append({
                    "idx_ext": finger_extended(lm, 8,  6),   # pekfingret utsträckt?
                    "mid_ext": finger_extended(lm, 12, 10),  # långfingret utsträckt?
                    "idx"    : (int(idx_n[0] * w), int(idx_n[1] * h)),
                    "mid"    : (int(mid_n[0] * w), int(mid_n[1] * h)),
                    "idx_n"  : idx_n,
                    "mid_n"  : mid_n,
                })

        # ta bort gamla händer ur EMA-historiken
        for k in list(self._smooth.keys()):
            if k not in seen_keys:
                del self._smooth[k]

        return hands_data
