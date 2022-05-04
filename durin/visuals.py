
import multiprocessing 
import numpy as np

TOF_WIDTH = 8 #8*8
TOF_HEIGHT = 8

DVS_HEIGHT = 480
DVS_WIDTH = 640


import cv2

    

def vis_process(dvs_np, tof_np, ev_count):

    cv2.namedWindow('Dashboard')

    ext = 120
    img_mat = np.zeros((DVS_HEIGHT, DVS_WIDTH+ext*4,3))
    dvs_px_mat = np.zeros((DVS_HEIGHT,DVS_WIDTH,3))
    tof_px_mat = np.zeros((TOF_HEIGHT,TOF_WIDTH,3))


    font = cv2.FONT_HERSHEY_TRIPLEX
    org = (830, 60)
    fontScale = 1
    color = (255, 255, 255)
    thickness = 2
    md = 2000 # 

    while True:

        helper = (tof_np)/md
        tof_px_mat[:,:,1] = np.where(helper>md, md, helper)
        img_mat[:,DVS_WIDTH:DVS_WIDTH+4*ext,:] = np.zeros((DVS_HEIGHT, 4*ext, 3)) #to clean
        img_mat[ext-1:3*ext+1,ext+DVS_WIDTH-1:DVS_WIDTH+ext*3+1,:] = np.ones((2*ext+2,2*ext+2,3))*255
        img_mat[ext:3*ext,ext+DVS_WIDTH:DVS_WIDTH+ext*3,:] = cv2.resize(tof_px_mat,(2*ext, 2*ext), interpolation = cv2.INTER_NEAREST)
        img_mat[:,0:DVS_WIDTH,2] = np.transpose(dvs_np*255)

        img_mat = cv2.putText(img_mat, "Durin", org, font, fontScale, color, thickness, cv2.LINE_AA)
        img_mat = cv2.putText(img_mat, f"{ev_count.value} ev/s", (760,420), font, fontScale, color, thickness, cv2.LINE_AA)

        cv2.imshow('Dashboard', img_mat)
        cv2.waitKey(1) 



def launch_visual():


    manager = multiprocessing.Manager()

    dvs_mp = multiprocessing.Array('I', int(np.prod((DVS_WIDTH, DVS_HEIGHT))), lock=multiprocessing.Lock())
    dvs_np = np.frombuffer(dvs_mp.get_obj(), dtype='I').reshape((DVS_WIDTH, DVS_HEIGHT))

    tof_mp = multiprocessing.Array('I', int(np.prod((TOF_HEIGHT, TOF_WIDTH))), lock=multiprocessing.Lock())
    tof_np = np.frombuffer(tof_mp.get_obj(), dtype='I').reshape((TOF_HEIGHT, TOF_WIDTH))

    ev_count = multiprocessing.Value('i', 0)


    p_visual = multiprocessing.Process(target=vis_process, args=(dvs_np, tof_np, ev_count,))

    return p_visual, dvs_np, tof_np, ev_count