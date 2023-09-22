import cv2
import numpy as np

# Initialize global variables to store mouse click coordinates
cropping = False
x_start, y_start, x_end, y_end = 0, 0, 0, 0

# Mouse callback function
def mouse_callback(image, event, x, y, flags):
    global x_start, y_start, x_end, y_end, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        cropping = True

    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping:
            x_end, y_end = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        x_end, y_end = x, y
        cropping = False

        # Draw a rectangle around the selected region
        cv2.rectangle(image, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)
        cv2.imshow("Image", image)

# Path to the images
image_path = 'c:/Users/Jake/Documents/robot_maze/platform_images_22-09-2023'

# get all file names in the directory
import os
filenames = os.listdir(image_path)

# find and remove any filenames that don't end in .jpg
for f in filenames:
    if f[-4:] != '.jpg':
        filenames.remove(f)
        continue

    # extract the platform numbers from the file name
    # split the filename by the underscore
    f_split = f.split('.')[0].split('_')[1:]

    # load image
    img = cv2.imread(image_path + '/' + f)

    # convert to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # allow the user to crop the image using the mouse
    # display the image
    # Create a window and set the mouse callback function
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)

    while True:
        cv2.imshow("Image", img)
        key = cv2.waitKey(1) & 0xFF

        # Press 'c' to crop the selected region
        if key == ord("c"):
            cropped_image = img[y_start:y_end, x_start:x_end]
            cv2.imshow("Cropped Image", cropped_image)
            cv2.waitKey(0)

        # Press 'r' to reset the selection
        elif key == ord("r"):
            image = cv2.imread("example.jpg")

        # Press 'q' to quit
        elif key == ord("q"):
            break
    
    cv2.destroyAllWindows()



    # apply gaussian blur to reduce noise and improve circle detection
    img = cv2.GaussianBlur(img, (9, 9), 1)

    # display the image
    # cv2.imshow('image', img)
    # cv2.waitKey(0)

    # Use the Hough Circle Transform to detect circles
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 100,
                               param1=70, param2=40, minRadius=100, maxRadius=150)
    
   # Check if circles were found
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            center = (circle[0], circle[1])
            radius = circle[2]
            # Draw the circle on the original image
            cv2.circle(img, center, radius, (0, 255, 0), 2)
        cv2.imshow('Detected Circles', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("No circles were detected in the image.")

