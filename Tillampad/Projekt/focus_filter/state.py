# ============================================================
# File        : state.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Gesthantering och filterstatus för Focus Filter.
#               Tolkar handdata och uppdaterar rutan och blur-nivån.
#
# Tre gestlägen:
#   TRANSLATE : 1 finger (pekfinger) → flytta rutan
#   SCROLL    : 2 fingrar (en hand)  → ändra blur-nivå
#   RESIZE    : 1 finger per hand    → ändra rutans storlek
# ============================================================

from config import RESIZE_HOLD_FRAMES


# ============================================================
# GestureState – hanterar filterrutan och blur-nivån
# main.py anropar update(hands_data, h) varje frame
# ============================================================
class GestureState:

    # ----------------------------------------------------------
    # box sätts till None och initieras av main.py vid första frame
    # när skärmdimensionerna är kända
    # ----------------------------------------------------------
    def __init__(self):
        self.box               = None   # [x1, y1, x2, y2]
        self.blur_level        = 0.0    # -1 till 1, 0 = ingen effekt
        self._translate_anchor = None   # offset fingret → rutans centrum
        self._resize_streak    = 0      # antal frames resize-gesten hållits

    # ----------------------------------------------------------
    # sätter startrutan till en tredjedel av skärmen, centrerat
    # anropas av main.py vid första frame
    # ----------------------------------------------------------
    def init_box(self, w, h):
        bw = w // 3
        bh = int(h * 0.45)
        self.box = [
            w // 2 - bw // 2,
            h // 2 - bh // 2,
            w // 2 + bw // 2,
            h // 2 + bh // 2,
        ]

    # ----------------------------------------------------------
    # tolkar gestdata och uppdaterar box och blur_level
    # prioriteringsordning: resize → scroll → translate → ingenting
    # returnerar (show_ruler, show_coords) för renderer.py
    # ----------------------------------------------------------
    def update(self, hands_data, h):
        show_ruler  = False
        show_coords = False

        # kolla om det är resize-gest (1 finger per hand, 2 händer)
        two_hand_resize = (
            len(hands_data) == 2
            and hands_data[0]["idx_ext"] and not hands_data[0]["mid_ext"]
            and hands_data[1]["idx_ext"] and not hands_data[1]["mid_ext"]
        )

        if two_hand_resize:
            self._resize_streak += 1
        else:
            self._resize_streak = 0

        if two_hand_resize and self._resize_streak >= RESIZE_HOLD_FRAMES:
            self._apply_resize(hands_data)
            show_coords = True

        elif len(hands_data) == 1:
            hd = hands_data[0]
            if hd["idx_ext"] and hd["mid_ext"]:
                self._apply_scroll(hd, h)   # 2 fingrar = blur-kontroll
                show_ruler = True
            elif hd["idx_ext"]:
                self._apply_translate(hd)   # 1 finger = flytta rutan
            else:
                self._translate_anchor = None
        else:
            self._translate_anchor = None

        return show_ruler, show_coords

    # ----------------------------------------------------------
    # sätter rutans hörn till de två fingertopparnas positioner
    # tar yttersta koordinaterna så rutan alltid omsluter båda fingrarna
    # ----------------------------------------------------------
    def _apply_resize(self, hands_data):
        ax, ay = hands_data[0]["idx"]
        bx, by = hands_data[1]["idx"]
        self.box = [min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)]
        self._translate_anchor = None

    # ----------------------------------------------------------
    # mappar fingrarnas vertikala position till blur_level
    # toppen = -1.0 (insidan pixeleras), botten = +1.0 (utsidan)
    # direktmappning är mer intuitiv än delta-baserad kontroll
    # ----------------------------------------------------------
    def _apply_scroll(self, hd, h):
        avg_y  = (hd["idx"][1] + hd["mid"][1]) / 2
        margin = h * 0.1
        span   = h - 2 * margin
        norm   = (avg_y - margin) / span   # 0 (topp) till 1 (botten)
        self.blur_level = max(-1.0, min(1.0, norm * 2 - 1))
        self._translate_anchor = None

    # ----------------------------------------------------------
    # flyttar rutan med fingret, håller samma offset som vid gestens start
    # translate_anchor sparas vid start → naturlig gripliknande rörelse
    # ----------------------------------------------------------
    def _apply_translate(self, hd):
        box    = self.box
        bw     = box[2] - box[0]
        bh     = box[3] - box[1]
        ix, iy = hd["idx"]

        if self._translate_anchor is None:
            cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            self._translate_anchor = (ix - cx, iy - cy)

        ox, oy = self._translate_anchor
        ncx    = ix - ox
        ncy    = iy - oy
        self.box = [ncx - bw // 2, ncy - bh // 2, ncx + bw // 2, ncy + bh // 2]

    # ----------------------------------------------------------
    # klampar rutan innanför skärmens kanter
    # krymper rutan om den är större än skärmen
    # ----------------------------------------------------------
    def clamp_box(self, w, h):
        box = self.box
        bw  = min(box[2] - box[0], w)
        bh  = min(box[3] - box[1], h)
        box[2] = box[0] + bw
        box[3] = box[1] + bh
        if box[0] < 0:
            box[0], box[2] = 0, bw
        if box[1] < 0:
            box[1], box[3] = 0, bh
        if box[2] > w:
            box[2], box[0] = w, w - bw
        if box[3] > h:
            box[3], box[1] = h, h - bh
