# ============================================================
# File        : renderer.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : All OpenCV-ritning för Focus Filter.
#               Modulen har inga sidoeffekter på spelstatus –
#               den tar emot data och ritar, inget mer.
# ============================================================

import cv2
import numpy as np


# ------------------------------------------------------------
# pixelerar en bild genom att krympa och förstora med INTER_NEAREST
# ger karaktäristisk pixelering utan blur
# strength 0 = ingen effekt, 1 = max pixelering
# ------------------------------------------------------------
def pixelate(img, strength):
    if strength <= 0.02:
        return img
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return img
    blocks = max(4, int(80 - strength * 75))  # färre block = grövre pixelering
    small  = cv2.resize(img, (blocks, max(1, int(blocks * h / w))), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


# ------------------------------------------------------------
# applicerar pixelering på rätt del av bilden beroende på blur_level
# blur_level > 0 = utsidan pixeleras (insidan är fokusrutan)
# blur_level < 0 = insidan pixeleras (utsidan är fokus)
# ------------------------------------------------------------
def render_frame(frame, box, blur_level):
    x1, y1, x2, y2 = box
    inside  = max(0.0,  blur_level)
    outside = max(0.0, -blur_level)

    if outside > 0.02:
        output = pixelate(frame, outside)
        if inside > 0.02:
            output[y1:y2, x1:x2] = pixelate(frame[y1:y2, x1:x2], inside)
        else:
            output[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
    else:
        if inside > 0.02:
            output = frame.copy()
            output[y1:y2, x1:x2] = pixelate(frame[y1:y2, x1:x2], inside)
        else:
            output = frame
    return output


# ------------------------------------------------------------
# ritar filterrutans kant och hörnmarkörer
# tunna vita linjer + cirklar i hörnen syns mot alla bakgrunder
# ------------------------------------------------------------
def draw_box(output, box):
    x1, y1, x2, y2 = box
    cv2.rectangle(output, (x1, y1), (x2, y2), (255, 255, 255), 1)
    for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
        cv2.circle(output, (cx, cy), 7, (0, 0, 0), 2)       # svart kant
        cv2.circle(output, (cx, cy), 5, (255, 255, 255), -1) # vit kärna


# ------------------------------------------------------------
# ritar vita punkter på utsträckta fingertoppar
# visuell feedback att gesten detekterats korrekt
# ------------------------------------------------------------
def draw_fingertips(output, hands_data):
    for hd in hands_data:
        if hd["idx_ext"]:
            cv2.circle(output, hd["idx"], 9, (0, 0, 0), 2)
            cv2.circle(output, hd["idx"], 5, (255, 255, 255), -1)
        if hd["mid_ext"]:
            cv2.circle(output, hd["mid"], 9, (0, 0, 0), 2)
            cv2.circle(output, hd["mid"], 5, (255, 255, 255), -1)


# ------------------------------------------------------------
# hjälpfunktion som väljer färg och text för status-pillret
# grön = svag effekt, gul = medium, röd = stark
# ------------------------------------------------------------
def _status_info(level):
    def color_text(mag, label):
        pct  = int(mag * 100)
        text = label + " " + str(pct) + "%"
        if mag < 0.33:
            return (80, 220, 80),  text   # grön
        elif mag < 0.66:
            return (40, 220, 240), text   # gul
        else:
            return (60, 60, 240),  text   # röd

    if level > 0.05:
        return color_text(level, "BLUR")
    if level < -0.05:
        return color_text(-level, "FOCUS")
    return (80, 220, 80), "NEUTRAL"


# ------------------------------------------------------------
# hjälpfunktion för att rita rundade rektanglar
# kombinerar rektanglar och ellipsbågar för hörnen
# ------------------------------------------------------------
def rounded_rect(img, p1, p2, color, radius=12, thickness=-1):
    x1, y1 = p1
    x2, y2 = p2
    if thickness < 0:
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    else:
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90,  0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0,   0, 90, color, thickness)


# ------------------------------------------------------------
# ritar vertikal linjal med rörlig markör och status-pill
# visas till vänster i bild under scroll-gesten
# markörens position speglar blur_level direkt
# ------------------------------------------------------------
def draw_ruler(img, level):
    h   = img.shape[0]
    rx  = 55
    top = int(h * 0.18)
    bot = int(h * 0.82)
    mid = (top + bot) // 2

    # linjalen
    cv2.line(img, (rx, top), (rx, bot), (255, 255, 255), 2)
    cv2.line(img, (rx - 12, top), (rx + 12, top), (255, 255, 255), 2)
    cv2.line(img, (rx - 12, bot), (rx + 12, bot), (255, 255, 255), 2)
    cv2.line(img, (rx - 8,  mid), (rx + 8,  mid), (255, 255, 255), 1)
    for i in range(1, 10):
        ty = top + (bot - top) * i // 10
        tw = 9 if i % 5 == 0 else 6
        cv2.line(img, (rx - tw, ty), (rx + tw, ty), (255, 255, 255), 1)

    # rörlig markör
    marker_y = int(mid + level * (bot - top) / 2)
    cv2.circle(img, (rx, marker_y), 12, (0, 0, 0), -1)
    cv2.circle(img, (rx, marker_y), 9,  (255, 255, 255), -1)

    # status-pill bredvid markören
    color, text = _status_info(level)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    pad  = 10
    bx1  = rx + 22
    by1  = marker_y - th // 2 - pad
    bx2  = bx1 + tw + 2 * pad
    by2  = marker_y + th // 2 + pad
    rounded_rect(img, (bx1, by1), (bx2, by2), color,          radius=14, thickness=-1)
    rounded_rect(img, (bx1, by1), (bx2, by2), (255, 255, 255), radius=14, thickness=1)
    cv2.putText(img, text, (bx1 + pad, marker_y + th // 2 - 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)


# ------------------------------------------------------------
# ritar koordinatetikett bredvid ett finger vid resize-gesten
# visar normaliserade x/y-koordinater (0.0–1.0)
# ------------------------------------------------------------
def draw_coord_label(img, point, nx, ny):
    text = "x:" + str(round(nx, 2)) + "  y:" + str(round(ny, 2))
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    pad  = 8
    px, py = point
    bx1  = px + 14
    by1  = py - th // 2 - pad
    bx2  = bx1 + tw + 2 * pad
    by2  = py + th // 2 + pad
    rounded_rect(img, (bx1, by1), (bx2, by2), (0, 0, 0),          radius=10, thickness=-1)
    rounded_rect(img, (bx1, by1), (bx2, by2), (255, 255, 255),     radius=10, thickness=1)
    cv2.putText(img, text, (bx1 + pad, py + th // 2 - 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
