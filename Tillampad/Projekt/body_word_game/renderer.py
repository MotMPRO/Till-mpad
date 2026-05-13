# ============================================================
# File        : renderer.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : All OpenCV-ritning för Body Word Game.
#               Modulen vet ingenting om spellogik – den tar
#               emot data och ritar, inget mer.
# ============================================================

import cv2
import mediapipe as mp
import numpy as np

from config import (
    BONE_COLOR, BONE_THICKNESS, JOINT_R,
    CATCH_LM_IDS, BASE_CATCH_RADIUS,
    TYPE_COLOR, FONT,
)

_pose = mp.solutions.pose


# ------------------------------------------------------------
# ritar text med svart kontur så den syns mot alla bakgrunder
# första putText = tjock svart skugga, andra = färgad text ovanpå
# ------------------------------------------------------------
def draw_text(frame, text, pos, scale, color, stroke=3):
    thick = max(1, int(scale * 2))
    cv2.putText(frame, text, pos, FONT, scale, (0, 0, 0), thick + stroke, cv2.LINE_AA)  # kontur
    cv2.putText(frame, text, pos, FONT, scale, color, thick, cv2.LINE_AA)               # text


# ------------------------------------------------------------
# ritar en halvtransparent svart panel, används för HUD-banden
# arbetar direkt på ROI-slicen för att slippa kopiera hela bilden
# ------------------------------------------------------------
def draw_panel(frame, x1, y1, x2, y2, alpha=0.6):
    roi = frame[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
    if roi.size == 0:
        return
    dark = np.zeros_like(roi)
    cv2.addWeighted(dark, alpha, roi, 1 - alpha, 0, dst=roi)


# ------------------------------------------------------------
# ritar spelarens skelett (ben, leder, fångstcirklar) på bilden
# fångstpunkter markeras med en cyan ring som visuell feedback
# ------------------------------------------------------------
def draw_skeleton(frame, landmarks, w, h):
    lm = landmarks.landmark

    # rita linjer mellan alla anslutna landmärken
    for a_id, b_id in _pose.POSE_CONNECTIONS:
        a, b = lm[a_id], lm[b_id]
        if a.visibility < 0.35 or b.visibility < 0.35:
            continue
        ax, ay = int(a.x * w), int(a.y * h)
        bx, by = int(b.x * w), int(b.y * h)
        cv2.line(frame, (ax, ay), (bx, by), (0, 0, 0), BONE_THICKNESS + 3, cv2.LINE_AA)  # kontur
        cv2.line(frame, (ax, ay), (bx, by), BONE_COLOR, BONE_THICKNESS, cv2.LINE_AA)      # linje

    # rita en cirkel vid varje synlig led
    for pt in lm:
        if pt.visibility < 0.35:
            continue
        px, py = int(pt.x * w), int(pt.y * h)
        cv2.circle(frame, (px, py), JOINT_R + 2, (0, 0, 0), -1, cv2.LINE_AA)          # svart kant
        cv2.circle(frame, (px, py), JOINT_R, (255, 255, 255), -1, cv2.LINE_AA)         # vit kula

    # cyan ring på fångstpunkterna så spelaren vet var de är
    for lm_id in CATCH_LM_IDS:
        pt = lm[lm_id]
        if pt.visibility > 0.35:
            px, py = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (px, py), int(BASE_CATCH_RADIUS * 0.45), (0, 220, 255), 1, cv2.LINE_AA)


# ============================================================
# FallingWord – ett ord som faller nedåt och kan fångas
# game.py skapar och lagrar instanserna
# ============================================================
class FallingWord:

    # ----------------------------------------------------------
    # sätter startpositionen ovanför skärmen (y = -50)
    # så att ordet glider in naturligt utan att "poppa" fram
    # ----------------------------------------------------------
    def __init__(self, text, wtype, x, speed, scale, frame_h):
        self.text    = text
        self.wtype   = wtype
        self.x       = x
        self.y       = float(-50)  # startar ovanför skärmen
        self.speed   = speed
        self.scale   = scale
        self.frame_h = frame_h
        self.caught  = False
        self.flash   = 0.0         # sekunder kvar av fångst-animation

    # ----------------------------------------------------------
    # uppdaterar position och flash-timer en frame framåt
    # fångade ord slutar falla men flash-timern räknas ner
    # ----------------------------------------------------------
    def update(self, dt):
        if not self.caught:
            self.y += self.speed * dt
        if self.flash > 0:
            self.flash -= dt

    # ----------------------------------------------------------
    # returnerar True om ordet ska tas bort från listan
    # antingen har det fallit utanför skärmen eller är flash-animationen klar
    # ----------------------------------------------------------
    def done(self):
        return self.y > self.frame_h + 80 or (self.caught and self.flash <= 0)

    # ----------------------------------------------------------
    # ritar ordet på bilden
    # quest-ord: ljusa, större, grön glow-bakgrund
    # övriga ord: grå, mindre
    # fångade ord: grön flash-text ersätter normalvisningen
    # ----------------------------------------------------------
    def draw(self, frame, quest):
        x, y     = self.x, int(self.y)
        is_quest = (self.wtype == quest)
        col      = (255, 255, 255) if is_quest else (160, 160, 160)
        scale    = self.scale * (1.1 if is_quest else 0.82)

        # fångst-flash: byt ut hela ordet mot en grön bekräftelse
        if self.caught and self.flash > 0:
            draw_text(frame, "CAUGHT! " + self.text.upper(), (x - 60, y), scale * 1.25, (50, 255, 80), stroke=4)
            return

        # grön glow-rektangel bakom quest-ord
        # bugfix: använd samma tjocklek som draw_text för korrekt boxstorlek
        if is_quest:
            thick = max(1, int(scale * 2))
            (tw, th), _ = cv2.getTextSize(self.text, FONT, scale, thick + 3)
            pad = 7
            ov  = frame.copy()
            cv2.rectangle(ov, (x - pad, y - th - pad), (x + tw + pad, y + pad), (0, 50, 0), -1)
            cv2.addWeighted(ov, 0.4, frame, 0.6, 0, frame)

        # rita själva ordtexten
        draw_text(frame, self.text, (x, y), scale, col, stroke=3 if is_quest else 2)

        # liten ordklassetikett under ordet
        tc = TYPE_COLOR.get(self.wtype, (200, 200, 200))
        draw_text(frame, self.wtype, (x, y + 16), max(0.28, scale * 0.4), tc, stroke=2)
