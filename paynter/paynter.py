#External modules
import numpy as N
import PIL.Image
import PIL.ImageOps
import PIL.ImageFont
import PIL.ImageDraw 


#PaYnter Modules
from .blendModes import *
from .brush import *
from .utils import *
from .image import *
from .layer import *
import paynter.config as config



'''
TODO:
-add asserts to main functions
-uniform the way in main.py we handle paynter and image
-add color class
'''

######################################################################
# Paynter class
######################################################################
#The paynter class is the object that draw stuff on a layer using a brush and a color
class Paynter:
	brush = 0
	layer = 0
	color = [0, 0, 0, 1]
	secondColor = [1, 1, 1, 1]
	image = 0
	mirrorMode = '' # ''/'h'/'v'/'hv'

	#Init the paynter
	def __init__(self):
		#Setup some stuff
		config.CANVAS_SIZE = int(config.REAL_CANVAS_SIZE/config.DOWNSAMPLING)
		self.image = Image()



	######################################################################
	# Level 0 Functions, needs downsampling
	######################################################################
	#Draw a line between two points
	def drawLine(self, x1, y1, x2, y2):
		#Downsample the coordinates
		x1 = int(x1/config.DOWNSAMPLING)
		x2 = int(x2/config.DOWNSAMPLING)
		y1 = int(y1/config.DOWNSAMPLING)
		y2 = int(y2/config.DOWNSAMPLING)
		print('drawing line from: '+str((x1,y1))+' to: '+str((x2,y2)))


		#Calculate the direction and the length of the step
		direction = math.degrees(math.atan2(y2 - y1, x2 - x1))
		length = self.brush.spacing

		#Prepare the loop
		x, y = x1, y1
		currentDist = math.sqrt((x2 - x)**2 + (y2 - y)**2)
		previousDist = currentDist+1

		#Do all the steps until I passed the target point
		while(previousDist>currentDist):
			#Make the dab on this point
			self.brush.makeDab(self.image.getActiveLayer(), int(x), int(y), self.color, self.secondColor, mirror=self.mirrorMode)

			#Mode the point for the next step and update the distances
			x += length*dcos(direction)
			y += length*dsin(direction)
			previousDist = currentDist
			currentDist = math.sqrt((x2 - x)**2 + (y2 - y)**2)

	#Draw a single dab
	def drawPoint(self, x, y):
		x = int(x/config.DOWNSAMPLING)
		y = int(y/config.DOWNSAMPLING)
		self.brush.makeDab(self.image.getActiveLayer(), int(x), int(y), self.color, self.secondColor, mirror=self.mirrorMode)

	######################################################################
	# Level 1 Functions, calls Level 0 functions, no downsampling
	######################################################################
	#Draw a path from a series of points
	def drawPath(self, pointList):
		self.drawLine(pointList[0][0], pointList[0][1], pointList[1][0], pointList[1][1])
		i = 1
		while i<len(pointList)-1:
			self.drawLine(pointList[i][0], pointList[i][1], pointList[i+1][0], pointList[i+1][1])
			i+=1

	#Draw a path from a series of points
	def drawClosedPath(self, pointList):
		self.drawLine(pointList[0][0], pointList[0][1], pointList[1][0], pointList[1][1])
		i = 1
		while i<len(pointList)-1:
			self.drawLine(pointList[i][0], pointList[i][1], pointList[i+1][0], pointList[i+1][1])
			i+=1
		self.drawLine(pointList[-1][0], pointList[-1][1], pointList[0][0], pointList[0][1])
		
	#Draw a rectangle
	def drawRect(self, x1, y1, x2, y2, angle=0):
		vertices = [[x1,y1],[x2,y1],[x2,y2],[x1,y2],]
		rotatedVertices = rotateMatrix(vertices, (x1+x2)*0.5, (y1+y2)*0.5, angle)
		self.drawClosedPath(rotatedVertices)

	#Fill the current layer with a color
	def fillLayerWithColor(self, color):
		layer = self.image.getActiveLayer().data
		layer[:,:,0] = color[0]
		layer[:,:,1] = color[1]
		layer[:,:,2] = color[2]
		layer[:,:,3] = color[3]

	#Add border to image
	def addBorder(self, width, color=0):
		width = int(width/config.DOWNSAMPLING)
		if color==0:
			color = self.color
		layer = self.image.getActiveLayer().data
		layer[0:width,:,0] = color[0]
		layer[0:width,:,1] = color[1]
		layer[0:width,:,2] = color[2]
		layer[0:width,:,3] = color[3]*255

		layer[:,0:width,0] = color[0]
		layer[:,0:width,1] = color[1]
		layer[:,0:width,2] = color[2]
		layer[:,0:width,3] = color[3]*255

		layer[layer.shape[0]-width:layer.shape[0],:,0] = color[0]
		layer[layer.shape[0]-width:layer.shape[0],:,1] = color[1]
		layer[layer.shape[0]-width:layer.shape[0],:,2] = color[2]
		layer[layer.shape[0]-width:layer.shape[0],:,3] = color[3]*255

		layer[:,layer.shape[1]-width:layer.shape[1],0] = color[0]
		layer[:,layer.shape[1]-width:layer.shape[1],1] = color[1]
		layer[:,layer.shape[1]-width:layer.shape[1],2] = color[2]
		layer[:,layer.shape[1]-width:layer.shape[1],3] = color[3]*255




	######################################################################
	# Setters and getters
	######################################################################
	#Setter for color, takes 0-255 RGBA
	def setColor(self, r=0, g=0, b=0, a=255):
		#Separated paramters
		if isinstance(r, int):
			self.color = N.divide([r, g, b, a], 255)
		#RGBA list 
		else:
			self.color = N.divide([r[0], r[1], r[2], r[3]], 255)

	#Swap between first and second color
	def swapColors(self):
		temp = N.copy(self.color)
		self.color = self.secondColor
		self.secondColor = temp

	#Setter for brush reference
	def setBrush(self, b):
		self.brush = b

	#Setter for the mirror mode
	def setMirrorMode(self, mirror):
		assert (mirror=='' or mirror=='h' or mirror=='v' or mirror=='hv'), 'setMirrorMode: wrong mirror mode, got '+str(mirror)+' expected one of ["","h","v","hv"]'
		self.mirrorMode = mirror
		
	#Render the final image
	def renderImage(self):
		#Make sure the alpha on the base layer is ok
		#self.image.layers[0].data[:,:,3] = 255

		#Merge all the layers to apply blending modes
		resultLayer = self.image.mergeAllLayers()
		resultLayerData = resultLayer.data

		#Show the results
		img = PIL.Image.fromarray(resultLayerData, 'RGBA')
		img.show()


















