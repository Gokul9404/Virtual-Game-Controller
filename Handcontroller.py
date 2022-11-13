from math import hypot
from mediapipe import solutions
from cv2 import line, circle, cvtColor, flip, FILLED, COLOR_BGR2RGB
import cv2
import numpy as np


#================================================================================
class Hand_Controller:
    def __init__(self,mode=False,max_hands=1,detection_con=0.7,track_confidence=0.5):
        """Used to detect the Hand position, it's Finger-Up state ,and \n To draw the Landmarks of the hand """
        self.mpHands = solutions.hands
        self.hands = self.mpHands.Hands(mode,max_hands,1,detection_con,track_confidence)
        self.mpdraw = solutions.drawing_utils
        
        self.fingerup_list, self.lm_list = [], []
        self.tip_id = [4,8,12,16,20]
        self.close_tip_id = [5,6,10,14,18]
        self.hand_side = None

    def findhand(self,img,draw=False,fliped_img=True):
        #=== Getting the image in BGR format ====================================
        #=== Then flipping the image for better understanding ===================
        self.fliped_img = fliped_img
        RGBimg = cvtColor(img,COLOR_BGR2RGB)
        if self.fliped_img:
            self.img = img  
        else:
            self.img =  flip(img,1)
            RGBimg = flip(RGBimg,1)
        #=== Processing the Hand position and ===================================
        self.result = self.hands.process(RGBimg)
        #=== Drawing the Landmarks of the Hand, if given draw ===================
        if self.result.multi_hand_landmarks:        
            for handlms in self.result.multi_hand_landmarks:
                if draw:
                    self.mpdraw.draw_landmarks(img,handlms,self.mpHands.HAND_CONNECTIONS)
        return img
    
    def findPosition(self,handno=0):
        lm_list = [ ]
        if self.result.multi_hand_landmarks:    
            given_hand = self.result.multi_hand_landmarks[handno]
            for id, lm in enumerate(given_hand.landmark):
                    h ,w , c = self.img.shape
                    cx, cy = int(lm.x*w),int(lm.y*h)
                    lm_list.append([id,cx,cy])
        self.lm_list = lm_list
        return lm_list

    def fingersUp(self):
        self.fingerup_list = []
        if len(self.lm_list) != 0:
            #==== Checking whther left hand or right hand =======================
            #==== And then determining the Thumb state:- Open or Close ==========
            if self.lm_list[0][1] > self.lm_list[1][1]:
                self.hand_side = 'right'
                if self.lm_list[self.tip_id[0]][1] < self.lm_list[self.close_tip_id[0]][1]  :
                    self.fingerup_list.append(1)
                else: self.fingerup_list.append(0)
            else :
                self.hand_side = 'left'
                if self.lm_list[self.tip_id[0]][1] > self.lm_list[self.close_tip_id[0]][1]  :
                    self.fingerup_list.append(1)
                else: self.fingerup_list.append(0)
            #==== Checking the state of the Fingers:- Open or Close =============
            for id in range(1,5):
                if self.lm_list[self.tip_id[id]][2] < self.lm_list[self.close_tip_id[id]][2]:
                    self.fingerup_list.append(1)
                else: self.fingerup_list.append(0)
            #====================================================================
        return self.fingerup_list
    
    def findDistance(self,img,F1,F2,draw_f=True,draw_line=True,draw_cntr=False,finger_up=True):
        f1 = self.tip_id[F1]
        f2 = self.tip_id[F2]
        distance = 0
        cx, cy = 0 ,0
        def find():
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
        if self.lm_list and self.fingerup_list:
            if finger_up:
                if (self.fingerup_list[F1] == self.fingerup_list[F2] == 1):
                    distance, (cx, cy) = find()
                else:
                    pass 
            else:
                distance = find()
            return [distance , (cx, cy)]