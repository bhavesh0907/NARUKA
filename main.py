import copy
import math
import argParser
import ctypes
import tkinter as tk
from PIL import Image, ImageTk
import cv2 as cv
import mediapipe as mp
import numpy as np
import vgamepad as vg
import BoundingBox
import LandmarkCalculation as lc

RValue = 0
SValue = 0
DtValue = 0
dialog_created = False  

minDetectionConfidence = 0.0
minTrackingConfidence = 0.0
sensitivity = 0
deadzone = 0

root = tk.Tk()
root.geometry("1x1+-1000+-1000")
root.title("Webcam Feed")


def open_dialog(event):         
    global dialog_created
    if not dialog_created:
        dialog_created = True
        dialog = tk.Toplevel(root)
        dialog.geometry("720x200")      
        dialog.title("Settings")
        
        frame1 = tk.Frame(dialog)
        frame1.grid(row = 0, column = 0, padx = 10, pady = 10)
        
        frame2 = tk.Frame(dialog)
        frame2.grid(row = 0, column = 1, padx = 10, pady = 10)
        
        frame3 = tk.Frame(dialog)
        frame3.grid(row = 1, column = 0, padx = 10, pady = 10)      
        
        frame4 = tk.Frame(dialog)
        frame4.grid(row = 2, column = 0, padx = 10, pady = 10) 
        
        def apply_radius_value():
            global RValue
            RValue = int(entry.get()) 
            print("Value entered:", RValue)
            
        def apply_sensitivity_value():
            global SValue
            SValue = int(entry.get())
            print("Sensitivity set to: ", SValue)
            
        def apply_Deadzone_tolerance():
            global DtValue
            DtValue = int(entry.get())
            print("Deadzone tolerance set to: ", DtValue)       
            
        def on_dialog_close():
            global dialog_created
            dialog_created = False    
            dialog.destroy()     
        
        label = tk.Label(frame1, text = "Enter joystick radius")
        label.grid(row = 0, column = 0, padx = 0, pady = 5)
        entry = tk.Entry(frame1)
        entry.grid(row = 0, column = 1, padx = 5, pady = 5)
        apply_button = tk.Button(frame1, text="set", command=apply_radius_value)
        apply_button.grid(row = 0, column = 2, padx = 0, pady = 5)
        
        label_1 = tk.Label(frame2, text = "Enter sensitivity")
        label_1.grid(row = 0, column = 0, padx = 0, pady = 5)
        entry_1 = tk.Entry(frame2)
        entry_1.grid(row = 0, column = 1, padx = 5, pady = 5)
        apply_button_1 = tk.Button(frame2, text="set", command=apply_sensitivity_value)
        apply_button_1.grid(row = 0, column = 2, padx = 0, pady = 5)        
        
        label_2 = tk.Label(frame3, text = "Enter Deadzone tolerance")
        label_2.grid(row = 0, column = 0, padx = 0, pady = 5)
        entry_2 = tk.Entry(frame3)
        entry_2.grid(row = 0, column = 1, padx = 5, pady = 5)
        apply_button_2 = tk.Button(frame3, text="set", command=apply_Deadzone_tolerance)
        apply_button_2.grid(row = 0, column = 2, padx = 0, pady = 5)
        
        label_3 = tk.Label(frame4, text = "**To change the joystick origin, press 'q' while \n"
                           "hovering the index finger at the dseired center.\n"
                           "**To exit press 'esc' while the main window is selected")
        label_3.grid(row = 0, column = 1, padx = 0, pady = 5)
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        

def key_press(event):       #opens the settings menu when 'e' is pressed
    if event.keysym == 'e':
        open_dialog(event)

