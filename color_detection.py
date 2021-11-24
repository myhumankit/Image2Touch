import math
import numpy as np
import cv2
from scipy.cluster.hierarchy import ward, fcluster
from scipy.spatial.distance import pdist

def findColors(imagePath):
    # Reads the image and converts to RGB
    img = cv2.cvtColor(cv2.imread(imagePath), cv2.COLOR_BGR2RGB)
    # Flattened list of the pixel values
    pixel_list = np.reshape(img, [img.shape[0]*img.shape[1], 3])
    
    # Lists all unique colors
    color_list, cl_index, cl_inverse, cl_count = np.unique(pixel_list, axis=0, return_index=True, return_inverse=True, return_counts=True)

    # Makes a small sample of colors by imitating the color rations in the original image. It has all unique colors.
    color_list_duplicates = color_list
    for x, c in zip(color_list, cl_count):
        for i in range(max(1, math.floor(100*c/(img.shape[0]*img.shape[1])))):
            color_list_duplicates = np.append(color_list_duplicates, [x], axis=0)
            
    # Ward clustering
    y = pdist(color_list_duplicates)
    Z = ward(y)
    labels = fcluster(Z, 100, criterion='distance')
    
    # processes color means for each class
    unique_labels = np.unique(labels)
    sums = [[0,0,0] for _ in unique_labels]
    counts = [0 for _ in unique_labels]
    color_to_label = {(x,y,z):label-min(unique_labels) for label,[x,y,z] in zip(labels[0:len(color_list)], color_list)}
    def temp_fn(c):
        x,y,z = c
        label = color_to_label[(x, y, z)]
        counts[label] += 1
        sums[label] = [x+y for x,y in zip(sums[label], c)]
        
    any(temp_fn(c) for c in pixel_list)
    means = [[int(round(x/c)) for x in s] for s,c in zip(sums, counts)]
    
    # Filters classes that appear in at least 0.2% of the image
    relevant_colors = [[math.floor(r),math.floor(g),math.floor(b)] for [r,g,b],c in zip(means, counts) if c > (img.shape[0] * img.shape[1])/500]
    
    # Translates to HEX
    color_hexes = ['#%02x%02x%02x' % (r, g, b) for [r,g,b] in relevant_colors]
    
    return color_hexes
    