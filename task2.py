from load_data import load_data
import os
from matplotlib import pyplot as plt
import numpy as np
import cv2
from vispy.color import ColorArray
from PIL import Image

# Goal: draw lines between box vertices
# Input: img = the image on which bbox would be drawn
#        image_corners = the list of 3d bbox vertices 
# Output: an image with bbod drawn on it
def draw_line_between_pts(img, image_corners):
    thickness = 2
    color = (0,255,0)
    radius = 2
    corners = image_corners
    for box in corners:
        for corner in box:
            img = cv2.circle(img,tuple(corner[:-1]),radius,color,thickness) # draw all corner points as well
        # (0,1),(0,3),(0,4),(1,2),(1,5),(2,3),(2,6),(3,7),(4,5),(4,7),(5,6),(6,7)
        img = cv2.line(img,tuple(box[0,:-1].astype(int)),tuple(box[1,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[0,:-1].astype(int)),tuple(box[3,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[0,:-1].astype(int)),tuple(box[4,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[1,:-1].astype(int)),tuple(box[2,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[1,:-1].astype(int)),tuple(box[5,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[2,:-1].astype(int)),tuple(box[3,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[2,:-1].astype(int)),tuple(box[6,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[3,:-1].astype(int)),tuple(box[7,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[4,:-1].astype(int)),tuple(box[5,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[4,:-1].astype(int)),tuple(box[7,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[5,:-1].astype(int)),tuple(box[6,:-1].astype(int)),color,thickness)
        img = cv2.line(img,tuple(box[6,:-1].astype(int)),tuple(box[7,:-1].astype(int)),color,thickness) # draw each line 
    return img


# Goal: draw a bbox on the image
# Param: img = the image on which bbox would be drawn
#        objects = the object list
#        R1 = extrinsic matrix, unused as we would create T for extrinsic matrix
#        R2 = intrinsic matrix
# Output: an image with all bboxes 
def draw_bbox( img , objects , R1 , R2 ):
    number_of_objects = len(objects) # number of objects 
    corners = np.empty([number_of_objects,8,3]) # array that will hold all objects corners in 3D world coordinates
    i = 0
    for individual in objects:
        ''' 3 dimensions 3D object dimensions: height, width, length (in meters)
        3 location 3D object location x,y,z in Cam 0 coordinates (in meters) describing the center
        of the bottom face of the bounding box '''
        # Height, Width, Length 
        dimension = np.array(individual[8:11])
        bbox_height = dimension[0]
        bbox_width = dimension[1]
        bbox_length =  dimension[2]
        # # Right, Down, Front (X,Y,Z)
        location = np.array(individual[11:14])
        bbox_x = location[0]
        bbox_y = location[1]
        bbox_z = location[2]
        rotation_y = individual[14]
        corner = np.zeros([8,3])
        # corner[0,:] = location + np.array([bbox_width/2,-bbox_height, bbox_length/2])
        # corner[1,:] = corner[0,:] + np.array([-bbox_width ,0 , 0])
        # corner[2,:] = corner[1,:] + np.array([0 ,0,-bbox_length])
        # corner[3,:] = corner[2,:] + np.array([bbox_width, 0, 0])
        # corner[4,:] = corner[0,:] + np.array([0, bbox_height ,0])
        # corner[5,:] = corner[4,:] + np.array([-bbox_width,0, 0])
        # corner[6,:] = corner[5,:] + np.array([0,0,-bbox_length])
        # corner[7,:] = corner[6,:] + np.array([bbox_width,0,0])



        corner[0,:] = location + np.array([bbox_length/2,-bbox_height,bbox_width/2])
        corner[1,:] = corner[0,:] + np.array([-bbox_length,0,0])
        corner[2,:] = corner[1,:] + np.array([0,0,-bbox_width])
        corner[3,:] = corner[2,:] + np.array([bbox_length,0,0])
        for ind in range(4):
            corner[ind+4,:] = corner[ind,:] + np.array([0,bbox_height,0])
        # Rotate along the y-axis
        T = np.array([[location[0]],[location[1]-bbox_height/2],[location[2]]])
        R = np.array([[np.cos(rotation_y),0,np.sin(rotation_y)],[0,1,0],[-np.sin(rotation_y),0,np.cos(rotation_y)]])
        R1 = np.block([[R,np.dot(-R,T)+T],[0,0,0,1]])
        ind = 0
        for point in corner:
            pos = np.dot(np.dot(R2,R1),np.concatenate((point,[1])))
            pos /= pos[-1]
            corner[ind,:] = pos
            ind += 1
        corners[i,:,:] = corner
        i += 1
    #R = data['P_rect_00']
    # T = A homogeneous translation matrix of 4x4 dimension
    # Used to transform cam0 -> cam2
    # T = np.eye(4)
    # T[0,3] = 0.06

    # Loop over each corner lists 
    # for bbox in corners:
    #     for ind,pt in enumerate(bbox):
    #         pos = np.dot(R2,np.concatenate((pt,[1])))
    #         pos /= pos[-1]
    #         pos = pos.astype(int)
    #         bbox[ind]=pos
    
    # Casting pixels into integer points
    corners = corners.astype(int,copy=False)
    # Draw lines between them
    img = draw_line_between_pts(img , corners)
    return img  



def project_lidar_data_on_image(data  , objects , img , bbox = "no"):
    ''' This method inputs the data to get all the matrices, as well as the object array for segmentation
    also it has a flag for bbox drawing. Finally, it has an image input (uint8)((height,width ,3)) '''
    R1 = data["T_cam0_velo"] # this consitutes our extrinsic parameters matrix
    R2 = data["P_rect_20"] #this constitues our intrinsic parameters matrix
    # Both R1 and R2 constitute the camera calibration of our scene that helps project the 3D lidar points to a 2D image plane
    velodyne = data['velodyne']
    points = velodyne [:,:-1] # keep only the 3 dimensions of velodyne data 
    # Forward direction only => Filter out the points of the backward direction
    ind = points[:,0]>=0 # keep only the points that have an x>=0
    points = points[ind] #keep the points only with the corresponding indeces
    #this will be used for the laser id
    label_clip = data['sem_label'][ind] # get the semantic labels for each point of the cloud


    # Homonegenous
    P = np.concatenate([points,np.ones([points.shape[0],1])],axis=1)
    # Multiply different parameter matrices to project 3D points on the 2D camera 2 image

    #Extrinsic & intrinsic
    print("The shape of the homogenous lidar points is ", P.shape)
    print("The shape of the intrinsic matrix is ", R2.shape)
    print("The shape of the extrinsic matrix is ", R1.shape)

    P_2 = np.empty(points.shape)

    for ind,point in enumerate(P):
        # Projection
        P_2[ind,:] = np.dot(np.dot(R2,R1),point)  # project for each point of the the Lidar = (1x3)
        # Normalization
        P_2[ind,:] = P_2[ind,:]/P_2[ind,-1] #normalize with the last element, to end up with 1 in the last dimension -> homogenous coordinates

    print("The final 2D projected data have shape ", P_2.shape)

    P_2 = P_2.astype(int) #this are all the 2D projected data



    #Check the pixel values for each point
    i = 10 #ith point of cloud 
    print("For a random point of the cloud we have ", P_2[i] , "with u = " ,P_2[i][1], " and v = " , P_2[i][0])
    print("Remember that the camera coordinates are different => Camera: x: right, y: down, z: forward . Think of how the velodyne would look from the camera coordinates perspective")
    print("Remember that for our image we can only have pixel locations within (u,v) range of the image =>" ,  (img.shape[0], img.shape[1]))

    # For all the remaining points filter out, the points that do not correspond to a pixel location in our frame
    ind_x = np.logical_and(P_2[:,1] < img.shape[0], P_2[:,1] >= 0) # we accept only P_2 pixels that are => 0 and within the appropariate image shape 
    ind_y = np.logical_and(P_2[:,0] < img.shape[1], P_2[:,0] >= 0) # why are u,v reversed in the P_2 shape ?
    ind_z = P_2[:,-1]>=0
    ind = np.logical_and(ind_x,ind_y) # we want first criterion t be true , as well as the second 
    ind = np.logical_and(ind,ind_z) # not sure if this one is needed


    #Convert the index to integer
    projected_cloud_pixels = P_2[ind] # projected 3D cloud lidar points on 2D image
    points = points[ind] # these are the corresponding 3D lidar points shown in the image
    label_clip = label_clip[ind]
    print("The label segmentation matrix has the numeric segmentation labels , e.g for point 1", label_clip[0])


    # Color for each pixel position
    color = np.empty([projected_cloud_pixels.shape[0],3]) #this matrix will hold all the colors for the image 
    ''' color map is a dictionary which maps numeric semantic labels to a BGR color for visualization. (Careful, not RGB!)
    Example: 10: [245, 150, 100] # car, blue-ish '''
    color_map = data['color_map']

    for ind,label in enumerate(label_clip):
        color[ind,:] = color_map [label[0]]  # color the corresponding index in the image 
        color[ind,:] = [color[ind,-1],color[ind,1],color[ind,0]]
    #color = ColorArray(color,clip=True)



    for i,point in enumerate(projected_cloud_pixels):
        u = point[1] # corresponds to y
        v = point[0] # corresponds to x 
        img = cv2.circle(img, (v,u), radius=1, color=color[i,:] , thickness=1) # make pixels more visible
        #img[point[1],point[0],:] = color[i,:]


    if bbox == 'no':
        # don't draw bbox rectangles
        print("With no bbox rectangles draw on image")
    else: 
        img  = draw_bbox(img , objects , R1 , R2)
        

    img_array = img
    


    return points ,projected_cloud_pixels , img_array



########################################### MAIN ################################
def main():
    print("So let's start the task")
    data_path = os.path.join("./data", "data.p") # change to data.p for submission
    data = load_data(data_path)
    velodyne =  data['velodyne']
    objects = data['objects']
    #Get image and display it
    image= data['image_2']
    print( "our image is ", image.dtype)
    image = np.uint8(image) #convert uint32 to uint8 with RGB channels
    print( "our image is ", image.dtype , " with shape " , image.shape)
    image_original = np.copy(image)

    '''#Cv2 display
    cv2.imshow('image' , img)
    cv2.waitKey(2000) 
    #PIL method 
    image= Image.fromarray(image, "RGB")
    image.show("hey") '''
    lidar_points , projected_points , output_image_array  = project_lidar_data_on_image(data , objects , image , bbox = 'yes')
    #save image
    cv2.imwrite("task2.jpg" , output_image_array) 
    #PIL method
    image= Image.fromarray(output_image_array, "RGB")
    image.show("POINT CLOUD ON IMAGE TASK 2")       


if __name__ == "__main__":
    main()
