#! /usr/bin/env python

#mathtests.py
#A selection of 3D spacial math tests for a possible space game 

#Author
#======
#Jess Hill (Jestermon)
#jestermon.weebly.com
#jestermonster@gmail.com

#resources
#==========
#Planetary maps from ~ http://planetpixelemporium.com/index.php
#Models and other resources by the author

#dependencies:
#=============
#python   ~ http://www.python.org
#pygame   ~ http://www.pygame.org
#pyopengl ~ http://pyopengl.sourceforge.net
#pyggel (included)  ~ http://http://code.google.com/p/pyggel/downloads/list
#PIL      ~ http://www.pythonware.com/products/pil/
#numpy    ~ http://numpy.scipy.org/
#psyco    ~ http://psyco.sourceforge.net  (not required, but handy to speed things up)
#euclid (included) ~ from the Pyweek delta-v game by Alex Holkner ~http://www.pyweek.org/e/ambling/

#NOTE
#====
#Refer to the included pyggel library for documentation
#Refer to the included euclid.txt for documentation on euclid

import sys
sys.path += ['.']

import pyggel
import math
from math import *
from euclid import *
import random
import view
import scene
import light
import camera
import event
import pygame
import geometry
import font
import mesh as me
import __init__

        
########################################
class Model:
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self,mesh):
        self.model = mesh
        self.rotation_speed = 0
        self.orbit_angle = (0,0,0)
        self.velocity = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.oldx = 0
        self.oldy = 0
        self.oldz = 0
        self.xspeed = 0
        self.yspeed = 0
        self.zspeed = 0
        self.mass = 3      

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def cleanAngles(self,rotation):
        """Clean all negative angles to give positive values"""
        rx,ry,rz = rotation
        if rx < 0:
            rx += 360
        rx = rx%360
        if ry < 0:
            ry += 360
        ry = ry%360
        if rz < 0:
            rz += 360
        rz = rz%360            
        return rx,ry,rz

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def translateToCenter(self,source,destination):
        """Translates destination co-ords to 0,0,0 offset from source"""
        sx,sy,sz = source
        dx,dy,dz = destination
        x=dx-sx; y=dy-sy; z=dz-sz
        return x,y,z

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def translateFromCenter(self,source,destination):
        sx,sy,sz = source
        dx,dy,dz = destination
        x=dx-sx; y=dy-sy; z=dz+sz
        return x,y,z
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getRotationAngles(self,source,destination):
        srcx,srcy,srcz = source
        dstx,dsty,dstz = destination
        dx=float(dstx-srcx); dy=float(dsty-srcy); dz=float(dstz-srcz)
        yrot = atan2(dx, dz)
        xrot = atan2(abs(dy), sqrt((abs(dx) * abs(dx)) + (abs(dz) * abs(dz))))
        xdeg = degrees(xrot)
        ydeg = degrees(yrot)
        zdeg = 0
        rx,ry,rz = self.cleanAngles((xdeg,-ydeg,zdeg))  
        return rx,ry,rz

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getRotationPos(self,point,rotation):
        rx = radians(rotation[0])
        ry = radians(rotation[1])
        rz = radians(rotation[2])
        center = Vector3(float(point[0]),float(point[1]),float(point[2])) 
        newpoint = Matrix4.new_rotate_euler(ry, rx, rz)*center    
        return (newpoint.x, newpoint.y, newpoint.z)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getDistance(self,point1,point2):
        x1,y1,z1 = point1
        p = Vector3(x1,y1,z1)
        x2,y2,z2 = point2
        q = Vector3(x2,y2,z2)
        n = p-q
        return sqrt(n.x**2 + n.y**2 + n.z**2)        

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def moveTowards(self,destination):
        climb_rate = 1.5
        x1,y1,z1 = self.getRotation()
        x2,y2,z2 = self.getRotationAngles(self.getPosition(),destination)
        x = y = z = 0
        #First adjust y-rotation 
        dy = y2-y1
        if dy <= 0:
            y = y1 - self.rotation_speed
        if dy > 0:
            y = y1 + self.rotation_speed
            
        #Next compensate for up down motion
        px,py,pz = self.getPosition()
        dsx,dsy,dsz = destination
        if dsy < py:
            self.setPosition((px,py-self.velocity/climb_rate,pz))
        if dsy > py:
            self.setPosition((px,py+self.velocity/climb_rate,pz))
        self.setRotation((x,y,z))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getDirectionVector(self):
        dv =  self.getRotationPos((0,0,self.velocity),self.getRotation())
        return dv
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def move(self):
        vx,vy,vz = self.getDirectionVector()
        tx,ty,tz = self.translateFromCenter((vx,vy,vz),self.getPosition())
        self.setPosition((tx,ty,tz))
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def rotate(self):
        """rotate the model in place, along y-axis"""
        x,y,z = self.model.rotation
        y += self.rotation_speed
        self.model.rotation = (x,y,z)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setPosition(self,position):
        """set position of model"""
        self.model.pos = position    

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getPosition(self):
        """get position of model"""
        return self.model.pos

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setRotation(self,rotation):
        """set new rotation for model"""
        rx,ry,rz = self.cleanAngles(rotation)
        self.model.rotation = (rx,ry,rz)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getRotation(self):
        """get rotation of model"""
        x,y,z = self.model.rotation
        rx,ry,rz = self.cleanAngles((x,y,z))
        self.model.rotation = (rx,ry,rz)
        return self.model.rotation

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def scale(self,scale):
        """scale the model"""
        self.model.scale = scale

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def hide(self):
        """hide the model"""
        self.model.visible = False

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def show(self):
        """show the model"""
        self.model.visible = True


