#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import pygame, sys
import os
from pygame.locals import *
import subprocess
# play random game?
#import random
import glob
import re


#FIXME: function to convert string into tuple
# otherwise pygame give me this error:
# TypeError: Invalid foreground RGBA argument
def get_color(string):
    return tuple(int(v) for v in re.findall("[0-9]+", string))

def get_config():
    config = ConfigParser.ConfigParser()
    config.readfp(open("config.cfg"))
    config.readfp(open("skins/"+config.get("config","skin")+"/skin.cfg"))
    colors = []
    colors.append(get_color(config.get("skin","font_color")))
    colors.append(get_color(config.get("skin","back_color")))
    colors.append(get_color(config.get("skin","second_color")))
    colors.append(get_color(config.get("skin","selector_color")))
    machines = []
    for s in config.sections():
        if s != "config" and s != "skin":
            machines.append(dict(config.items(s)))
    return config,colors,machines


config,colors,machines = get_config()
pygame.init()
pygame.mixer.init()
pygame.font.init()
pygame.key.set_repeat(300, 25)
pygame.mouse.set_visible(False)

#screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN|pygame.HWACCEL|pygame.HWSURFACE)
screen = pygame.display.set_mode((0,0),pygame.HWACCEL|pygame.HWSURFACE)
screenX = screen.get_width()
screenY = screen.get_height()
resolution = config.get("skin","resolution").split("x")
convX = float(screenX) / float(resolution[0])
convY = float(screenY) / float(resolution[1])


font_name = "extra/ttf/Orbitron-Regular.ttf"
font2_name = "extra/ttf/QuattrocentoSans-Regular.ttf"
machine_font = pygame.font.Font(font_name, int(100*convY))
font_subtitle = pygame.font.Font(font_name, int(28*convY))
pitems = []

def center_element_in_area(element,area):
    x = area[2]/2 - element.get_width()/2
    y = area[3]/2 - element.get_height()/2
    position = (x+area[0],y+area[1])
    screen.blit(element,position)

def scale_image(image,width=0,height=0,proportion=1):
    img = pygame.image.load(image).convert_alpha()
    w = img.get_width()
    h = img.get_height()
    if height > 0 and width > 0:
        h = height
        w = width
    elif height > 0:
        if proportion:
            h = height
            w = h / float(img.get_height()) * float(img.get_width())
        else:
            h = height
    elif width > 0:
        if proportion:
            w = width
            h = w / float(img.get_width()) * float(img.get_height())
        else:
            w = width
    img = pygame.transform.scale(img, (int(w*convY), int(h*convX)) )
    return img

def scale_position(pos):
    if convX != 1 or convY != 1:
        pos = (pos[0]*convX,pos[1]*convY)
    return pos

def draw_element(image,position):
    position = scale_position(position)
    screen.blit(image,position)

def render_text(text, font, position, color, antialias=1):
    surface = font.render(text,antialias,color)
    draw_element(surface, position)

#this should be changed to more generic function
def paint_element(image, px):
    dy = (-100 * convY) + screenY/2 - image.get_height()/2
    dx = screenX/2- image.get_width()/2+px
    draw_element(image, (dx, dy))

def loadfolder( folder ):
    global currentfolder, pitems
    pitems = []
    currentfolder = folder
    for file in glob.glob(currentfolder+"/*"):
        try:
            filen = file.decode('utf-8')
        except Exception:
            filen = file
            pass
        if os.path.basename(filen) != "README":
            pitems.append ( {"value":filen, "name":os.path.basename(filen)} )
    pitems.sort()



