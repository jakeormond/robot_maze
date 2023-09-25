'''
code adapted from: https://pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/#pyis-cta-modal

The original code feature argument parsing, not used here. 

'''
# import the necessary packages
import argparse
import numpy as np
import cv2
import os
import pickle

def crop_platform_image(image_full_path):    
    
    # initialize the list of reference points and boolean indicating
    refPt = np.zeros((2,2), dtype=int)
    cropping = False

    # define the function that will be called when the mouse is clicked
    def click_and_crop(event, x, y, flags, param):
        # grab references to the global variables
        # global refPt, cropping
        # if the left mouse button was clicked, record the starting
        # (x, y) coordinates and indicate that cropping is being
        # performed
        if event == cv2.EVENT_LBUTTONDOWN:
            refPt[0,:] = [x, y]
            cropping = True
        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            refPt[1,:] = [x, y]
            cropping = False
            # draw a rectangle around the region of interest
            cv2.rectangle(resized, refPt[0], refPt[1], (0, 255, 0), 2)
            cv2.imshow("resized", resized)

    # get image name
    directory, full_filename = os.path.split(image_full_path)
    image_name, _ = os.path.splitext(full_filename)
    print(image_name)

    image = cv2.imread(image_full_path)
    clone = image.copy()

    image_width = image.shape[1]
    image_height = image.shape[0]
    resized = cv2.resize(image, (int(image_width/2), int(image_height/2)))    
    
    cv2.namedWindow("resized")
    cv2.setMouseCallback("resized", click_and_crop)
    # keep looping until the 'q' key is pressed
    while True:
        # display the image and wait for a keypress
        cv2.imshow("resized", resized)
        key = cv2.waitKey(1) & 0xFF
        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            resized = cv2.resize(image, (int(image_width/2), int(image_height/2)))
        # if the 'c' key is pressed, break from the loop
        elif key == ord("c"):
            break
    
    # multiply refPt by 2 (to account for the resize), then crop 
    # the region of interest from the full size image and display it

    refPt = refPt*2
    roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
    cv2.imshow("ROI", roi)
    cv2.waitKey(0)

    # save the cropped image
    cv2.imwrite(directory + '/' + image_name + '_cropped.jpg', roi)

    # close all open windows
    cv2.destroyAllWindows()

    return image_name, refPt


def crop_platform_images(image_paths):
    
    # create storage for the crop coordinates
    crop_coordinates = {}
    
    for i in image_paths:
        file_name, crop_coor= crop_platform_image(i)      
        
        # store the crop coordinates[:-len(image_name)]
        crop_coordinates[file_name + '.jpg'] = [crop_coor[0][0], crop_coor[0][1], crop_coor[1][0], crop_coor[1][1]]

    return crop_coordinates
    
# main method
if __name__ == "__main__":
    image_path = '/home/jake/Documents/robot_maze_platform_images'

    # find any images that are already cropped, so we don't duplicate our effort!
    cropped_files = [f for f in os.listdir(image_path) if f[-11:] == 'cropped.jpg']

    # get the list of uncropped images
    uncropped_files = [f for f in os.listdir(image_path) if f[-4:] == '.jpg' 
                        and f[-11:] != 'cropped.jpg']

    # remove uncropped files that have already been cropped
    virgin_files = uncropped_files

    for c in cropped_files:
        # remove file extension from cropped file name
        _, full_filename = os.path.split(c)
        filename, _ = os.path.splitext(full_filename)
        virgin_files.remove(filename[:-8] + '.jpg')
    

    # add the directory to the file names
    virgin_files = [image_path + '/' + f for f in virgin_files]

    crop_coordinates = crop_platform_images(virgin_files)

    # if crop_corrdinates.pickle already exists, load it
    if os.path.isfile(image_path + '/crop_coordinates.pickle'):
        with open(image_path + '/crop_coordinates.pickle', 'rb') as handle:
            crop_coordinates_og = pickle.load(handle)
        # update the crop_coordinates dictionary with the new coordinates
        crop_coordinates_og.update(crop_coordinates)
        # save the updated dictionary
        with open(image_path + '/crop_coordinates.pickle', 'wb') as handle:
            pickle.dump(crop_coordinates_og, handle, protocol=pickle.HIGHEST_PROTOCOL)


    else:
        # save crop_coordinates to a pickle file
        with open(image_path + '/crop_coordinates.pickle', 'wb') as handle:
            pickle.dump(crop_coordinates, handle, protocol=pickle.HIGHEST_PROTOCOL)