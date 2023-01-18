import cv2
import time
import numpy as np
from hazard_detect import saturated_red_flash_count, luminance_flash_count
from collections import deque
import imutils

# Buffer size (in frames)
BUFFER_SIZE = 16

# Open the webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 100)

# Disable auto exposure
# TODO: This is not working

# Width and height of the webcam frame after resizing (without changing resolution)
ret, frame = cap.read()
frame = imutils.resize(frame, width = frame.shape[1] // 4)

WIDTH = frame.shape[1]
HEIGHT = frame.shape[0]

# Set the quarter area threshold (in pixels)
quarter_area_threshold = (WIDTH * HEIGHT) / 4

# Initialize the frame buffer
frame_buffer = deque()
time_buffer = deque()
luminous_flash_buffer = deque()
red_flash_buffer = deque()

luminous_flashes = np.zeros(frame.shape[:2])
red_flashes = np.zeros(frame.shape[:2])

# Initialize previous time
prev_time = time.time()

# Capture frames from the webcam
try:
    while True:
        # Read a frame from the webcam
        ret, frame = cap.read()
        #frame = np.zeros(frame.shape)
        
        #If the frame was successfully read
        if ret:
            s = time.time()
            #changing the resolution while keeping the aspect ratio
            frame = imutils.resize(frame, width=WIDTH)
            
            # Add the frame to the frame buffer
            frame_buffer.append(frame)
            time_buffer.append(time.time())
            
            # If a previous frame exists, check whether the transition has a luminous/red flash
            if len(frame_buffer) > 1:
                cur_frame = frame_buffer[-1]
                prev_frame = frame_buffer[-2]
                
                # Check if transition is a flash
                luminous = luminance_flash_count(cur_frame, prev_frame)
                red = saturated_red_flash_count(cur_frame, prev_frame)
                
                # Update buffers and flash count
                luminous_flash_buffer.append(luminous)
                luminous_flashes += luminous
                red_flash_buffer.append(red)
                red_flashes += red
                
            # When there are enough frames and more than 1s has elapsed, check for flashing sequences
            interval = time_buffer[-1] - time_buffer[0]
            if len(frame_buffer) >= BUFFER_SIZE and interval >= 1:
                
                luminous_flash_freq = (luminous_flashes/2) / interval
                red_flash_freq = (red_flashes/2) / interval
                
                luminous_count = np.sum(luminous_flash_freq >= 3)
                red_count = np.sum(red_flash_freq >= 3)
                
                print(np.mean(luminous_flash_freq), np.mean(red_flash_freq))
                if luminous_count >= quarter_area_threshold or red_count >= quarter_area_threshold:
                    print("Flashing detected")
                    
                # Pop first element to change sliding window
                frame_buffer.popleft()
                time_buffer.popleft()
                
                # Update flash count
                luminous_flashes -= luminous_flash_buffer.popleft()
                red_flashes -= red_flash_buffer.popleft()
            
finally:
    cap.release()
    cv2.destroyAllWindows()
    
