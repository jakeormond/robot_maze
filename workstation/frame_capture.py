'''
take a jpeg image using the imaging source camera.
NOTE: this code has not been tested on the lab camera!!!
'''
import cv2
import os

def capture_frame(filename, directory):

    # Open a connection to the USB camera (usually camera index 0)
    cap = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    # set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2448)  # Width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2048)  # Height

    # Capture a frame
    ret, frame = cap.read()

    # Check if the frame was captured successfully
    if not ret:
        print("Error: Could not capture frame.")
        cap.release()  # Release the camera
        exit()

    # Save the frame as a JPEG image
    jpeg_path = os.path.join(directory, filename)
    cv2.imwrite(jpeg_path, frame)

    # Release the camera
    cap.release()

    print(f"Frame captured and saved as {filename}")
    
    return

if __name__ == '__main__':
    filename = "captured_frame.jpg"
    # directory = "/media/jake/LaCie/robot_maze_workspace"
    directory = 'D:/testFolder/pico_robots/platform_images'
    capture_frame(filename, directory)