def opencv_window():
    args = argParser.get_args()

    device = args.device
    width = args.width
    height = args.height

    use_static_image_mode = args.use_static_image_mode
    min_detection_confidence = args.min_detection_confidence
    min_tracking_confidence = args.min_tracking_confidence

    
    #default values for the vcontroller
    joystick_origin_right = [800, 200]
    joystick_origin_left = [400, 200]
    joystick_deadzone_tolerance = 40
    sensitivity_modifier = 1
    joystick_radius = 150
    rt_level = 0
    gamepad = vg.VX360Gamepad()
    
    use_brect = False
    cap = cv.VideoCapture(device, cv.CAP_DSHOW)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode = use_static_image_mode,
        max_num_hands = 2,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )
    
    while True:
        key = cv.waitKey(50)    
        
        if key == 27:  #esc to exit
            break
        
        if key == 119: #w to change settings 
            print("Enter deadzone size: ")
            try:
                joystick_deadzone_tolerance = (int) (input())
            except:
                print("Default deadzone")
            print("Enter sensitivity: ")
            try:
                sensitivity_modifier = (int) (input())
            except:
                print("Default sensitivity")
            print("Enter joystick radius: ")
            try:
                joystick_radius = (int) (input())
            except:
                print("Default joystick radius")

        ret, image = cap.read()
        if not ret:
            break
        
        if (RValue > 0):
            joystick_radius = RValue
            
        if (SValue > 0):
            sensitivity_modifier = SValue
            
        if (DtValue > 0):
            joystick_deadzone_tolerance = DtValue
            
        root.bind("<KeyPress>", key_press)
        
        image = cv.flip(image, 1)  #to mirror the display
        final_image = copy.deepcopy(image)

        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True

        if results.multi_hand_landmarks is not None:
            
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                handedness = handedness.classification[0].label[0:]
                brect = BoundingBox.calc_bounding_rect(final_image, hand_landmarks)
                landmark_list = lc.calc_landmark_list(final_image, hand_landmarks)

                if key == 113: #to reset the pointer position (q)
                    if handedness == "Right":
                        joystick_origin_right = landmark_list[8]
                        print("Right Joystick Origin set to: " + str(joystick_origin_right))
                    if handedness == "Left":
                        joystick_origin_left = landmark_list[8]
                        print("Left Joystick Origin set to: " + str(joystick_origin_left))

                if (math.dist(joystick_origin_right, landmark_list[8]) > joystick_deadzone_tolerance):
                    if handedness == "Right":
                        origin_difference_right = list(map(lambda x, y: x-y, joystick_origin_right, landmark_list[8]))
                        joystick_coordinates = list(map(lambda x: (x / joystick_radius) * sensitivity_modifier, origin_difference_right))
                        joystick_coordinates = np.clip(joystick_coordinates, -1.0, 1.0)
                        joystick_coordinates[0] = joystick_coordinates[0] * -1
                        gamepad.right_joystick_float(x_value_float=joystick_coordinates[0], y_value_float=joystick_coordinates[1])
                else:
                    gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
                if (math.dist(joystick_origin_left, landmark_list[8]) > joystick_deadzone_tolerance):
                    if handedness == "Left":
                        origin_difference_left = list(map(lambda x, y: x-y, joystick_origin_left, landmark_list[8]))
                        joystick_coordinates = list(map(lambda x: (x / joystick_radius) * sensitivity_modifier, origin_difference_left))
                        joystick_coordinates = np.clip(joystick_coordinates, -1.0, 1.0)
                        joystick_coordinates[0] = joystick_coordinates[0] * -1
                        gamepad.left_joystick_float(x_value_float=joystick_coordinates[0], y_value_float=joystick_coordinates[1])
                else:
                    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)

                pressed_tolerance = 20
                if (math.dist(landmark_list[8], landmark_list[4]) < pressed_tolerance):
                    print("pressed " + handedness + " index")
                    if handedness == "Right":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                    if handedness == "Left":
                        #gamepad.right_trigger(value=255)
                        rt_level += 30
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                    rt_level -= 10
                rt_level = np.clip(rt_level, 0, 255)
                if (math.dist(landmark_list[12], landmark_list[4]) < pressed_tolerance):
                    print("pressed " + handedness + " middle")
                    if handedness == "Right":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
                    if handedness == "Left":
                        gamepad.left_trigger(value=255)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
                    gamepad.left_trigger(value=0)
                if (math.dist(landmark_list[16], landmark_list[4]) < pressed_tolerance):
                    print("pressed " + handedness + " ring")
                    if handedness == "Right":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
                    if handedness == "Left":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
                if (math.dist(landmark_list[20], landmark_list[4]) < pressed_tolerance):
                    print("pressed " + handedness + " pinky")
                    if handedness == "Right":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
                    if handedness == "Left":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                if (math.dist(landmark_list[8], landmark_list[2]) < pressed_tolerance):
                    print("pressed " + handedness + " bottom of thumb")
                    if handedness == "Right":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
                    if handedness == "Left":
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
                if ((landmark_list[20][0] - landmark_list[4][0]) > pressed_tolerance) and (handedness == "Left"):
                    # print("flipped left hand")
                    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
                if ((landmark_list[4][0] - landmark_list[20][0]) > pressed_tolerance) and (handedness == "Right"):
                    # print("flipped right hand")
                    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
                else:
                    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

                gamepad.right_trigger(value=rt_level)
                gamepad.update()

                final_image = lc.draw_origin(final_image, joystick_origin_right, joystick_radius)
                final_image = lc.draw_origin(final_image, joystick_origin_left, joystick_radius)
                final_image = BoundingBox.draw_bounding_rect(use_brect, final_image, brect)
                final_image = lc.draw_landmarks(final_image, landmark_list)
    
        cv.imshow('Hand Gesture Controller', final_image)
        root.update()
    
    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    opencv_window()
    root.mainloop()