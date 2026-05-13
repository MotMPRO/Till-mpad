# ============================================================
# File        : game.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : All spellogik för Body Word Game.
#               Spawn, fångst, poäng och HUD-rendering.
#               Ingen kamerakod här – det sköter main.py.
# ============================================================

import random
import time

import mediapipe as mp
import numpy as np

from config import (
    BASE_CATCH_RADIUS, BASE_INTERVAL, BASE_SPEED,
    CATCH_LM_IDS, REF_SHOULDER_WIDTH, TYPE_COLOR,
)
from renderer import FallingWord, draw_panel, draw_text
from words import ALL_TYPES, WORDS

_pose = mp.solutions.pose


# ------------------------------------------------------------
# skattar spelarens avstånd via normaliserad axelbredd
# ju närmre kameran desto bredare axlar → högre dfactor
# resultatet klipps till [0.3, 2.5] för att undvika extremvärden
# ------------------------------------------------------------
def distance_factor(pose_lm):
    lm = pose_lm.landmark
    ls = lm[_pose.PoseLandmark.LEFT_SHOULDER]
    rs = lm[_pose.PoseLandmark.RIGHT_SHOULDER]
    if ls.visibility < 0.5 or rs.visibility < 0.5:
        return 1.0  # axlarna syns inte – använd neutralt värde
    shoulder_w = abs(rs.x - ls.x)
    return max(0.3, min(2.5, shoulder_w / REF_SHOULDER_WIDTH))


