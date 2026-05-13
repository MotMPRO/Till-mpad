# ============================================================
# File        : main.py
# Author      : Amin Bachar
# Date        : 10 maj 2026
# Description : Startpunkt för Body Word Game.
#               Öppnar kameran, startar MediaPipe Pose
#               och kör huvudloopen.
# Controls    : Q = avsluta | R = starta om
# ============================================================

import time

import cv2
import mediapipe as mp

from config import CAM_FPS, CAM_HEIGHT, CAM_WIDTH, FONT
from game import Game, distance_factor
from renderer import draw_skeleton, draw_text


# ------------------------------------------------------------
# öppnar och konfigurerar webbkameran
# CAP_DSHOW och MJPG används för lägre latens på Windows
# ignoreras tyst på Linux/macOS
# ------------------------------------------------------------
def open_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)  # minska buffert för lägre latens
    if not cap.isOpened():
        print("[ERROR] Kunde inte öppna kameran")
        raise SystemExit(1)
    return cap


# ------------------------------------------------------------
# kör spelet tills spelaren trycker Q
# dt begränsas till 0.1s för att undvika hopp vid sega frames
# ------------------------------------------------------------
def run_loop(cap, game, pose):
    prev_time  = time.time()
    dfac       = 1.0
    read_fails = 0  # räknar på varandra följande kamerafel

    while True:
        ok, frame = cap.read()
        if not ok:
            # bugfix: bryt loopen vid ihållande kamerafel
            # undviker oändlig loop med 100% cpu om kameran kopplas ur
            read_fails += 1
            if read_fails > 30:
                print("[ERROR] Kameran svarar inte – avslutar")
                break
            continue
        read_fails = 0  # återställ räknaren vid lyckad läsning

        frame    = cv2.flip(frame, 1)  # spegla så det känns som en spegel
        h, w     = frame.shape[:2]
        now      = time.time()
        dt       = min(now - prev_time, 0.1)  # begränsa tidsdelta
        prev_time = now

        # mediapipe kräver RGB, opencv ger BGR
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = pose.process(rgb)

        if result.pose_landmarks:
            dfac = distance_factor(result.pose_landmarks)
            draw_skeleton(frame, result.pose_landmarks, w, h)
            game.check_catch(result.pose_landmarks, w, h, dfac)
        else:
            # ingen kropp hittad – visa meddelande
            draw_text(frame, "Stand in front of the camera – upper body must be visible",
                      (w // 2 - 370, h // 2), 0.72, (100, 200, 255), stroke=3)

        game.update(dt, w, h, dfac)
        game.draw_hud(frame, dfac)

        cv2.imshow("Body Word Game – Catch the right word class!", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("r"):
            game.reset()
            print("[INFO] Spelet startades om")


# ------------------------------------------------------------
# initierar alla komponenter och startar spelet
# ------------------------------------------------------------
def main():
    cap  = open_camera()
    game = Game()

    with mp.solutions.pose.Pose(
        model_complexity         = 0,   # 0 = snabbast, tillräckligt exakt
        smooth_landmarks         = True,
        min_detection_confidence = 0.5,
        min_tracking_confidence  = 0.4,
    ) as pose:
        print("[INFO] Spelet startar – ställ dig framför kameran!")
        print("[INFO] Q = avsluta  |  R = starta om")
        run_loop(cap, game, pose)

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Spelet slut – slutpoäng: " + str(game.score))


if __name__ == "__main__":
    main()