########################################world
class World:
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        self.initialise()
        self.setupValues()
        self.loadModels()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def initialise(self):
        #initialize pygel screen
        view.init(screen_size=(800,600))
        #create pygel scene
        self.scene = scene.Scene()
        #Set window title
        view.set_title("3D Spatial Math Tests in Python")
        #create a pygel light
        self.light = light.Light((10,0,0),
                          (0.1,0.1,0.1,1),#ambient color
                          (1,1,1,1),#diffuse color
                          (10,10,10,5),#specular
                          (0,0,0),#spot position
                          False) #directional, not a spot light
        self.scene.add_light(self.light)
        self.light2 = light.Light((0,0,-2),
                          (0.1,0.1,0.1,1),#ambient color
                          (0.1,0.1,0.1,1),#diffuse color
                          (1,1,1,1),#specular
                          (0,0,0),#spot position
                          True) #directional, not a spot light
        self.scene.add_light(self.light2)
        
        #create third person camera
        self.world_center = (0,0,0)
        self.camera = camera.LookAtCamera(self.world_center,distance=10)
        #create first person camera
        self.camera2 = camera.LookFromCamera((0,0,-10),(0,-5,0))
        #setup pygel event handler
        self.event_handler = event.Handler()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setupValues(self):
        self.scene.pick = True
        self.events = event.Handler()
        self.clock = pygame.time.Clock()
        self.mousedown = None
        self.mousebutton = None
        self.twomousebuttons = False
        self.mouseX = None
        self.mouseY = None
        self.mousemoveX = None
        self.mouseMoveY = None
        self.leftmousebutton = 1
        self.middlemousebutton = 2
        self.rightmousebutton = 3
        self.mousewheelup = 4
        self.mousewheeldown = 5
        self.mouse_over_object = None
        self.object_selected = None
        self.do_once = False
        self.delta = 0
        self.labels = []
        self.movelabels = False
        self.cameratype = 0 #type 0=third person, 1=first person
        self.rot = 0
        self.models = {}
        self.currentkey = None
        self.grid = []
        self.pointlist = ['point1','point2','point3','point3','point4','point5']
        self.tempmodels = []
        self.testnumber = 1

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def deleteGrid(self):
        for g in self.grid:
            self.scene.remove_3d(g)
            del g
        self.grid=[]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def createGrid(self,lower,upper,step):
        self.deleteGrid()
        x1,y1,z1 = lower
        x2,y2,z2 = upper
        for xx in range(x1,x2,step):
            gridline = geometry.Lines((xx,0,x1),(xx,0,x2),colorize=(0.1,0.1,0.1))
            self.scene.add_3d(gridline)
            self.grid.append(gridline)
        for zz in range(z1,z2,step):
            gridline = geometry.Lines((z1,0,zz),(z2,0,zz),colorize=(0.1,0.1,0.1))
            self.scene.add_3d(gridline)
            self.grid.append(gridline)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def loadAxis(self):
        self.lineZ = geometry.Lines((0,0,-300),(0,0,300),colorize=(1,0,0))
        self.scene.add_3d(self.lineZ)
        self.lineX = geometry.Lines((-300,0,0),(300,0,0),colorize=(0,1,0))
        self.scene.add_3d(self.lineX)
        self.lineY = geometry.Lines((0,-300,0),(0,300,0),colorize=(0,0,1))
        self.scene.add_3d(self.lineY)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def makeLabel(self,text,size,pos):
        font = font.Font3D(None, size)        
        text1 = font.make_text_image(text)
        text1.pos = pos
        self.scene.add_3d_blend(text1)
        self.labels.append(text1)
        return text1

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def loadModels(self):
        #load axis core
        self.loadAxis()

        #load meshes from file
        self.loadMesh('crux','data/crux.obj')
        self.loadMesh('earth','data/earthmesh.obj')
        self.loadMesh('sun','data/sunmesh.obj')
        self.loadMesh('pointer','data/pointer.obj')
        self.loadMesh('moon','data/moonmesh.obj')
        self.loadMesh('mars','data/marsmesh.obj')
        self.loadMesh('jupiter','data/jupitermesh.obj')        
        self.loadMesh('eagle','data/eagleship.obj')        
        
        #load skyball
        self.skyball = geometry.Skyball("data/stars.jpg")
        self.scene.add_skybox(self.skyball)
        self.line1 = geometry.Lines((0,0,0),(10,0,0))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def copyModel(self,source,destination):
        mesh = self.models[source].model.copy()
        mesh.scale = self.models[source].model.scale
        self.scene.add_3d(mesh)
        meshmodel = Model(mesh)
        self.models[destination] = meshmodel        
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def loadMesh(self,name,filename):
        """Load 3D .obj meshe from file"""
        mesh = me.OBJ(filename,pos=(0,0,0))
        mesh.scale = 0.1 #default scale
        self.scene.add_3d(mesh)
        meshmodel= Model(mesh)
        self.models[name] = meshmodel        

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def hideModels(self):
        """hide all 3d models"""
        for m in self.models:
            try:
                self.models[m].hide()
            except:
                pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def deleteModel(self,name):
        try:
            self.scene.remove_3d(self.models[name].model)
        except:
            pass
        try:
            del self.models[name].model
        except:
            pass
        try:
            del self.models[name]
        except:
            pass
            
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def resetCamera(self):
        """reset 3rd person camera"""
        self.camera.rotx =0
        self.camera.roty =0
        self.camera.rotz =0

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def focusCamera(self, focus):
        self.camera.posx, self.camera.posx, self.camera.posz = focus

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setCameradistance(self,distance):
        self.camera.distance = distance

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def placeCamera(self,focus,rotation,distance):
        """focus, place and rotate 3rd person camera"""
        self.camera.posx, self.camera.posx, self.camera.posz = focus
        self.rotateCamera(rotation)
        self.camera.distance = distance        
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def rotateCamera(self,rotation):
        """rotate 3rd person camera based on mouse movement"""
        x,y,z = rotation
        self.camera.rotx += x
        self.camera.roty += y
        self.camera.rotz += z

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getCameraRotation(self):
        return self.camera.rotx, self.camera.roty, self.camera.rotz
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getDistance(self,point1,point2):
        """Get distance between 2 bodies. ~ see euclid for Vector3"""
        x1,y1,z1 = point1
        p = Vector3(x1,y1,z1)
        x2,y2,z2 = point2
        q = Vector3(x2,y2,z2)
        n = p-q
        return sqrt(n.x**2 + n.y**2 + n.z**2)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getRotationPos(self,point,rotation):
        """Returns a tuple 'newpoint' when 'point' is rotated by 'rotation' at (0,0,0)"""
        rx = radians(rotation[0])
        ry = radians(rotation[1])
        rz = radians(rotation[2])
        center = Vector3(float(point[0]),float(point[1]),float(point[2])) 
        newpoint = Matrix4.new_rotate_euler(ry, rx, rz)*center    
        return (newpoint.x, newpoint.y, newpoint.z)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def translateToCenter(self,source,destination):
        """Translates destination co-ords to 0,0,0 offset from source"""
        sx,sy,sz = source
        dx,dy,dz = destination
        x=dx-sx; y=dy-sy; z=dz-sz
        return x,y,z

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def translateFromCenter(self,source,destination):
        """Translates destination co-ords back from 0,0,0 to source"""
        sx,sy,sz = source
        dx,dy,dz = destination
        x=dx+sx; y=dy+sy; z=dz+sz
        return x,y,z

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def orbit_planet(self,orbiting_planet,center_planet):
        orbiting_planet_position = self.models[orbiting_planet].getPosition()
        center_planet_position = self.models[center_planet].getPosition()
        rx,ry,rz = self.models[orbiting_planet].orbit_angle
        rotation = (rx,ry,rz)
        temp_position = self.translateToCenter(center_planet_position,orbiting_planet_position)
        newpos = self.getRotationPos(temp_position,rotation)    
        newpos = self.translateFromCenter(center_planet_position,newpos)
        self.models[orbiting_planet].setPosition(newpos)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def r2d(self,rad):
        """convert radians to degrees"""
        return degrees(rad)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def d2r(self,deg):
        """convert degrees to radians"""
        return radians(deg)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getVectorAngle(self,v1,v2):
        """Return the angle between 2 vectors using arccos dotproduct"""
        x1,y1,z1 = v1
        x2,y2,z2 = v2
        L1 = x1*x1 + y1*y1 + z1*z1  #length of v1
        L2 = x2*x2 + y2*y2 + z2*z2  #length of v2
        dot = (x1+x2 + y1+y2 + z1+z2)/(sqrt(L1)*sqrt(L2)) #dot.product
        acr = acos(dot)  #arccos
        acd = degrees(acr) #to degrees
        return acd
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getRotationAngles(self,source,destination):
        """Returns angles needed to rotate source to destination vector"""
        #due to multiple OGL rotations, the display is not always accurate, though the calculations are spot on
        srcx,srcy,srcz = source
        dstx,dsty,dstz = destination
        dx=float(dstx-srcx); dy=float(dsty-srcy); dz=float(dstz-srcz)
        yrot = atan2(dx, dz)
        xrot = atan2(abs(dy), sqrt((abs(dx) * abs(dx)) + (abs(dz) * abs(dz))))
        return degrees(xrot),degrees(-yrot),0

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setModelsSame(self,model1,model2):
        """Set values of model2 same as model1"""
        self.models[model2].setPosition(self.models[model1].getPosition())
        self.models[model2].setRotation(self.models[model1].getRotation())

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def pointTo(self,item,pos):
        """rotate item-vector to point to pos-vector"""
        ix,iy,iz = item
        px,py,pz = pos
        v1 = Vector3(ix,iy,iz)
        v2 = Vector3(px,py,pz)
        angles = self.getRotationAngles(item,pos)
        return angles

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def processInput(self):
        """Process user input"""
        #rotate camera if right mouse button is down, and mouse is moved
        #rotate third person camera
        if self.cameratype == 0:
            rotx=0; roty=0; rotz=0
            if self.mousebutton == self.rightmousebutton and self.mousedown and self.mouseMoveX:
                roty = -0.5*self.mouseMoveX;
            if self.mousebutton == self.rightmousebutton and self.mousedown and self.mouseMoveY:
                rotx = -0.5*self.mouseMoveY;
            self.rotateCamera((rotx,roty,rotz))
        #Move camera distance, activated by 2 mouse buttons, and mouse move up or down
        if self.twomousebuttons and self.mouseMoveY:
            self.camera.distance += 0.05*self.mouseMoveY

        #rotate first person camera
        if self.cameratype == 1:
            pass

        #if an object is selected, do something
        #if self.object_selected:
            #add code for selected object here
            #..then deselect the object
            #self.object_selected = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getInput(self):
        """Get user input"""
        self.mousemoveX=None; self.mouseMoveY = None
        self.mouseX, self.mouseY = pygame.mouse.get_pos()
        self.mouseMoveX, self.mouseMoveY = pygame.mouse.get_rel()
        self.events.update()
        
        if K_PERIOD in self.events.keyboard.hit: #period ">"
            self.testnumber += 1
            self.do_once = False
            self.delta = 0
        if K_COMMA in self.events.keyboard.hit: #comma "<"
            self.testnumber -= 1
            self.do_once = False
            self.delta = 0
            if self.testnumber < 1:
                self.testnumber = 1
        if K_DOWN in self.events.keyboard.hit: 
            self.currentkey = "down"
        if K_UP in self.events.keyboard.hit: 
            self.currentkey = "up"
        if K_LEFT in self.events.keyboard.hit: 
            self.currentkey = "left"
        if K_RIGHT in self.events.keyboard.hit: 
            self.currentkey = "right"
        if K_SPACE in self.events.keyboard.hit: 
            self.currentkey = "space"
        if self.events.quit or K_ESCAPE in self.events.keyboard.hit:
           quit()
           sys.exit(0)
           
        #if 1 mouse button is held down
        if len(self.events.mouse.held)==2:
            #if right mouse button is held down
            self.mousebutton = self.events.mouse.held[0]
            self.mousedown = True
        else:
            self.mousebutton = None
            self.mousedown = False
        #if 2 mouse buttons are held down
        if len(self.events.mouse.held)==4:
            self.twomousebuttons = True
        else:
            self.twomousebuttons = False

        #if 1 mouse button is pressed
        if len(self.events.mouse.hit)==2 and self.mouse_over_object:
            if self.events.mouse.hit[0] == 1: #if left mouse button
                self.object_selected = self.mouse_over_object
            else:
                self.object_selected = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def clearLabels(self):
        for n in self.labels:
            self.scene.remove_3d_blend(n)
            del n
        self.labels = []

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test1(self):
        """Simple in place rotation"""
        if self.do_once == False:
            self.do_once = True
            self.cameratype=0
            self.resetCamera()
            self.hideModels()
            self.models['earth'].show()
            self.light.pos = (10,0,0)
            self.models['earth'].rotation_speed = 0.3
            x,y,z = self.models['earth'].model.rotation
            z=0
            self.models['earth'].model.rotation = (x,y,z)
            self.models['earth'].model.pos = (0,0,0)
            self.camera.distance = 10
            self.clearLabels()
            label = self.makeLabel("Simple in-place Rotation\nPress '>' for next test\n\nKeep right mouse button in\nand move mouse to rotate\nKeep left and rifht mouse buttons in\nand move mouse up or down to zoom",
                                   40,(0,3.5,0))
        self.models['earth'].rotate()


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test2(self):
        """Simple angled in place rotation"""
        if self.do_once == False:
            self.do_once = True
            self.cameratype=0
            self.resetCamera()
            self.hideModels()
            self.models['earth'].show()
            self.light.pos = (10,0,0)
            self.models['earth'].rotation_speed = 0.3
            x,y,z = self.models['earth'].model.rotation
            z+= 25
            self.models['earth'].model.rotation = (x,y,z)
            self.models['earth'].model.pos = (0,0,0)
            self.camera.distance = 10
            self.clearLabels()
            self.makeLabel("Angled in-place Rotation\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nKeep left and rifht mouse buttons in\nand move mouse up or down to zoom",
                                   40,(0,3.5,0))
        self.models['earth'].rotate()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test3(self):
        """Simple circular orbit"""
        if self.do_once == False:
            self.do_once = True
            self.cameratype=0
            self.hideModels()
            self.models['earth'].show()
            self.models['sun'].show()
            self.resetCamera()
            self.rotateCamera((-20,0,0))
            self.light.pos = (0,0,0)
            self.light.ambient = (0.1,0.1,0.1,1)
            self.light.diffuse = (1,1,1,1)
            self.camera.distance = 15
            self.clearLabels()
            self.makeLabel("Circular Orbit\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nKeep left and rifht mouse buttons in\nand move mouse up or down to zoom",
                                   40,(0,3.5,-5))
        radius = 5
        self.delta += 0.01
        if self.delta > 360:
            self.delta = 0
        x = radius*cos(self.delta)
        y=0
        z = radius*sin(self.delta)
        self.light.direction = (x,y,z)
        self.models['earth'].model.pos = (x,y,z)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test4(self):
        """Simple circular orbit with rotating planet"""
        if self.do_once == False:
            self.do_once = True
            self.cameratype=0
            self.resetCamera()
            self.rotateCamera((-20,0,0))
            self.hideModels()
            self.models['earth'].show()
            self.models['sun'].show()
            self.light.pos = (0,0,0)
            self.light.ambient = (0.1,0.1,0.1,1)
            self.light.diffuse = (1,1,1,1)
            self.camera.distance = 15
            self.models['sun'].rotation_speed = 0.2
            self.models['earth'].rotation_speed = 4
            self.clearLabels()
            self.makeLabel("Circular Orbit with rotations\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nKeep left and rifht mouse buttons in\nand move mouse up or down to zoom",
                                   40,(0,3.5,-5))
        radius = 5
        self.delta += 0.01
        x = radius*cos(self.delta)
        y=0
        z = radius*sin(self.delta)
        self.models['earth'].model.pos = (x,y,z)
        self.test1()
        self.models['sun'].rotate()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test5(self):
        """Perform angular calculations test"""
        if self.do_once == False:
            self.do_once = True
            self.hideModels()
            self.models['pointer'].show()
            self.models['earth'].show()
            self.models['pointer'].scale((0.1, 0.1, 0.1))
            self.cameratype=0
            self.resetCamera()
            self.rotateCamera((-20,0,0))
            self.light.pos = (0,0,0)
            self.light.ambient = (0.1,0.1,0.1,1)
            self.light.diffuse = (1,1,1,1)
            self.camera.distance = 15
            self.object_selected = None
            self.clearLabels()
            self.makeLabel("Angular calculations test\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nKeep left and rifht mouse buttons in\nand move mouse up or down to zoom",
                                   40,(0,3.5,-5))            
        radius = 5
        self.delta += 0.003
        x = radius*cos(self.delta)
        y=0
        z = radius*sin(self.delta)
        self.models['earth'].model.pos = (x,y,z)
        self.test1()
        rotations = self.pointTo((0,0,0),self.models['earth'].getPosition())
        self.models['pointer'].setRotation(rotations)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def pointToPlanet(self):
        if self.object_selected:
            for n in self.models:
                if self.models[n].model == self.object_selected:
                    rotations = self.pointTo(self.models['pointer'].getPosition(),self.models[n].getPosition())
                    self.models['pointer'].setRotation(rotations)        
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test6(self,point):
        """Enhanced angular calculations with solar system"""
        #solar system driven by self-orbit around the sun
        if self.do_once == False:
            self.deleteGrid()
            self.do_once = True
            self.cameratype=0
            self.resetCamera()
            self.placeCamera((0,0,0),(0,0,0),40)
            self.hideModels()
            #setup sun
            self.models['sun'].show()
            self.models['sun'].setPosition((0.0001,0.0001,0.0001))
            self.models['sun'].scale(0.2)
            self.models['sun'].rotation_speed = 0.2
            #setup earth
            self.models['earth'].show()
            self.models['earth'].setPosition((5,0.0001,0.0001))
            self.models['earth'].scale(0.08)
            self.models['earth'].rotation_speed = 1
            self.models['earth'].orbit_angle = (0,-0.1,0)
            #setup moon
            self.models['moon'].show()
            self.models['moon'].setPosition((6.5,0,0))
            self.models['moon'].scale(0.05)
            self.models['moon'].rotation_speed = 0.4
            self.models['moon'].orbit_angle = (0,-2,0)
            #setup mars
            self.models['mars'].show()
            self.models['mars'].setPosition((9,2,0))
            self.models['mars'].scale(0.1)            
            self.models['mars'].rotation_speed = 0.3
            self.models['mars'].orbit_angle = (0,-0.3,0)
            #setup jupiter
            self.models['jupiter'].show()
            self.models['jupiter'].setPosition((15,5,0))
            self.models['jupiter'].scale(0.2)
            self.models['jupiter'].rotation_speed = 0.5
            self.models['jupiter'].orbit_angle = (0,-0.08,0)
            #setup pointer
            if point==1:
                self.models['pointer'].show()
                self.models['pointer'].setPosition((0,3,0))
                self.models['pointer'].scale(0.15)
                self.clearLabels()
                self.makeLabel("Angular calculations test with Solar system\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nClick left mouse button on any planet\nTo activate pointer\nTry to catch the moon...",
                                   40,(-1,1.5,-35))            
            
        self.delta += 0.1
        self.models['sun'].rotate()
        self.models['earth'].rotate()
        self.models['moon'].rotate()
        self.models['mars'].rotate()
        self.models['jupiter'].rotate()
        self.orbit_planet('earth','sun')
        self.orbit_planet('moon','earth') 
        self.orbit_planet('mars','sun')
        self.orbit_planet('jupiter','sun')
        if point:
            self.pointToPlanet()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def lookAtPlanet(self):
        if self.object_selected:
            for n in self.models:
                if self.models[n].model == self.object_selected:
                    focus = self.models[n].getPosition()
                    self.focusCamera(focus)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test7(self):
        """Focus camera on selected planet"""
        if self.do_once == False:
            self.cameratype=0
            self.deleteGrid()
            self.resetCamera()            
            self.placeCamera((0,0,0),(0,0,0),40)
            self.models['pointer'].hide()
            self.clearLabels()
            self.makeLabel("Focus camera on selected planet - test\nPress '>' for next test\nPress '<' for prev test\nKeep right mouse button in\nand move mouse to rotate\nClick left mouse button on planet or moon, to focus",
                                   40,(-1,1.5,-35))            
        self.test6(0)
        self.lookAtPlanet()
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getSelectedModel(self):
        if self.object_selected:
            for n in self.models:
                if self.models[n].model == self.object_selected:
                    return n
        return None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stopWhenClose(self,source,destination,distance):
        """Stop 'source' model moving when closer than 'distance' to 'destination' model """
        if destination == None: return
        d = self.getDistance(self.models[source].getPosition(),self.models[destination].getPosition())
        if d < distance:
            self.object_selected = None  #set no destination to move towards

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test8(self):
        """Smooth homing flight"""
        if self.do_once == False:
            self.do_once = True
            self.resetCamera()            
            self.cameratype=0
            self.hideModels()
            self.placeCamera((0,0,0),(-90,0,0),70) #look straight down
            self.createGrid((-40,-40,-40),(40,40,40),2.5)
            #setup waypoint markers
            for n in self.pointlist:
                self.deleteModel(n)
                self.copyModel("sun",n)
            #setup spaceship 'eagle'
            self.models['eagle'].show()
            self.models['eagle'].setPosition((0,0,0))
            self.models['eagle'].scale(0.2)
            self.models['eagle'].setRotation((0,0,0))
            #place random waypoints
            self.models["sun"].hide()
            for n in self.pointlist:
                x = random.randint(-35,35)
                y = random.randint(-6,6)
                z = random.randint(-24,24)
                self.models[n].setPosition((x,y,z))
                self.models[n].scale(0.05)
            #setup spaceship values
            self.models['eagle'].rotation_speed = 2
            self.models['eagle'].velocity = 0.2
            self.clearLabels()
            self.makeLabel("Smooth homing flight\nPress '>' for next test\nPress '<' for prev test\nClick on a waypoint to set destination\nPress SpaceBar to change waypoints\nCan rotate and zoom camera",
                                   40,(-1.6,65.2,1.5))            
            
        if self.currentkey == "space":
            for n in self.pointlist:
                x = random.randint(-35,35)
                y = random.randint(-6,6)
                z = random.randint(-24,24)
                self.currentkey = ""
                self.models[n].setPosition((x,y,z))

        dest = self.getSelectedModel()
        self.stopWhenClose('eagle',dest,0.8)
        if dest:
            self.models['eagle'].moveTowards(self.models[dest].getPosition())
            self.models['eagle'].move()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def bounceAtEdge(self,model):
        px,py,pz = self.models[model].getPosition()
        rx,ry,rz = self.models[model].getRotation()
        radius = 1
        bounce = 0
        dx,dy,dz = self.models[model].getDirectionVector()
        if px+radius <= self.leftedge:
            bounce = abs(360-ry)
            self.models[model].setRotation((rx,bounce,rz))
        if px+radius >= self.rightedge:
            bounce = 360-ry
            self.models[model].setRotation((rx,bounce,rz))
        if pz+radius >= self.topedge:
            if ry <180:
                bounce = 180-ry
            else:
                bounce = 540-ry
            self.models[model].setRotation((rx,bounce,rz))
        if pz+radius <= self.bottomedge:
            if ry < 180:                
                bounce = 180-ry
            else:
                bounce = 540-ry
            self.models[model].setRotation((rx,bounce,rz))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def ballBounce(self,ball, ball2):
        """Generic 2d ball bounce function"""
        dx = ball.x-ball2.x
        dy = ball.y-ball2.y
        collisionision_angle = atan2(dy, dx)
        magnitude_1 = sqrt(ball.xspeed*ball.xspeed+ball.yspeed*ball.yspeed)
        magnitude_2 = sqrt(ball2.xspeed*ball2.xspeed+ball2.yspeed*ball2.yspeed)
        direction_1 = atan2(ball.yspeed, ball.xspeed)
        direction_2 = atan2(ball2.yspeed, ball2.xspeed)
        new_xspeed_1 = magnitude_1*cos(direction_1-collisionision_angle)
        new_yspeed_1 = magnitude_1*sin(direction_1-collisionision_angle)
        new_xspeed_2 = magnitude_2*cos(direction_2-collisionision_angle)
        new_yspeed_2 = magnitude_2*sin(direction_2-collisionision_angle)
        final_xspeed_1 = ((ball.mass-ball2.mass)*new_xspeed_1+(ball2.mass+ball2.mass)*new_xspeed_2)/(ball.mass+ball2.mass)
        final_xspeed_2 = ((ball.mass+ball.mass)*new_xspeed_1+(ball2.mass-ball.mass)*new_xspeed_2)/(ball.mass+ball2.mass)
        final_yspeed_1 = new_yspeed_1
        final_yspeed_2 = new_yspeed_2
        ball.xspeed = cos(collisionision_angle)*final_xspeed_1+cos(collisionision_angle+pi/2)*final_yspeed_1
        ball.yspeed = sin(collisionision_angle)*final_xspeed_1+sin(collisionision_angle+pi/2)*final_yspeed_1
        ball2.xspeed = cos(collisionision_angle)*final_xspeed_2+cos(collisionision_angle+pi/2)*final_yspeed_2
        ball2.yspeed = sin(collisionision_angle)*final_xspeed_2+sin(collisionision_angle+pi/2)*final_yspeed_2
        return ball.xspeed, ball.yspeed, ball2.xspeed, ball2.yspeed

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def ballCollisions(self,model):
        diameter = 2.5
        ball1 = self.models[model]
        rx1,ry1,rz1 = ball1.getRotation()
        for n in self.tempmodels:
            if n != model:
                ball2 = self.models[n]
                rx2,ry2,rz2 = ball2.getRotation()
                d = self.getDistance(ball1.getPosition(),ball2.getPosition())
                if d <= (diameter):
                    #Note: y an z are transposed for y-plane calculations
                    ball1.x, ball1.z, ball1.y = ball1.getPosition()
                    ball1.xspeed, ball1.zspeed, ball1.yspeed = ball1.getDirectionVector()
                    ball2.x, ball2.z, ball2.y = ball2.getPosition()
                    ball2.xspeed, ball2.zspeed, ball2.yspeed = ball2.getDirectionVector()
                    x1,z1,x2,z2 = self.ballBounce(ball1,ball2)
                    y1 = y2 = 0                    
                    angles1 = ball1.getRotationAngles(ball1.getPosition(),(x2,y2,z2))
                    angles2 = ball2.getRotationAngles(ball2.getPosition(),(x1,-y1,z1))
                    ax1,ay1,az1 = angles1
                    ball1.setRotation((rx1,ry1+180,rz1))
                    ball2.setRotation((rx2,ry2+180,rz2))
                    ball1.move()
                    #work around 'sticky ball' bug
                    ball1.move()
                    ball2.move()
                    ball1.setRotation((ax1,ay1+190,az1))
                    ball2.setRotation(angles1)
                            
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def test9(self):
        """simple bouncing balls"""
        if self.do_once == False:
            self.do_once = True
            self.resetCamera()            
            self.deleteGrid()
            self.cameratype=0
            self.hideModels()
            self.createGrid((-20,-20,-20),(20,20,20),39.9)
            self.placeCamera((0,0,0),(-90,0,0),70)
            self.clearLabels()
            #setup bouncing suns
            self.tempmodels = []
            for n in range(0,6):
                newmodel = "ball"+str(n)
                self.deleteModel(newmodel)
                self.copyModel("sun",newmodel)
                x = random.randint(-16,16)
                z = random.randint(-16,16)
                self.models[newmodel].setPosition((x,0,z))
                self.models[newmodel].scale(0.1)
                rot = random.randint(0,360)
                self.models[newmodel].setRotation((0,rot,0)) #random direction
                vel = random.randint(3,4)*0.05
                self.models[newmodel].velocity = vel #random velocity
                self.tempmodels.append(newmodel)
            #setup boundry edged
            self.leftedge = -18
            self.rightedge = 19
            self.bottomedge = -17.5
            self.topedge = 20
            self.clearLabels()
            self.makeLabel("simple bouncing balls\nPress '>' for next test\nPress '<' for prev test\nCan rotate and move camera\nPress SpaceBar to reset balls",
                                   40,(-1.6,65.2,1.5))            

        if self.currentkey == "space":
            for n in self.tempmodels:
                x = random.randint(-16,16)
                z = random.randint(-16,16)
                self.models[n].setPosition((x,0,z))
                rot = random.randint(0,360)
                self.models[n].setRotation((0,rot,0)) #random direction
                vel = random.randint(3,4)*0.05
                self.models[n].velocity = vel #random velocity
                self.currentkey = ""

        for n in self.tempmodels:
            self.bounceAtEdge(n)
            self.ballCollisions(n)
            self.models[n].move()


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def draw(self):
        """main draw method"""
        if self.testnumber == 1:
            self.test1()
        if self.testnumber == 2:
            self.test2()
        if self.testnumber == 3:
            self.test3()
        if self.testnumber == 4:
            self.test4()
        if self.testnumber == 5:
            self.test5()
        if self.testnumber == 6:
            self.test6(1)
        if self.testnumber == 7:
            self.test7()
        if self.testnumber == 8:
            self.test8()
        if self.testnumber == 9:
            self.test9()
            
            
            

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        """game main loop"""
        while 1:
            #limit frames per second
            self.clock.tick(60)
            #get user input
            self.getInput()
            #process user input
            self.processInput()
            #clear screen for new drawing
            view.clear_screen()
            #draw objects from here
            self.draw()
            #render the scene... Also retrieve the picked object
            if self.cameratype == 0:
                self.mouse_over_object = self.scene.render(self.camera)
            else:
                self.mouse_over_object = self.scene.render(self.camera2)                
            #flip the display buffer
            view.refresh_screen()




########################################main
if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except:
        pass
    game = World()
    game.run()
