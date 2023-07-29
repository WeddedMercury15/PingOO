import pygame
from pygame.locals import *
import sys

pygame.init()
display = (800, 600)
screen = pygame.display.set_mode(display, DOUBLEBUF)

bowl_img = pygame.image.load('cheems.png')  # 替换为碗的图像文件路径
bowl_img = pygame.transform.scale(bowl_img, (270, 270))

angle = 0

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((255, 255, 255))

    rotated_bowl = pygame.transform.rotate(bowl_img, angle)
    rotated_rect = rotated_bowl.get_rect(center=(display[0] // 2, display[1] // 2))
    screen.blit(rotated_bowl, rotated_rect)

    pygame.display.flip()
    pygame.time.wait(10)

    angle += 1
    if angle >= 360:
        angle = 0
