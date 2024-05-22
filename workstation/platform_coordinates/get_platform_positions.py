import cv2
import numpy as np
import pickle
import os
import re


def get_platform_positions(image_path=None):
    '''
    Finds the platform positions in the images using the Hough Circle Transform.
    It automatically adjusts the parameters until the correct number of circles 
    are produced. Once the thresholds are correctly set, accurate detection requires
    setting the circle radius appropriately. The algorithm begins the search with a 
    slightly smaller radius than expected, and then increases the radius until the 
    user is satisfied with the results.'''
    
    if image_path is None:
        # image_path = 'c:/Users/Jake/Documents/robot_maze/platform_images_22-09-2023'
        # image_path = '/home/jake/Documents/robot_maze_platform_images'
        image_path = 'C:/Users/Jake/Documents/robot_maze/platform_images'

    # get all files in the directory that begin with "platforms", 
    # and end with "cropped.jpg"
    import os
    image_names = [f for f in os.listdir(image_path) if f[-11:] == 'cropped.jpg']

    platform_coordinates_cropped = {}

    for i, image_name in enumerate(image_names):

        # extract the platform numbers from the file name
        # split the filename by the underscore
        # i_split = image_name.split('.')[0].split('_')[1:]
        i_split = image_name.split('_')[1:-1]
        # remove the string 'cropped' from the list
        # i_split.remove('cropped')
        platforms = [int(float(i)) for i in i_split]
        # sort the list
        platforms.sort()

        # load image
        img = cv2.imread(image_path + '/' + image_name)

        # convert to grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # apply gaussian blur to reduce noise and improve circle detection
        img = cv2.GaussianBlur(img, (9, 9), 1)

        # get the number of platforms in the image
        num_platforms = len(platforms)

        # Use the Hough Circle Transform to detect circles
        minRadius = 80
        maxRadius = minRadius + 4
        minDist = minRadius*2
        param1 = 30 # threshold to pass to Canny edge detector
        param2 = 30 # accumaulator threshold for circle centers, 
        # smaller value means more false circles may be detected

        while True:
            circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, minDist,
                                param1=param1, param2=param2, minRadius=minRadius, 
                                maxRadius=maxRadius)
        
            # Check if circles were found
            if circles is not None:
                circles = np.uint16(np.around(circles))      

                # count the number of circles detected
                num_circles = circles.shape[1]
                
                if num_circles == num_platforms:
                    print("Correct number of circles detected.")
                elif num_circles > num_platforms:
                    print("Too many circles detected.")
                    param2 += 1    
                elif num_circles < num_platforms:
                    print("Too few circles detected.")
                    param2 -= 1       

                if num_circles == num_platforms:
                    # squeeze cicrles array to remove the extra dimension
                    circles = circles[0]
                    # display the image
                    clone = img.copy()
                    for c in range(num_circles):
                        center = (circles[c, 0], circles[c, 1])
                        radius = circles[c, 2]
                        # Draw the circle on a copy of the original image
                        cv2.circle(clone, center, radius, (0, 255, 0), 2)                    
                    
                    scaling_factor = 2
                    resized_image = cv2.resize(clone, None, fx=scaling_factor, fy=scaling_factor)
                    cv2.namedWindow('Detected Circles', cv2.WINDOW_AUTOSIZE)
                    cv2.moveWindow('Detected Circles', 1500, 200)
                    cv2.imshow('Detected Circles', resized_image)
                    cv2.waitKey(1000)

                    # ask user if the circles radii are correct
                    radii = circles[:,2]
                    # reorder the radii and circles to match the order of the x positions
                    # of the platforms
                    y_positions = circles[:,1]
                    radii = radii[np.argsort(y_positions)]
                    circles = circles[np.argsort(y_positions), :]

                    print("radii = ", radii)
                    radii_correct = input("Are the radii correct? (y/n) ")
                
                    cv2.destroyAllWindows()
                    
                    if radii_correct == 'y' and num_circles == num_platforms:
                            break
                    
                    elif radii_correct != 'y':
                        print(f"the set min radius is {minRadius} and the set max radius is {maxRadius}")
                        
                        minRadius += 3
                        maxRadius += 3

                        minDist = minRadius*2

                    
            else:
                print("No circles were detected in the image.")
                
                param2 -= 1

        # save the circle coordinates
        for i, p in enumerate(platforms):
            platform_coordinates_cropped[p] = [circles[i,0], circles[i,1], circles[i,2]]

    # order the platform coordinates by platform number
    platform_coordinates_cropped = dict(sorted(platform_coordinates_cropped.items()))

    # save the platform coordinates to a file
    # if platform_coordinates_cropped.pickle already exists, load it
    if os.path.isfile(image_path + '/platform_coordinates_cropped.pickle'):
        with open(image_path + '/platform_coordinates_cropped.pickle', 'rb') as handle:
            platform_coordinates_og = pickle.load(handle)
        # update the platform_coordinates dictionary with the new coordinates
        platform_coordinates_og.update(platform_coordinates_cropped)
        # save the updated dictionary
        with open(image_path + '/platform_coordinates_cropped.pickle', 'wb') as handle:
            pickle.dump(platform_coordinates_og, handle, protocol=pickle.HIGHEST_PROTOCOL)

    else:
        # save platform_coordinates_cropped to a pickle file
        with open(image_path + '/platform_coordinates_cropped.pickle', 'wb') as handle:
            pickle.dump(platform_coordinates_cropped, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    return platform_coordinates_cropped

def draw_platforms_on_uncropped(directory=None):
    '''
    Draws the platform positions on the uncropped images. This is useful for 
    checking that the platform positions were extracted correctly. 
    CURRENTLY, THIS NEEDS TO BE RUN TO SAVE THE CORRECTED PLATFORM COORDINATES FILE!!!!
    '''
    if directory is None:
        # directory = '/home/jake/Documents/robot_maze_platform_images'
        # directory = 'D:/testFolder/pico_robots/platform_images'
        directory = 'C:/Users/Jake/Documents/robot_maze/platform_images'

    # load the platform coordinates
    with open(directory + '/platform_coordinates_cropped.pickle', 'rb') as handle:
        platform_coordinates_cropped = pickle.load(handle)

    # load the crop coordinates
    with open(directory + '/crop_coordinates.pickle', 'rb') as handle:
        crop_coordinates = pickle.load(handle) 

    # get all files in the directory that begin with "platforms" and don't end
    # with "cropped.jpg"
    image_names = [f for f in os.listdir(directory) if f[-4:] == '.jpg' 
                    and f[-11:] != 'cropped.jpg']
    
    platform_coordinates = {}

    for i, image_name in enumerate(image_names):

        # load image
        img = cv2.imread(directory + '/' + image_name)

        # get the crop coordinates
        crop_coor = crop_coordinates[image_name]

        # get the platform numbers from the file name
        # split the filename by the underscore
        # platforms = [int(digit) for digit in (image_name.split('.')[0].split('_')[1:])]

        i_split = re.split('[_.]', image_name)
        # remove any strings starting with 'plat', 'j', or equal to '0'
        i_split = [i for i in i_split if not re.match(r'plat|j|0', i)]
        platforms = [int(float(i)) for i in i_split]
        # sort the list
        platforms.sort()

        # loop through the platforms and draw them on the image
        for p in platforms:
            # get the platform coordinates
            center = (platform_coordinates_cropped[p][0] + crop_coor[0], 
                      platform_coordinates_cropped[p][1] + crop_coor[1])
            radius = platform_coordinates_cropped[p][2]

            # store the corrected coordinates in platform_coordinates
            platform_coordinates[p] = [center[0], center[1], radius]

            # Draw the circle on a copy of the original image
            cv2.circle(img, center, radius, (0, 255, 0), 2)

        # display the image
        scaling_factor = 0.5
        resized_image = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor)
        cv2.namedWindow('Detected Circles', cv2.WINDOW_AUTOSIZE)
        # cv2.moveWindow('Detected Circles', 1500, 200)
        cv2.moveWindow('Detected Circles', 200, 0)
        cv2.imshow('Detected Circles', resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # save corrected coordinates
    # sort the platform coordinates by platform number
    platform_coordinates = dict(sorted(platform_coordinates.items()))
    with open(directory + '/platform_coordinates.pickle', 'wb') as handle:
        pickle.dump(platform_coordinates, handle, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == "__main__":
    # get_platform_positions()
    draw_platforms_on_uncropped()