def filesel(title, path, emulator, marquee):
    font_size = int(26*convY)
    font_item = pygame.font.Font(font2_name, font_size)
    list_area = (screenX/16*9, screenY/9, screenX/16*6, screenY/9*7)
    itemh = font_size + 14
    selectmarge = 50
    selectleft = list_area[0]-selectmarge
    visibleitems = int((list_area[3]) / itemh)
    #print list_area[3], list_area[1], itemh
    folder = "machines/"+path+"/roms"
    original_folder = folder
    loadfolder(folder)
    current = 0
    offset = 0
    if marquee:
        marquee = scale_image(marquee)
        trans = scale_image("skins/"+config.get("config","skin")+"/transparent.png",height=marquee.get_height()/2, proportion=0)
    img_folderico = scale_image("skins/"+config.get("config","skin")+"/folder.png")

    while True:
        event = pygame.event.wait()
        screen.fill(colors[3])
        #screen.fill((0,255,0), pygame.Rect(list_area))

        if (event.type == KEYDOWN and event.key == K_ESCAPE) or (event.type == QUIT):
            return

        if event.type == KEYDOWN and (event.key == K_RETURN or event.key == K_RIGHT):
            cpos = current - offset
            #don't crash when the directory is empty
            if current != -1:
                fname = pitems[cpos]["value"];
                if os.path.isdir( fname ):
                    loadfolder( fname )
                else:
                    try:
                        subprocess.call(emulator+[fname])
                    except:
                        print "Can't execute"

        if (event.type == KEYDOWN and event.key == K_LEFT):
            if currentfolder != original_folder:
                dirname = os.path.dirname(currentfolder)
                if dirname == "/":
                    dirname = ""
                loadfolder( dirname )

        if (event.type == KEYDOWN and event.key == K_UP):
            current -= 1
            if current < offset:
                offset = current

        if (event.type == KEYDOWN and event.key == K_DOWN):
            current += 1
            if current - offset >= visibleitems:
                offset +=1

        if (event.type == KEYDOWN and (event.key == K_PAGEDOWN or event.key == K_PAGEUP)):
            if event.key == K_PAGEUP:
                current -= visibleitems
                offset -= visibleitems
            else:
                current += visibleitems
                offset += visibleitems
            if current - offset >= visibleitems:
                offset = current

        #don't go outside pitems
        if current < 0:
            current = 0
        if current >= len(pitems):
            current = len(pitems)-1


        if (current < offset) or (current >= offset+visibleitems):
            offset = current

        if offset >= len(pitems) - visibleitems:
            offset = len(pitems) - visibleitems
        if offset < 0:
            offset = 0

        cpos = current - offset

        if len(pitems) > 0:
            pospaint=0
            rectsel = pygame.Rect( selectleft, (list_area[1]+cpos*itemh-3), list_area[2], itemh-2 )
            screen.fill(colors[1], rectsel)
            for compta in range(0, min(visibleitems, len(pitems) )):
                item = pitems[compta+offset]
                leftpad = 0

                if os.path.isdir( item["value"] ):
                    draw_element(img_folderico, (list_area[0], list_area[1]+(itemh * pospaint)+4))
                    leftpad = 50

                item_name = font_item.render(item["name"], 1, colors[0] if pospaint != cpos else colors[2])
                draw_element(item_name, (list_area[0]+leftpad, list_area[1] + (itemh * pospaint)))
                # FIXME: crop the file name
                if ( item_name.get_width() >= list_area[2]-selectmarge*2 ):
                    item_name = font_item.render("...", 1, colors[0] if pospaint != cpos else colors[2])
                    draw_element(item_name, (list_area[0]+list_area[2]-selectmarge*2, list_area[1]+(itemh * pospaint)))
                pospaint += 1

        if offset+visibleitems < len(pitems):
            item_name = font_item.render("...", 1, colors[1])
            draw_element(item_name, (selectleft , list_area[1]+list_area[3]))
        if offset > 1:
            item_name = font_item.render("...", 1, colors[1])
            draw_element(item_name, (selectleft, list_area[1]-30))

        if len(pitems) > 1:
            npos = list_area[1] + current * list_area[3] / (len(pitems)-1)
            pygame.draw.circle ( screen, colors[1], (int((list_area[0]+list_area[2]+3)), int(npos)), 9)
        render_text(currentfolder,font_subtitle,(screenX/2,screenY/18),colors[1])
        rectsel = pygame.Rect( (list_area[0]+list_area[2]), list_area[1], 6, list_area[3])
        screen.fill(colors[1], rectsel)
        if marquee:
            draw_element(marquee, (screenX/32,screenY/18))
            where = marquee.get_height()
            trans_height = trans.get_height()
            draw_element(trans, (screenX/32,screenY/18 + where - trans_height))
        #rectimg = pygame.Rect( screenX/32*convX, (screenY/18 + where-15)*convY, screenX/2,20*convY)
        #screen.fill((120,120,120), rectimg)
        #draw file selector
        pygame.display.update()

def main():
    for i in machines:
        i["picture"] = scale_image("extra/images/"+i["image"])

    if os.path.exists("skins/"+config.get("config","skin")+"/tada.ogg"):
        tada = pygame.mixer.Sound("skins/"+config.get("config","skin")+"/tada.ogg")
        tada.play()
    ft = scale_image("skins/"+config.get("config","skin")+"/background.png")
    moving = moving_count = moving_start = offsetX = current = 0
    moving_duration = 180
    moving_dist = screenX / 2
    nmachines = len(machines)
    while True:
        screen.fill((236,236,236))
        draw_element(ft, (0,0))

        if moving == 0:
            event = pygame.event.wait()
            if (event.type == KEYDOWN and (event.key == K_q or event.key == K_ESCAPE)) or (event.type == QUIT):
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_RETURN):
                marquee = ""
                if os.path.exists("machines/"+machines[current]["path"]+"/marquee.png"):
                    marquee = "machines/"+machines[current]["path"]+"/marquee.png"
                filesel(machines[current]["name"], machines[current]["path"],machines[current]["exec"].split(" "), marquee)
            if (event.type == KEYDOWN and (event.key == K_LEFT or event.key == K_RIGHT)):
                moving = 1 if (event.key == K_LEFT) else -1
                moving_start = pygame.time.get_ticks()
                pygame.time.set_timer(pygame.USEREVENT, 500)
            draw_element(ft, (0,0))
            nom = machine_font.render(machines[current]["name"], 1, colors[0])
            screen.blit( nom, (screenX/2 - nom.get_width()/2, screenY - int(screenY/4)) )

        if moving != 0:
            moving_time = pygame.time.get_ticks() - moving_start
            if moving_time >= moving_duration:
                offsetX = 0
                current = current  - moving
                current %= nmachines
                moving = 0
            else:
                offsetX = moving_dist * moving_time / moving_duration * moving
        paint_element(machines[current]["picture"], offsetX)
        paint_element(machines[(current + 1) % nmachines]["picture"], offsetX+screenX/2)
        paint_element(machines[(current - 1) % nmachines]["picture"], offsetX-screenX/2)
        pygame.display.update()

if __name__ == "__main__":
    main()
