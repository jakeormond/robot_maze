The purpose of the platform coordinates sub-package is to calculate the position of platform
within the field of view of the over-head camera. The coordinates are required during the 
running of the behavioural task for 2 reasons: 1) so the image acquired from the camera can 
be cropped around the platforms before being save to disk, making the file sizes more 
manageable, and 2) so that, given the animal's coordinates within the field of view, we can
determine on which platform he is located. 

How to use this sub-package:
1) Run capture_all_positions.py
    - This will drive the robots around the maze, acquiring images of the platforms at each 
    location. 
    - The 3 robots should be placed at the upper left most corner of the maze in a vertical 
    arrangement (i.e. in column 1; see platform_map for platform locations)
    - An image will be taken, and saved with the platform numbers in the file name.
    - The robots will be driven right to the next position, and another image taken. 
    - This process continues until the image in the final column has been captured, at which 
    point, the robots move down to the next set of rows, and the process begins again but moving
    to the right. 
    - Depending on the maze size, the robots may have to switch directions a few times before the 
    process completes.
    - Also, depending on the size, the final right or left sweep may use fewer than 3 robots. 
    - Note that the code is currently hard-coded for the row and column size of our maze. 
    - From the same sub-package, calls capture_frame from frame_capture.py to acquire the image
    from the camera. 

2) Run crop_platform_images.py
    - Next, images are manually cropped around the 3 robot platforms. This aids the subsequent 
    automatic detection of the platforms.

3) From get_platform_positions.py, call get_platform_positions.
    - This will automatically detect the platforms using a circle detection algorithm. 
    - Both the platform centre and its radius will be calculated. 
    - The algorithm proceeds iteratively, adjusting parameters until the correct number 
    of objects are detected. It is designed to err on the side of a smaller radius for 
    each platform. It will draw the platform outlines over the platforms, and ask the 
    user if they are satisfied with the platform radius. If not, it will search for objects
    with a slightly larger radius and ask the user again. In our hands, this process worked
    in all cases to accurately identify the platform positions. 

4) From get_platform_positions.py, call draw_platforms_on_uncropped
    - This draws all the identified platforms on the uncropped image, allowing the user to 
    verify that accurate platform positions have indeed been calculated. 