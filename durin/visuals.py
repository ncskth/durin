
import multiprocessing 
import numpy as np

TOF_WIDTH = 8*8
TOF_HEIGHT = 8

DVS_HEIGHT = 480
DVS_WIDTH = 640


import cv2

def vis_process(dvs_np):

    cv2.namedWindow('win1')

    dvs_px_mat = np.zeros((DVS_HEIGHT,DVS_WIDTH,3))


    while True:
        dvs_px_mat[:,:,2] = dvs_np*255
        cv2.imshow('win1', dvs_px_mat)
        cv2.waitKey(1) 



def launch_visual():


    manager = multiprocessing.Manager()

    dvs_mp = multiprocessing.Array('I', int(np.prod((DVS_HEIGHT, DVS_WIDTH))), lock=multiprocessing.Lock())
    dvs_np = np.frombuffer(dvs_mp.get_obj(), dtype='I').reshape((DVS_HEIGHT, DVS_WIDTH))

    p_visual = multiprocessing.Process(target=vis_process, args=(dvs_np,))

    return p_visual, dvs_np