# ============================================================
# Game – hanterar all spelstatus och logik
# main.py anropar check_catch(), update() och draw_hud() per frame
# ============================================================
class Game:

    # ----------------------------------------------------------
    # skapar spelet och startar med reset()
    # ----------------------------------------------------------
    def __init__(self):
        self.reset()

    # ----------------------------------------------------------
    # återställer all speldata till startläge
    # anropas också av R-tangenten i main.py
    # ----------------------------------------------------------
    def reset(self):
        self.score      = 0
        self.quest      = random.choice(ALL_TYPES)
        self.words      = []
        self.last_spawn = time.time()
        self.fb_text    = ""
        self.fb_color   = (255, 255, 255)
        self.fb_timer   = 0.0

    # ----------------------------------------------------------
    # skapar ett nytt ord om det har gått tillräckligt lång tid
    # spawn-intervallet minskar när dfactor är hög (spelaren nära)
    # quest-ordklassen spawnar 40% av gångerna
    # ----------------------------------------------------------
    def _maybe_spawn(self, w, h, dfactor):
        interval = BASE_INTERVAL / max(0.3, dfactor)
        if time.time() - self.last_spawn < interval:
            return
        self.last_spawn = time.time()

        wtype  = self.quest if random.random() < 0.40 else random.choice(ALL_TYPES)
        text   = random.choice(WORDS[wtype])
        speed  = BASE_SPEED * max(0.4, dfactor) * random.uniform(0.85, 1.15)
        scale  = 0.82 * max(0.55, dfactor)
        margin = 90

        # bugfix: hoppa spawn om skärmen är för smal (t.ex. kamerafel)
        if w <= margin * 2:
            return
        x = random.randint(margin, w - margin)
        self.words.append(FallingWord(text, wtype, x, speed, scale, h))

    # ----------------------------------------------------------
    # kollar om en kroppspunkt rör vid ett fallande ord
    # cirkulär kollision: avstånd² < radie²
    # radien skalas med dfactor så avstånd inte ger orättvis fördel
    # ----------------------------------------------------------
    def check_catch(self, pose_lm, w, h, dfactor):
        catch_r = int(BASE_CATCH_RADIUS / max(0.4, dfactor))
        lm      = pose_lm.landmark

        # samla pixelpositioner för alla synliga fångstpunkter
        catchers = []
        for lm_id in CATCH_LM_IDS:
            pt = lm[lm_id]
            if pt.visibility > 0.35:
                catchers.append((int(pt.x * w), int(pt.y * h)))

        for word in self.words:
            if word.caught:
                continue
            wx, wy = word.x, int(word.y)
            for cx, cy in catchers:
                if (cx - wx) ** 2 + (cy - wy) ** 2 < catch_r ** 2:
                    self._register_catch(word)
                    break  # bara en fångst per ord per frame

    # ----------------------------------------------------------
    # hanterar ett fångat ord: poäng, feedback och ny quest
    # rätt ordklass → +1 poäng och ny quest
    # fel ordklass  → feedback utan poängändring
    # ----------------------------------------------------------
    def _register_catch(self, word):
        word.caught = True
        word.flash  = 0.75

        if word.wtype == self.quest:
            self.score   += 1
            self.fb_text  = "+1  '" + word.text + "' is a " + word.wtype + "!"
            self.fb_color = (50, 255, 100)

            # ny quest – alltid en annan klass än den precis fångade
            # bugfix: om bara en ordklass finns behålls quest (undviker krasch)
            others = [q for q in ALL_TYPES if q != self.quest]
            self.quest = random.choice(others) if others else self.quest
        else:
            self.fb_text  = "WRONG!  '" + word.text + "' is a " + word.wtype
            self.fb_color = (60, 80, 255)

        self.fb_timer = 2.2

    # ----------------------------------------------------------
    # uppdaterar all spellogik för en frame
    # ordning: spawn → flytta → rensa → feedback
    # ----------------------------------------------------------
    def update(self, dt, w, h, dfactor):
        self._maybe_spawn(w, h, dfactor)
        for word in self.words:
            word.update(dt)

        # ta bort ord som fallit utanför eller är klara
        kvar = []
        for word in self.words:
            if not word.done():
                kvar.append(word)
        self.words = kvar

        if self.fb_timer > 0:
            self.fb_timer -= dt

    # ----------------------------------------------------------
    # ritar hela HUD:en ovanpå kamerabilden
    # lager: ord → toppanel → quest/poäng/avstånd → feedback → bottompanel
    # ----------------------------------------------------------
    def draw_hud(self, frame, dfactor):
        h, w = frame.shape[:2]

        # rita alla fallande ord
        for word in self.words:
            word.draw(frame, self.quest)

        # mörk toppanel
        draw_panel(frame, 0, 0, w, 68)
        quest_col = TYPE_COLOR.get(self.quest, (255, 255, 100))
        draw_text(frame, "CATCH: " + self.quest, (w // 2 - 150, 50), 1.1, quest_col, stroke=4)
        draw_text(frame, "Score: " + str(self.score), (w - 200, 48), 0.9, (255, 255, 255), stroke=2)

        # avståndsstatus till vänster
        if dfactor > 1.35:
            dist_str, dist_col = "CLOSE >> step back!", (60, 60, 255)
        elif dfactor < 0.72:
            dist_str, dist_col = "FAR << step closer", (255, 165, 60)
        else:
            dist_str, dist_col = "Good distance", (60, 220, 60)
        draw_text(frame, dist_str, (16, 48), 0.52, dist_col, stroke=2)

        # feedbacktext med fade-effekt (timern används som alpha)
        if self.fb_timer > 0 and self.fb_text:
            fade = min(1.0, self.fb_timer)
            col  = (int(self.fb_color[0] * fade), int(self.fb_color[1] * fade), int(self.fb_color[2] * fade))
            draw_text(frame, self.fb_text, (w // 2 - 280, h // 2 + 50), 0.9, col, stroke=3)

        # mörk bottompanel med kontrollhints
        draw_panel(frame, 0, h - 30, w, h, alpha=0.55)
        draw_text(frame, "Catch with hands / elbows / feet  |  Q = quit  |  R = restart",
                  (14, h - 10), 0.42, (190, 190, 190), stroke=2)
