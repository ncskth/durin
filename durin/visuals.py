

import pygame
from pygame.locals import *
import sys
import multiprocessing 
import numpy as np

TOF_WIDTH = 8*8
TOF_HEIGHT = 8

class Viewer:
    def __init__(self, display_size, px_np):
        self.display_size = display_size
        self.px_np = px_np
    
    # def set_title(self, title):
    #     pygame.display.set_caption(title)
    
    def start(self):
        pygame.init()
        scaled_d_size = (self.display_size[0]*20, self.display_size[1]*20)
        display = pygame.display.set_mode(scaled_d_size)
        running = True
        while running:

            Z = self.update()
            surf = pygame.surfarray.make_surface(Z)
            surf = pygame.transform.scale(surf, scaled_d_size)

            display.blit(surf, (0, 0))

            pygame.display.update()
            # time.sleep(1/25)

        pygame.quit()

    def update(self):
        
        # image = 255*np.random.randint(0,2,(8*8,8,3)) #
        image = np.zeros((self.px_np.shape[0],self.px_np.shape[1],3))
        image[:,:,0] = self.px_np

        return image.astype('uint8')

def vis_process(px_np):

    viewer = Viewer((TOF_WIDTH, TOF_HEIGHT), px_np)
    viewer.start()

def launch_visual():

    manager = multiprocessing.Manager()
    px_mp = multiprocessing.Array('I', int(np.prod((TOF_WIDTH, TOF_HEIGHT))), lock=multiprocessing.Lock())
    px_np = np.frombuffer(px_mp.get_obj(), dtype='I').reshape((TOF_WIDTH, TOF_HEIGHT))

    p_visual = multiprocessing.Process(target=vis_process, args=(px_np,))

    return p_visual, px_np