#===== Importing Required Modules ==========================================
from pyautogui import click, moveTo, size
from pynput.keyboard import Key, Controller
import cv2
import mediapipe as mp

from win32com.client import Dispatch

from math import hypot
from numpy import interp
from time import sleep
import time

from pygame import mixer
mixer.init()



keyboard = Controller()
#================================================================================
class Handdetector:
    def __init__(self,mode=False,max_hands=1,detection_con=0.7,track_confidence=0.5):
        """Used to detect the Hand position, it's Finger-Up state ,and \n To draw the Landmarks of the hand """
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_confidence = track_confidence
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode ,self.max_hands,self.detection_con,self.track_confidence)
        self.mpdraw = mp.solutions.drawing_utils
        
        self.fingerup_list, self.lm_list = [], []
        self.tip_id = [4,8,12,16,20]
        self.close_tip_id = [5,6,10,14,18]
        self.hand_side = None

    def findhand(self,img,draw=False,fliped_img=True):
        #=== Getting the image in BGR format ====================================
        #=== Then flipping the image for better understanding ===================
        self.fliped_img = fliped_img
        RGBimg = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        if self.fliped_img:
            self.img = img  
        else:
            self.img =  cv2.flip(img,1)
            RGBimg = cv2.flip(RGBimg,1)
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
                cv2.line(img,(f1_x,f1_y),(f2_x,f2_y),(61,90,128),4)
            if draw_f:
                cv2.circle(img,(f1_x,f1_y),10,(0,29,62),cv2.FILLED)
                cv2.circle(img,(f1_x,f1_y),7,(0,53,102),cv2.FILLED)
                cv2.circle(img,(f2_x,f2_y),10,(0,29,62),cv2.FILLED)
                cv2.circle(img,(f2_x,f2_y),7,(0,53,102),cv2.FILLED)
            if draw_cntr:
                cv2.circle(img,(cx,cy),8,(224,251,252),cv2.FILLED)

            dis = hypot(f2_x - f1_x,f2_y - f1_y)
            return dis, (cx, cy)
        if self.lm_list and self.fingerup_list:
            if finger_up:
                if (self.fingerup_list[F1] == self.fingerup_list[F2] == 1):
                    distance, (cx, cy) = find()
                else:
                    pass 
                    #print("Keep finger up")
            else:
                distance = find()
            return [distance , (cx, cy)]
#=============== Machine Voice ==================================================
voice_engine = Dispatch('SAPI.Spvoice')

def say(audio):
    """Used to Speak the text, given audio parameter"""
    voice_engine.Speak(audio)

