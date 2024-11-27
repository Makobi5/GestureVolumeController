import numpy as np
import time
import cv2
import handtrackingminimum as htm
import math
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

def main():
    wcam, hcam = 648, 488
    cap = cv2.VideoCapture(0)
    cap.set(3, wcam)
    cap.set(4, hcam)
    pTime = 0

    # Hand detector
    detector = htm.HandTracker(detectioncon=0.7)

    # Volume setup
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volrange = volume.GetVolumeRange()
    minVol, maxVol = volrange[0], volrange[1]
    vol = 0
    volBar = 400
    volPer = 0

    while True:
        success, img = cap.read()
        img = detector.track_hands(img)
        lmList = detector.findPosition(img, draw=False)

        if len(lmList) != 0:
            # Determine which hand is detected (left or right)
            # MediaPipe hand landmarks are returned in order, so we can check the wrist x-coordinate
            hand_side = "Left" if lmList[0][1] > wcam // 2 else "Right"

            if hand_side == "Right":  # Volume control with right hand
                # Get positions of thumb and index finger tips
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                length = math.hypot(x2 - x1, y2 - y1)

                # Map the hand length to volume and volume bar height
                vol = np.interp(length, [20, 120], [minVol, maxVol])
                volBar = np.interp(length, [20, 120], [400, 150])
                volPer = np.interp(length, [20, 120], [0, 100])

                # Set the system volume based on hand gesture
                volume.SetMasterVolumeLevel(vol, None)

                # Change circle color when hand is in the minimum volume position
                if length < 20:
                    cv2.circle(img, (cx, cy), 8, (0, 255, 0), cv2.FILLED)

                # Draw the volume bar
                cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
                cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)

                # Display the volume percentage
                cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

            elif hand_side == "Left":  # Brightness control with left hand
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                length = math.hypot(x2 - x1, y2 - y1)

                # Map hand length to brightness (0-100%)
                brightness = np.interp(length, [20, 120], [0, 100])
                brightBar = np.interp(length, [20, 120], [400, 150])

                # Set screen brightness
                try:
                    sbc.set_brightness(brightness)
                except Exception as e:
                    print(f"Error setting brightness: {e}")

                # Draw brightness bar
                cv2.rectangle(img, (wcam - 85, 150), (wcam - 50, 400), (0, 255, 0), 3)
                cv2.rectangle(img, (wcam - 85, int(brightBar)), (wcam - 50, 400), (0, 255, 0), cv2.FILLED)

                # Display brightness percentage
                cv2.putText(img, f'{int(brightness)} %', (wcam - 100, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

        # Calculate and display FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

        # Show the image
        cv2.imshow('Brightness and Volume Control', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()