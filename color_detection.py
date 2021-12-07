import math
import numpy as np
import cv2
from scipy.cluster.hierarchy import ward, fcluster
from scipy.spatial.distance import pdist, euclidean
from tempfile import mkstemp

def findColorsAndMakeNewImage(imagePath):
    """Finds the different colors used in the image and makes a new one using only flat coloring

    Args:
        imagePath (string): The path to the image to analyze

    Returns:
        (list(string), imgae): the hex representations of the colors, and the path to the flat image
    """
    
    # Parameters that could become arguments
    carre_distance_min = 500
    prct = .003
    min_same_neighbours = 4
    
    
    ## Part 1 : finding the different colors
    
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
    labels = fcluster(Z, carre_distance_min, criterion='distance')
    
    # processes color means for each class
    unique_labels = np.unique(labels)
    sums = [[0,0,0] for _ in unique_labels]
    counts = [0 for _ in unique_labels]
    color_to_label = {(x,y,z):label for label,[x,y,z] in zip(labels[0:len(color_list)], color_list)}
    color_to_label_idx = {(x,y,z):label-min(unique_labels) for label,[x,y,z] in zip(labels[0:len(color_list)], color_list)}
    def temp_fn(c):
        x,y,z = c
        label = color_to_label_idx[(x, y, z)]
        counts[label] += 1
        sums[label] = [x+y for x,y in zip(sums[label], c)]
        
    any(temp_fn(c) for c in pixel_list)
    means = [[int(round(x/c)) for x in s] for s,c in zip(sums, counts)]
    
    # Filters classes that appear in at least 0.3% of the image
    relevant_labels = [l for l,c in zip(unique_labels, counts) if c > img.shape[0] * img.shape[1] * prct]
    relevant_colors = [[math.floor(r),math.floor(g),math.floor(b)] for l, [r,g,b] in zip(unique_labels, means) if l in relevant_labels]
    relevant_label_to_mean = {l:c for l,c in zip(relevant_labels, relevant_colors)}
    
    # Translates to HEX
    color_hexes = ['#%02x%02x%02x' % (r, g, b) for [r,g,b] in relevant_colors]

    
    ## Part 2 : making the new image    

    # For each unique color in the image, associate a label from relevant_labels, or a default value
    no_label = -42
    def get_closest_label(c):
        [r,g,b] = c
        orig_label = color_to_label[(r,g,b)]
        if orig_label in relevant_labels:
            return orig_label
        else:
            return no_label
    # The results are precomputed for performance reasons
    color_to_relevant_label = {(r,g,b):get_closest_label([r,g,b]) for [r,g,b] in color_list}
    # We apply the results to every pixel in the image
    pixel_list_labels = [color_to_relevant_label[(r,g,b)] for [r,g,b] in pixel_list]
        
    # In the following loop, we will classify the pixels that don't have a label yet
    firstIter = True
    pixel_list_2 = pixel_list
    while any(l for l in pixel_list_labels if l == no_label):
        # This first step will make 9 clones of the "image" (with labels instead of pixels), slightly shifted
        img_labels = np.reshape(pixel_list_labels, [img.shape[0],img.shape[1]])
        img_border = cv2.copyMakeBorder(img_labels, 1, 1, 1, 1, cv2.BORDER_CONSTANT, None, no_label)
        img_labels_shift = [img_border[1+shiftx:img_border.shape[0]-1+shiftx, 1+shifty:img_border.shape[1]-1+shifty] for (shiftx, shifty) in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)]]
        # The 9 clones are aggregated to make a single 3D array : each 2D "pixel" has a list of 9 labels (his own, plus the labels of its 8 neighbours)
        img_labels_shift_stack = np.dstack(img_labels_shift)
        # We convert this array into a list for easier handling
        pixel_possible_labels_list = np.reshape(img_labels_shift_stack, [img.shape[0]*img.shape[1], 9])

        # The first iteration will invalidate the labels of pixels that seem to be isolated (less than min_same_neighbours neighbours of the same label)
        if firstIter:
            pixel_list_labels = [(label if (label != no_label and sum(1 for pl in possible_labels if pl == label) >= min_same_neighbours)
                                else no_label)
                        for label, possible_labels in zip(pixel_list_labels, pixel_possible_labels_list)]
        # The next steps will, for each pixel of unknown label, choose the label with the closest color, among the neighbours' labels
        else:
            pixel_list_labels = [(label if label != no_label
                        else (no_label if not any(pl for pl in possible_labels if pl != no_label)
                        else min([(pl, relevant_label_to_mean[pl]) for pl in possible_labels if pl != no_label], key=lambda labAndMean: euclidean(pixel, labAndMean[1]))[0]))
                        for pixel, label, possible_labels in zip(pixel_list, pixel_list_labels, pixel_possible_labels_list)]

        firstIter = False
    
    # Once all pixels have a label, we rebuild the image
    pixel_list_2 = [relevant_label_to_mean[label] for label in pixel_list_labels]
    img_2 = np.reshape(pixel_list_2, img.shape).astype(np.uint8)
    
    # Writes the image to a temporary location
    _, image_path = mkstemp(suffix=".png")
    img_2_bgr = cv2.cvtColor(img_2, cv2.COLOR_RGB2BGR)
    cv2.imwrite(image_path, img_2_bgr)
    
    return color_hexes, image_path
    