from math import hypot
from mediapipe import solutions
from cv2 import line, circle, cvtColor, flip, FILLED, COLOR_BGR2RGB
import cv2
import numpy as np


class Hand_Controller:
    def __init__(self,mode=False,max_hands=1,detection_con=0.7,track_confidence=0.5):
        """
        Args:
            max_hands (int):        Defaults to 1.
                Represents the maximum no. of handes to detect in a frame at a time.
            detection_con (float):  Defaults to 0.7.
                Confidence in the detection of hande with-in the frame 
            track_confidence (float):Defaults to 0.6.
                Confidence of detecting the hand-movement between frame, i.e. Confidence to detecrmined the track change of hand.
        Custom-Class made to get the Hand-gesture , position, and state of each finger
        """
        self.mpHands = solutions.hands
        self.max_hand = max_hands
        self.hands = self.mpHands.Hands(mode,max_hands,1,detection_con,track_confidence)
        self.mpdraw = solutions.drawing_utils
        
        self.fingerup_list = np.array([])
        self.lm_list = []    
        self.tip_id = [4,8,12,16,20]
        self.close_tip_id = [5,6,10,14,18]
        self.hand_side = None

    def findhand(self,img,draw=False,fliped_img=True):
        """Method used to find hands with in the given frame/image

        Args:
            img     : Image onto which hands are needed to be find
            draw (bool): Need to draw hand landmarks. Defaults to False.
            fliped_img (bool): Image passed as agrgument is Flipped or not. Defaults to True.

        Returns:
            cv2-image: image onto which landmarks ar drawn
        """
        #=== Getting the image in BGR format ====================================
        #=== Then flipping the image for better understanding ===================
        self.fliped_img = fliped_img
        RGBimg = cvtColor(img,cv2.COLOR_BGR2RGB)
        if self.fliped_img:
            self.img = img  
        else:
            self.img =  flip(img,1)
            RGBimg = flip(RGBimg,1)
        #=== Processing the Hand position and ===================================
        self.result = self.hands.process(RGBimg)
        #=== Drawing the Landmarks of the Hand, if given draw ===================
        lm_list = []       
        if self.result.multi_hand_landmarks: 
            for handlms in self.result.multi_hand_landmarks:
                if draw:
                    self.mpdraw.draw_landmarks(img,handlms,self.mpHands.HAND_CONNECTIONS)
                if self.max_hand == 1:
                    given_hand = self.result.multi_hand_landmarks[0]
                    for id, lm in enumerate(given_hand.landmark):
                        h ,w , _ = self.img.shape
                        cx, cy = int(lm.x*w),int(lm.y*h)
                        lm_list.append([id,cx,cy])
        self.lm_list = lm_list
        return img
    
    def findPosition(self,handno=0):
        """
        Method used to find the postion of hand lanmarks in the image

        Args:
            handno (int) : If here are multi hands, select a specific hand to find it's landmark position. Defaults to 0.

        Returns:
            lm_list : list of coordinates of each handlandmarks in the image along with there landmark id.
        """
        if handno == 0:
            return self.lm_list
        
        lm_list = []
        if self.result.multi_hand_landmarks:    
            given_hand = self.result.multi_hand_landmarks[handno]
            for id, lm in enumerate(given_hand.landmark):
                h ,w , _ = self.img.shape
                cx, cy = int(lm.x*w),int(lm.y*h)
                lm_list.append([id,cx,cy])
        self.lm_list = lm_list
        return self.lm_list

    def fingersUp(self):
        """
        Method used to find whether the finges and thum are open or closed

        Returns:
            fingerup_list : list of states of each finger in the hand
        """
        self.fingerup_list = np.array([])
        if self.lm_list:
            #==== Checking whther left hand or right hand =======================
            #==== And then determining the Thumb state:- Open or Close ==========
            if self.lm_list[0][1] > self.lm_list[1][1]:
                self.hand_side = 'right'
                if self.lm_list[self.tip_id[0]][1] < self.lm_list[self.close_tip_id[0]][1]  :
                    self.fingerup_list = np.append(self.fingerup_list,[1])
                else: 
                    # self.fingerup_list.append(0)
                    self.fingerup_list = np.append(self.fingerup_list,[0])
            else :
                self.hand_side = 'left'
                if self.lm_list[self.tip_id[0]][1] > self.lm_list[self.close_tip_id[0]][1]  :
                    self.fingerup_list = np.append(self.fingerup_list,[1])
                else: 
                    self.fingerup_list = np.append(self.fingerup_list,[0])
            #==== Checking the state of the Fingers:- Open or Close =============
            for id in range(1,5):
                if self.lm_list[self.tip_id[id]][2] < self.lm_list[self.close_tip_id[id]][2]:
                    self.fingerup_list =  np.append(self.fingerup_list,[1])
                else: 
                    self.fingerup_list = np.append(self.fingerup_list,[0])
                #====================================================================
        return self.fingerup_list
        
    def findDistance(self,img,F1,F2,draw_f=True,draw_line=True,draw_cntr=False,finger_up=True):
        """
        Args:
            img : image onto which landmarks are to be drawn
            F1  : Finger 1 id no.
            F2  : Finger 2 id no.
            draw_f (bool)   : Do fingers are needed to be highlighted or not. Defaults to True.
            draw_line (bool): Is there any need of line conecting fingers to be highlighted or not. Defaults to True.
            draw_cntr (bool): Do centre point is needed to be highlighted or not. Defaults to False.
            finger_up (bool): Finger state. Defaults to True.

        Returns:
            distance        : distance btw the two fingers
            tuple (cx, cy)  : center point btw the fingers
        """
        f1 = self.tip_id[F1]
        f2 = self.tip_id[F2]
        distance = 0
        cx, cy = 0 ,0

        def find():
            """Used to find the distance btw the two fingers and draw the connecting lines btw the finger

            Returns:
                dis             : distance btw the fingers
                tuple (cx, cy)  : center point btw the fingers
            """
            f1_x,f1_y = self.lm_list[f1][1:]
            f2_x,f2_y = self.lm_list[f2][1:]
            cx,cy = (f1_x+f2_x)//2, (f1_y+f2_y)//2 
            if draw_line:
                line(img,(f1_x,f1_y),(f2_x,f2_y),(61,90,128),4)
            if draw_f:
                circle(img,(f1_x,f1_y),10,(0,29,62),FILLED)
                circle(img,(f1_x,f1_y),7,(0,53,102),FILLED)
                circle(img,(f2_x,f2_y),10,(0,29,62),FILLED)
                circle(img,(f2_x,f2_y),7,(0,53,102),FILLED)
            if draw_cntr:
                circle(img,(cx,cy),8,(224,251,252),FILLED)
            dis = hypot(f2_x - f1_x,f2_y - f1_y)
            return dis, (cx, cy)
        
        if (self.lm_list != []) and (self.fingerup_list.size != 0):
            if finger_up:
                if (self.fingerup_list[F1] == self.fingerup_list[F2] == 1):
                    distance, (cx, cy) = find()
                else:
                    pass 
            else:
                distance = find()
            return [distance , (cx, cy)]