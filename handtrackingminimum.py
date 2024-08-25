import cv2
import mediapipe as mp
import time

class HandTracker:
    def __init__(self, mode=False, maxHands=2, detectioncon=0.5, trackcon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectioncon = detectioncon
        self.trackcon = trackcon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, 
                                        min_detection_confidence=self.detectioncon, 
                                        min_tracking_confidence=self.trackcon)
        self.mpDraw = mp.solutions.drawing_utils
        
    def track_hands(self, img, draw=True):
        imgRgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRgb)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        LmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            h, w, c = img.shape
            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                LmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)
        return LmList

def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(0)
    detector = HandTracker()

    while True:
        success, img = cap.read()
        img = detector.track_hands(img)
        LmList = detector.findPosition(img)
        if len(LmList) != 0:
            print(LmList[4])
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv2.imshow('image', img)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()
