#===== Importing Required Modules ==========================================
from pynput.keyboard import Controller as kc
from pynput.keyboard import Key
from pynput.mouse import Controller as mc
from pynput.mouse import Button
import cv2

from win32com.client import Dispatch
from win32api import GetSystemMetrics

from numpy import interp
from time import sleep, time

from Handcontroller import Hand_Controller

keyboard = kc()
mouse  = mc()
#================================================================================
#=============== Machine Voice ==================================================
voice_engine = Dispatch('SAPI.Spvoice')

def say(audio):
    """Used to Speak the text, given audio parameter"""
    voice_engine.Speak(audio)

say('Machine Voice connected')
#=============== Main Program ===================================================
def main():
    """
    Main function to run the program
    """
    def check_in_fing(point_list=[0,0],box=0):
        """
        Args:
            point_list (list, optional): finger position on the image. (Defaults to [0,0])
            box (int, optional): It describes which box value has to be returned(Defaults to 0.)
        
        box = 0: Returns, is finger in the detection box.
        box = 1: Returns, is finger only in the gesture box.
        box = 2: Returns, on which state box fingeris inn.
        box = 3: Returns, is finger on the qutting button box.
        """
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
        
        elif box==3 :
            if (start_x-100) < point_list[0] < start_x and start_y < point_list[1] < hand_start_y:
                return True
            return False
        return 0
    #===========================================================================
    def mouse_pointer_click(centre, dis, Clicked):
        """
        Args:
            centre  : Middle Coordinates btw the two fingers
            dis     : Distance btw the two fingers
            Clicked : Interger that had stored previos clicked state
        Returns click state.
        """
        cx,cy = centre
        cv2.circle(Main_img,(cx,cy),15,(181,181,181),cv2.FILLED)   
        if Clicked >= 1: Clicked = 0

        if dis < 30:
            cv2.circle(Main_img,(cx,cy),15,(0,252,51),cv2.FILLED)
            if Clicked==0: Clicked = 1

        if Clicked == 1:
            Clicked += 1
        return Clicked
    #===========================================================================
    say('Getting Hand dectector')
    Hand_detector = Hand_Controller()      # Creating hand-Detector 
    #===========================================================================
    V_dir, H_dir, Jump = 0, 0, 0
    Controller_Mode = -1
    #===========================================================================
    # Setting up the fingers relted variable
    Thumb = Index_Finger = Middle_Finger = Ring_Finger = Pinky_Finger = 1
    sum_of_finger_state = 0
    finger_up_state = []
    #===========================================================================
    prev_time, cur_time  =  0, 0        # Creating time counter to get the fps
    Quit_confirm = False                # Variable that used to stop the program
    #===========================================================================
    # Font Type used in the text, that to be displayed in the image-frame
    Font_type = cv2.FONT_HERSHEY_PLAIN
    Font_size = 1
    Font_color = (215,255,214)
    Font_thickness = 2
    #===========================================================================
    # Mouse pointer cordinate variable
    pointer_x, pointer_y = 0, 0
    Clicked = 0
    clk = 0
    #===========================================================================
    # Setting up the dimension & co-ordinate for the image-frame to recoginize the gesture
    start_x, start_y, end_x, end_y = 225, 50, 575, 400
    hand_start_x, hand_start_y, hand_end_x, hand_end_y = 225, 100, 575, 400
    mid_x = (start_x + end_x)//2
    scrn_width, scrn_height = GetSystemMetrics(0), GetSystemMetrics(1)
    #===========================================================================
    say('Getting Camera')
    cap = cv2.VideoCapture(0)           # Initialising Camera object
    cam_width,cam_height = 960,720      # And setiing up it's
    cap.set(3,cam_width)                # Width and Height
    cap.set(4,cam_height)               # According to ourself
    say('Camera connected')
    #==========================================================================
    while True:
        _ , cap_img = cap.read()        # reading the image from the camera
        cur_time = time()               # storing the current time, [used to calculate FPS]
        Main_img = cv2.flip(cap_img,1)  # Flipping the image; This image will be used for further processing
        #======================================================================
        state = ''                      # Setting up the state variable
        Hand_Detection_check = False    # Variable to check detection of hand
        # Finding hand in 'Main_img' frame using custom class 
        Main_img = Hand_detector.findhand(Main_img,True)
        # Finding up the position of each landmarks in the image
        lm_list = Hand_detector.findPosition()
        #======================================================================
        # Setted Each Direction value -> 0
        V_dir, H_dir, Jump = 0, 0, 0
        #======================================================================
        # If hand is detected then do some works; else pass
        if lm_list:
            Hand_Detection_check = True         # Set detection->true for further refernce
            # Get the state of each finger; whether they are open or closed
            finger_up_state = Hand_detector.fingersUp()
            # getting each fingers coordinate list; such that they don't need to be fetched multiple times
            Index_pos = lm_list[8][1:]
            Middle_pos = lm_list[12][1:]
            # Ring_pos = lm_list[16][1:]
            Pinky_pos = lm_list[20][1:]
            Thumb_pos = lm_list[4][1:]
            #=============== Checking & Changing finger's State ===============
            """
            if any fingers is open,then check for gesture
            else pass
            """
            if finger_up_state.size != 0 :
                Index_finger_inn = check_in_fing(Index_pos)   # Checking whether Index & Middle finger
                Middle_finger_inn = check_in_fing(Middle_pos) # are in the detection box
                #==============================================================
                if Index_finger_inn or Middle_finger_inn:
                    """If Index & Middle finger are in the detection box check whether they are in the State-Change Button box"""
                    Index_finger_button_in = check_in_fing(Index_pos,2)
                    Middle_finger_button_in = check_in_fing(Middle_pos,2)
                    if Index_finger_button_in == Middle_finger_button_in:
                        """
                        if index & middle finger are state-change button box, 
                        find whether they are clicking or not
                        also check in which box they are clicking-in;
                        then change the Controller_mode according to the box
                        """
                        z = 0
                        [dis , centre ]= Hand_detector.findDistance(Main_img,1,2)
                        if centre and dis:
                            Clicked = mouse_pointer_click(centre,dis,Clicked)
                            if Clicked == 2: z = 1
                        if Index_finger_button_in == 1 and z == 1 :
                            """if fingers are in box 1 set controller_mode to 0 i.e. Arrow Controls"""
                            state += " asdf"
                            Controller_Mode = 0
                        elif Index_finger_button_in == 2 and z == 1:
                            """if fingers are in box 2 set controller_mode to 1 i.e. Mouse Controls"""
                            state += " arrow"
                            Controller_Mode = 1
                else:
                    """
                    
                    """
                    [Thumb,Index_Finger,Middle_Finger,Ring_Finger,Pinky_Finger] = finger_up_state
                    sum_of_finger_state = sum(finger_up_state[1:])
                    #==========================================================
                    """ Check for each finger & thumb, whether they are in the detection & gesture box """
                    Thumb_in = check_in_fing(Thumb_pos,1)
                    Index_finger_in = check_in_fing(Index_pos,1)
                    Middle_finger_in = check_in_fing(Middle_pos,1)
                    # Ring_Finger_in = check_in_fing(Ring_pos,1)
                    Pinky_Finger_in = check_in_fing(Pinky_pos,1)

                    """ Checking for Index & Middle finger whether they are in Qutting button section """
                    Index_fing_qt = check_in_fing(Index_pos,3)
                    Middle_fing_qt = check_in_fing(Middle_pos,3)
                    
                    if sum_of_finger_state == 0:            # if all the fingers & thumb is closed
                        if Thumb_in and not(Thumb):         # and thumb is in the gesture box
                            state = state + "Jump "         # set Jump state to high
                            Jump = 1
                    else:
                        """if any of the finger is open, check for other controls"""
                        # Create Direction Controlls
                        # Vertical Direction
                        if Index_Finger and Index_finger_in:    # if only index finger is in getsure box and is open,
                            if (not Middle_Finger):             # and middle finger is closed
                                state = state + "Up "           # then set Vertical direction to +ve
                                V_dir = 1
                            elif Middle_finger_in and Middle_Finger and not(Ring_Finger):   # if only index & middle finger is in getsure box and is open,
                                state = state + "Down "                                     # and ring finger is closed
                                V_dir = -1                                                  # then set Vertical direction to +ve
                        # Horizontal Direction
                        if (Thumb and Thumb_in) and not(Pinky_Finger):          # if Thumb is in the gesture box and is open
                            state = state + "Left "                             # and Pinky finger is closed, then set Horizontal direction to -ve i.e towarss left
                            H_dir = -1
                        elif (Pinky_Finger and Pinky_Finger_in) and not(Thumb): # if pinky finger is in the gesture box and is open and thumb is closed
                            state = state + "Right "                            # then set Horizontal direction to +ve i.e. towards right
                            H_dir = 1
                    #==========================================================
                    if Controller_Mode == 0:
                        """Controller mode -> 0; is mouse control mode
                        Available mouse controls are Pointer movement & Left-click"""
                        if V_dir == 1:
                            # IF vertical direction is +ve then pointer movement will occur
                            px, py = lm_list[8][1:]                        
                            pointer_x = int(interp(px,(hand_start_x,end_x),(0,scrn_width)))
                            pointer_y = int(interp(py,(hand_start_y,end_y),(0,scrn_height)))
                            #==== Mouse Pointer Movement ==============================
                            state = "Mouse Pointer"
                            cv2.circle(Main_img,(px,py),5,(200,200,200),cv2.FILLED)
                            cv2.circle(Main_img,(px,py),10,(200,200,200),3)
                            mouse.position = (int(pointer_x),int(pointer_y))
                        else:
                            # IF vertical direction is not +ve then left-click or quit-check wil happen
                            [dis , centre ]= Hand_detector.findDistance(Main_img,1,2)
                            if (Index_fing_qt and Middle_fing_qt) and sum_of_finger_state <= 3:
                                """If Index & middle finger are in quit button box,then check for click in it."""
                                state = "Quit Check"
                                if centre and dis:
                                    Clicked = mouse_pointer_click(centre,dis,Clicked)
                                    if Clicked == 2: Quit_confirm = True
                            if V_dir == -1 and (centre and dis):
                                """If vertial direction is -ve then check for mouse left-click"""
                                state = "Click mouse"
                                Clicked = mouse_pointer_click(centre,dis,Clicked)
                                if Clicked == 2:
                                    if(clk == 0):
                                        mouse.position = (int(pointer_x),int(pointer_y))
                                        mouse.click(Button.left)   
                                        clk+=1
                                    else: clk -=1                    
                    #==========================================================
                    if Controller_Mode == 1:
                        """Controller mode -> 1; is Keys control mode
                        Available Keys controls are Left, Right, Up, Down & Space bar press"""
                        # Horizontal direction control
                        if H_dir == 1: 
                            keyboard.press(Key.right)
                        elif H_dir == -1: 
                            keyboard.press(Key.left)
                        else:
                            keyboard.release(Key.right)
                            keyboard.release(Key.left)
                        
                        # Vertical direction control
                        if V_dir == 1: 
                            keyboard.press(Key.up)
                        elif V_dir == -1: 
                            keyboard.press(Key.down)
                        else:
                            keyboard.release(Key.up)
                            keyboard.release(Key.down)

                        # Space-bar/Jump control
                        if Jump == 1: keyboard.press(Key.space)
                        else: keyboard.release(Key.space)
        #======================================================================
        # Puttign Text onto the Image for user to get the states & controls & othe r info required  
        cv2.putText(Main_img,f'MOUSE',(start_x + 60,start_y + 30),Font_type,Font_size,Font_color,2)
        cv2.putText(Main_img,f'ARROW',(mid_x + 60,start_y + 30),Font_type,Font_size,Font_color,2)
        
        cv2.line(Main_img,(mid_x,start_y),(mid_x,hand_start_y),(10,10,250),2)            
        cv2.rectangle(Main_img,(start_x, start_y),(end_x, end_y),(10,10,250),2)
        cv2.rectangle(Main_img,(hand_start_x, hand_start_y),(hand_end_x, hand_end_y),(10,10,250),2)
        
        cv2.putText(Main_img,f'DETECTION :- {Hand_Detection_check}',(40,20),Font_type,Font_size,Font_color,Font_thickness)
        cv2.putText(Main_img,f'STATE :-{state}',(250,20),Font_type,Font_size,Font_color,Font_thickness)
        
        cv2.putText(Main_img,f'QUIT',(start_x-65,start_y + 30),Font_type,Font_size,Font_color,2)
        cv2.rectangle(Main_img,(start_x-100, start_y),(start_x, hand_start_y),(10,10,250),2)
        #======================================================================
        type_controller = "Mouse" if Controller_Mode == 0 else 'Arrow'
        cv2.putText(Main_img,f"Controll Type:-{type_controller}",(250,40),Font_type,Font_size,Font_color,Font_thickness)
        #======= Displaying the FPS of the CV Apk =============================
        fps = 1/(cur_time-prev_time)
        prev_time = cur_time
        cv2.putText(Main_img,f'FPS:- {int(fps)}',(40,40),Font_type,Font_size,(90,140,185),Font_thickness)
        #======== Displaying the Main Image ===================================
        cv2.imshow('Game Controller',Main_img)
        if cv2.waitKey(10) == ord("q"): Quit_confirm = True
        #======= Quiting the apk ==============================================
        if Quit_confirm:
            say('Quitting')
            sleep(1)
            break

#============================================
if __name__== '__main__':
    main()