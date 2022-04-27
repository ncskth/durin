
import multiprocessing 
import numpy as np

TOF_WIDTH = 8*8
TOF_HEIGHT = 8


import cv2

def vis_process(px_np):

    tof_px_mat = np.zeros((TOF_HEIGHT,TOF_WIDTH+7,3))
    for i in range(7):
        tof_px_mat[:,i+i*8+8,0:3] = np.ones((8,3))*255

    # md: max distance
    md = 6000 #6[m]

    while True:
        for i in range(8):
            # tof_px_mat[:,i+i*8:i+i*8+8,2]= px_np[:,i*8:i*8+8]/(2**16-1)
            tof_px_mat[:,i+i*8:i+i*8+8,2]= (np.ones((8,8))*md - px_np[:,i*8:i*8+8])/md
        im_final = cv2.resize(tof_px_mat,(1280, int(1280*TOF_HEIGHT/(TOF_WIDTH+7))), interpolation = cv2.INTER_NEAREST)
        cv2.imshow("ToF Sensors", im_final)
        cv2.waitKey(1) 



def launch_visual():

    manager = multiprocessing.Manager()
    px_mp = multiprocessing.Array('I', int(np.prod((TOF_HEIGHT, TOF_WIDTH))), lock=multiprocessing.Lock())
    px_np = np.frombuffer(px_mp.get_obj(), dtype='I').reshape((TOF_HEIGHT, TOF_WIDTH))

    p_visual = multiprocessing.Process(target=vis_process, args=(px_np,))

    return p_visual, px_np