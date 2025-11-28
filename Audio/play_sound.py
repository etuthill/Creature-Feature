import pygame
import time

pygame.mixer.init()
pygame.mixer.music.load("omnomnom_mixdown.wav") 
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    time.sleep(0.1)