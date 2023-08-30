'''
Code for generating cropping parameters for the overhead camera
recording in Bonsai.
'''
import numpy as np

# note that this has been translated by copilot and is untested!!!
def getCropNums(platforms, plat_coor):
    plat_centre = np.empty((len(platforms), 2))
    for p in range(len(platforms)):
        plat_centre[p,:] = plat_coor[platforms[p]].Centre
    
    plat_centre = np.round(np.mean(plat_centre, axis=0))
    
    plat_x = np.mean([np.min(plat_centre[:,0]), np.max(plat_centre[:,0])])
    plat_y = np.mean([np.min(plat_centre[:,1]), np.max(plat_centre[:,1])])
    
    crop_width = 600
    crop_height = 600
    
    crop_x = plat_x - crop_width/2
    crop_y = plat_y - crop_height/2
    
    if crop_x + crop_width > 2448:
        diff_crop_x = crop_x + crop_width - 2448
        crop_x = crop_x - diff_crop_x
    
    if crop_y + crop_height > 2048:
        diff_crop_y = crop_y + crop_height - 2048
        crop_y = crop_y - diff_crop_y
    
    crop_nums = [crop_x, crop_y, crop_width, crop_height]
    return crop_nums
# note that this has been translated by copilot and is untested!!!