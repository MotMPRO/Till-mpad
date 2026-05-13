# ============================================================
# File        : main.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Startpunkt för Focus Filter.
#               Öppnar kameran, detekterar händer och
#               uppdaterar filtret varje frame.
#
# Gester:
#   1 finger (pekfinger)          = flytta rutan
#   2 fingrar (pekfinger + lång)  = justera blur-nivå
#   1 finger per hand (2 händer)  = ändra storlek på rutan
#
# Controls    : Q = avsluta
# ============================================================

import cv2

from config import CAM_FPS, CAM_HEIGHT, CAM_WIDTH, WINDOW_NAME
from hands import HandDetector
from renderer import draw_box, draw_coord_label, draw_fingertips, draw_ruler, render_frame
from state import GestureState


# ------------------------------------------------------------
# öppnar webbkameran med rätt inställningar
# ------------------------------------------------------------
def open_camera():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
    if not cap.isOpened():
        print("[ERROR] Kunde inte öppna kameran")
        raise SystemExit(1)
    return cap


# ------------------------------------------------------------
# kör huvudloopen tills Q trycks
# initialized-flaggan säkerställer att box-positionen sätts
# en gång när vi faktiskt vet skärmdimensionerna
# ------------------------------------------------------------
def run_loop(cap, detector, state):
    initialized = False

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        frame = cv2.flip(frame, 1)  # spegla bilden
        h, w  = frame.shape[:2]

        # initiera rutan vid första frame (dimensioner nu kända)
        if not initialized:
            state.init_box(w, h)
            initialized = True

        # detektera händer
        hands_data = detector.detect(frame)

        # uppdatera gestlogik
        show_ruler, show_coords = state.update(hands_data, h)
        state.clamp_box(w, h)

        # applicera pixelering
        output = render_frame(frame, state.box, state.blur_level)

        # rita rutan och fingertoppar (alltid synliga)
        draw_box(output, state.box)
        draw_fingertips(output, hands_data)

        # kontextuella UI-element beroende på aktiv gest
        if show_ruler:
            draw_ruler(output, state.blur_level)
        if show_coords:
            for hd in hands_data:
                if hd["idx_ext"]:
                    draw_coord_label(output, hd["idx"], hd["idx_n"][0], hd["idx_n"][1])

        cv2.imshow(WINDOW_NAME, output)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


# ------------------------------------------------------------
# initierar alla komponenter och startar filtret
# try/finally garanterar att resurser frigörs även vid krasch
# ------------------------------------------------------------
def main():
    cap      = open_camera()
    detector = HandDetector()
    state    = GestureState()

    print("[INFO] Focus Filter startar – Q = avsluta")
    print("[INFO] 1 finger = flytta | 2 fingrar = blur | 2 händer = resize")

    try:
        run_loop(cap, detector, state)
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Avslutad")


if __name__ == "__main__":
    main()