say('Machine Voice connected')
#=============== Main Program ===================================================
def main():
    def check_in_fing(point_list=[0,0],box=0):
        """If finger is in box zero, it returns True; else False. \n
           If given box=1, then it returns the box_no on which the finger is."""
        if box==0:
            if start_x < point_list[0] < end_x and start_y < point_list[1] < hand_start_y:
                return True
            return False
        if box==1:
            if hand_start_x < point_list[0] < hand_end_x and hand_start_y < point_list[1] < hand_end_y:
                return True
            return False

        elif box==2:
            if start_x < point_list[0] < mid_x and start_y < point_list[1] < hand_start_y:
                return 1
            elif mid_x < point_list[0] < end_x and start_y < point_list[1] < hand_start_y:
                return 2
        return 0
    #===========================================================================
    def check_swipe_motion(finger_list=[]):
        """Returns the swipe done by the Hand-detected either in +ve direction['pos'] or -ve direction['neg']"""
        fing_len = len(finger_list)
        swipe = None
        if fing_len > 5:
            [x1, y1] = finger_list[0]
            [x2, y2] = finger_list[fing_len - 1]
            #===========================
            x = int(x2 - x1)
            y = int(y2 -y1)
            if x1 > x2: x *= -1
            if y1 > y2: y *= -1
            #===========================
            if x < 30 and y > 100:
                if y2 > y1 : swipe = 'pos'
                else: swipe = 'neg'
            #===========================
            # if x > 100 and y < 30:
            #     if x2 > x1 : swipe = 'right'
            #     else: swipe = 'left'
            return swipe
    #===========================================================================
    def Get_state_swipe(swipe):
        """Returns the state of the Swipe-gesture, and the swipe if fingers are in same box"""
        F1_box = check_in_fing(lm_list[8][1:],1)
        F2_box = check_in_fing(lm_list[12][1:],1)
        if F1_box == F2_box:
            state = 'Quit' if F1_box == 1 else  'To-do'
        else:
            state = 'Swipe'
        finger_pos_for_swipe.append(lm_list[12][1:])
        if len(finger_pos_for_swipe) > 30:
            finger_pos_for_swipe.pop(0)
        if state in ['Quit', 'To-do']:
            swipe = check_swipe_motion(finger_pos_for_swipe)
        return state, swipe
    #===========================================================================
    def mouse_pointer_click(centre, dis, Clicked):
        """Clicks the Pointer at it's place when Index & Middle Fingers are too close to each-other. \n
        Returns Clicked & state values."""
        cx,cy = centre
        Mouse_state = 0
        cv2.circle(Main_img,(cx,cy),15,(181,181,181),cv2.FILLED)   
        if Clicked >= 1: Clicked = 0

        if dis < 30:
            cv2.circle(Main_img,(cx,cy),15,(0,252,51),cv2.FILLED)
            if Clicked==0:
                Mouse_state = Clicked = 1
        elif dis > 55:
            Mouse_state = 0
        if Clicked == 1:
            Clicked += 1
        return Clicked, Mouse_state
    #===========================================================================
    say('Getting Hand dectector')
    Hand_detector = Handdetector()      # Creating hand-Detector 
    #===========================================================================
    V_dir, H_dir, Jump = 0, 0, 0
    Controller_Mode = -1
    #===========================================================================
    Thumb = Index_Finger = Middle_Finger = Ring_Finger = Pinky_Finger = 1
    sum_of_finger_state = 0
    finger_up_state = []
    finger_pos_for_swipe = []
    prev_time, cur_time  =  0, 0        # Creating time counter to get the fps
    Quit_confirm = False
    #===========================================================================
    #===========================================================================
    Font_type = cv2.FONT_HERSHEY_PLAIN
    Font_size = 1
    Font_color = (215,255,214)
    Font_thickness = 2
    #===========================================================================
    pointer_x, pointer_y = 0, 0
    Clicked = 0
    #===========================================================================
    start_x, start_y, end_x, end_y = 225, 50, 575, 400
    hand_start_x, hand_start_y, hand_end_x, hand_end_y = 225, 100, 575, 400
    mid_x = (start_x + end_x)//2
    scrn_width, scrn_height = size()
    #===========================================================================
    say('Getting Camera')
    cap = cv2.VideoCapture(0)           # Creating Camera object
    cam_width,cam_height = 640,480
    say('Camera connected')
    #==========================================================================
    while True:
        _ , cap_img = cap.read()
        cur_time = time.time()
        Main_img = cv2.flip(cap_img,1)
        #======================================================================
        swipe = ''
        state = ''
        Hand_Detection_check = False
        Main_img = Hand_detector.findhand(Main_img,True)
        lm_list = Hand_detector.findPosition()
        #======================================================================
        V_dir, H_dir, Jump = 0, 0, 0
        #======================================================================
        if lm_list:
            finger_up_state = Hand_detector.fingersUp()
            Hand_Detection_check = True
            #=============== Checking & Changing finger's State ===============
            if finger_up_state:
                Index_finger_button_in = check_in_fing(lm_list[8][1:])
                Middle_finger_button_in = check_in_fing(lm_list[12][1:])
                #==============================================================
                if Index_finger_button_in or Middle_finger_button_in:
                    Index_finger_button_in = check_in_fing(lm_list[8][1:],2)
                    Middle_finger_button_in = check_in_fing(lm_list[12][1:],2)
                    if Index_finger_button_in == Middle_finger_button_in:
                        z = 0
                        [dis , centre ]= Hand_detector.findDistance(Main_img,1,2)
                        if centre and dis:
                            Clicked, _ = mouse_pointer_click(centre,dis,Clicked)
                            if Clicked == 2: z = 1
                        if Index_finger_button_in == 1 and z == 1 :
                            state += " asdf"
                            Controller_Mode = 0
                            # print(state)
                        elif Index_finger_button_in == 2 and z == 1:
                            state += "arrow"
                            Controller_Mode = 1
                            # print(state)
                else:
                    #==========================================================
                    [Thumb,Index_Finger,Middle_Finger,Ring_Finger,Pinky_Finger] = finger_up_state
                    sum_of_finger_state = sum(finger_up_state[1:])
                    #==========================================================
                    Thumb_in = check_in_fing(lm_list[4][1:],1)
                    Index_finger_in = check_in_fing(lm_list[8][1:],1)
                    Middle_finger_in = check_in_fing(lm_list[12][1:],1)
                    Ring_Finger_in = check_in_fing(lm_list[16][1:],1)
                    Pinky_Finger_in = check_in_fing(lm_list[20][1:],1)
                    if sum_of_finger_state == 0:
                        if Thumb_in and not(Thumb):
                            state = state + "Jump "
                            Jump = 1
                    else:
                        # Create Direction Controlls
                        if Index_Finger and Index_finger_in:
                            if (not Middle_Finger):
                                state = state + "Up "
                                V_dir = 1
                            elif Middle_finger_in and Middle_Finger and not(Ring_Finger):
                                state = state + "Down "
                                V_dir = -1
                        if (Thumb and Thumb_in) and not(Pinky_Finger):
                            state = state + "Left "
                            H_dir = -1
                        elif (Pinky_Finger and Pinky_Finger_in) and not(Thumb):
                            state = state + "Right "
                            H_dir = 1
                    # print(H_dir, V_dir, Jump)

                    if Controller_Mode == 0:
                        if V_dir == 1:
                            px, py = lm_list[8][1:]                        
                            pointer_x = int(interp(px,(hand_start_x,end_x),(0,scrn_width)))
                            pointer_y = int(interp(py,(hand_start_y,end_y),(0,scrn_height)))
                            #==== Mouse Pointer Movement ==============================
                            state = "Mouse Pointer"
                            cv2.circle(Main_img,(px,py),5,(200,200,200),cv2.FILLED)
                            cv2.circle(Main_img,(px,py),10,(200,200,200),3)
                            moveTo(int(pointer_x),int(pointer_y))
                        else:
                            [dis , centre ]= Hand_detector.findDistance(Main_img,1,2)
                            if (sum_of_finger_state == 3) and (Index_Finger and Middle_Finger and Ring_Finger):
                                state = "Quit Check"
                                if centre and dis:
                                    Clicked, _ = mouse_pointer_click(centre,dis,Clicked)
                                    if Clicked == 2: Quit_confirm = True
                            elif V_dir == -1 and (centre and dis):
                                    state = "Click mouse"
                                    Clicked, _ = mouse_pointer_click(centre,dis,Clicked)
                                    if Clicked == 2:click(pointer_x,pointer_y)

                    if Controller_Mode == 1:
                        if H_dir == 1: 
                            keyboard.press(Key.right)
                        elif H_dir == -1: 
                            keyboard.press(Key.left)
                        else:
                            keyboard.release(Key.right)
                            keyboard.release(Key.left)
                        

                        if V_dir == 1: 
                            keyboard.press(Key.up)
                        elif V_dir == -1: 
                            keyboard.press(Key.down)
                        else:
                            keyboard.release(Key.up)
                            keyboard.release(Key.down)

                        # if Jump == 1: keyboard.press(Key.space)

        #======================================================================
        cv2.putText(Main_img,f'MOUSE',(start_x + 60,start_y + 30),Font_type,Font_size,Font_color,2)
        cv2.putText(Main_img,f'ARROW',(mid_x + 60,start_y + 30),Font_type,Font_size,Font_color,2)
        
        cv2.line(Main_img,(mid_x,start_y),(mid_x,hand_start_y),(10,10,250),2)            
        cv2.rectangle(Main_img,(start_x, start_y),(end_x, end_y),(10,10,250),2)
        cv2.rectangle(Main_img,(hand_start_x, hand_start_y),(hand_end_x, hand_end_y),(10,10,250),2)
        
        cv2.putText(Main_img,f'DETECTION :- {Hand_Detection_check}',(40,20),Font_type,Font_size,Font_color,Font_thickness)
        cv2.putText(Main_img,f'STATE :-{state}',(250,20),Font_type,Font_size,Font_color,Font_thickness)
        #======= Displaying the FPS of the CV Apk =============================
        fps = 1/(cur_time-prev_time)
        prev_time = cur_time
        cv2.putText(Main_img,f'FPS:- {int(fps)}',(40,40),Font_type,Font_size,(90,140,185),Font_thickness)
        #======================================================================
        type_controller = "Mouse" if Controller_Mode == 0 else 'Arrow'
        cv2.putText(Main_img,f"Controll Type:-{type_controller}",(250,40),Font_type,Font_size,Font_color,Font_thickness)
        #======== Displaying the Main Image ===================================
        cv2.imshow('Game Controller',Main_img)
        if cv2.waitKey(10) == ord("q"): Quit_confirm = True
        #======= Quiting the apk ==============================================
        if Quit_confirm:
            say('Quitting')
            sleep(2)
            break

if __name__== '__main__':
    main()