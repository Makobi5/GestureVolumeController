import numpy as np
import time
import cv2
import handtrackingminimum as htm
import math
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import logging

class HandControlManager:
    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Camera and hand tracking setup
        self.wcam, self.hcam = 648, 488
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.wcam)
        self.cap.set(4, self.hcam)
        self.detector = htm.HandTracker(detectioncon=0.7)

        # Volume setup
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)
            volrange = self.volume.GetVolumeRange()
            self.minVol, self.maxVol = volrange[0], volrange[1]
        except Exception as e:
            self.logger.error(f"Volume setup error: {e}")
            self.volume = None

        # Smoothing variables
        self.prev_volume = 0
        self.prev_brightness = 0
        self.smoothing_factor = 0.2

    def smooth_value(self, current, previous, factor=0.2):
        """Apply exponential smoothing to reduce jitter."""
        return previous + factor * (current - previous)

    def control_volume(self, lmList):
        """Control system volume based on hand gesture."""
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)
        
        # Smoothed volume calculation
        vol = np.interp(length, [20, 120], [self.minVol, self.maxVol])
        smoothed_vol = self.smooth_value(vol, self.prev_volume, self.smoothing_factor)
        
        volBar = np.interp(length, [20, 120], [400, 150])
        volPer = np.interp(length, [20, 120], [0, 100])

        try:
            self.volume.SetMasterVolumeLevel(smoothed_vol, None)
            self.prev_volume = smoothed_vol
        except Exception as e:
            self.logger.error(f"Volume control error: {e}")

        return cx, cy, volBar, volPer

    def control_brightness(self, lmList):
        """Control screen brightness based on hand gesture."""
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)
        
        # Smoothed brightness calculation
        brightness = np.interp(length, [20, 120], [0, 100])
        smoothed_brightness = self.smooth_value(brightness, self.prev_brightness, self.smoothing_factor)
        
        brightBar = np.interp(length, [20, 120], [400, 150])

        try:
            sbc.set_brightness(smoothed_brightness)
            self.prev_brightness = smoothed_brightness
        except Exception as e:
            self.logger.error(f"Brightness control error: {e}")

        return cx, cy, brightBar, brightness

    def run(self):
        """Main control loop."""
        pTime = 0
        instruction_timeout = 300  # Show instructions for 5 seconds
        show_instructions = True
        instructions_start_time = time.time()

        while True:
            success, img = self.cap.read()
            img = self.detector.track_hands(img)
            lmList = self.detector.findPosition(img, draw=False)

            # Show instructions
            if show_instructions and time.time() - instructions_start_time < instruction_timeout:
                cv2.putText(img, "Right Hand: Volume", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(img, "Left Hand: Brightness", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                show_instructions = False

            if len(lmList) != 0:
                hand_side = "Left" if lmList[0][1] > self.wcam // 2 else "Right"

                if hand_side == "Right" and self.volume:
                    cx, cy, volBar, volPer = self.control_volume(lmList)
                    
                    # Volume bar and percentage
                    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
                    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

                elif hand_side == "Left":
                    cx, cy, brightBar, brightness = self.control_brightness(lmList)
                    
                    # Brightness bar and percentage
                    cv2.rectangle(img, (self.wcam - 85, 150), (self.wcam - 50, 400), (0, 255, 0), 3)
                    cv2.rectangle(img, (self.wcam - 85, int(brightBar)), (self.wcam - 50, 400), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, f'{int(brightness)} %', (self.wcam - 100, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

            # FPS calculation
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

            # Show the image
            cv2.imshow('Brightness and Volume Control', img)
            
            # Exit conditions
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord('r'):  # Reset to default
                try:
                    sbc.set_brightness(50)
                    self.volume.SetMasterVolumeLevel(-20, None)
                except Exception as e:
                    self.logger.error(f"Reset error: {e}")

        self.cap.release()
        cv2.destroyAllWindows()

def main():
    controller = HandControlManager()
    controller.run()

if __name__ == "__main__":
    main()