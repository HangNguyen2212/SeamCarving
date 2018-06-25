from scipy.ndimage.filters import generic_gradient_magnitude, sobel
import numpy as np
import test
from PIL import Image
# pylint: disable=E1101
# pylint: disable=E1121


def displayImage(screen, px, topleft, prior):
    # ensure that the rect always has positive width, height
    x, y = topleft
    width =  pygame.mouse.get_pos()[0] - topleft[0]
    height = pygame.mouse.get_pos()[1] - topleft[1]
    if width < 0:
        x += width
        width = abs(width)
    if height < 0:
        y += height
        height = abs(height)
    # eliminate redundant drawing cycles (when mouse isn't moving)
    current = x, y, width, height
    if not (width and height):
        return current
    if current == prior:
        return current

    # draw transparent box and blit it onto canvas
    screen.blit(px, px.get_rect())
    im = pygame.Surface((width, height))
    im.fill((128, 128, 128))
    pygame.draw.rect(im, (32, 32, 32), im.get_rect(), 1)
    im.set_alpha(128)
    screen.blit(im, (x, y))
    pygame.display.flip()

    # return current box extents
    return (x, y, width, height)
def setup(path):
    px = pygame.image.load(path)
    screen = pygame.display.set_mode( px.get_rect()[2:] )
    screen.blit(px, px.get_rect())
    pygame.display.flip()
    return screen, px

def mainLoop(screen, px):
    topleft = bottomright = prior = None
    n=0
    while n!=1:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                if not topleft:
                    topleft = event.pos
                else:
                    bottomright = event.pos
                    n=1
        if topleft:
            prior = displayImage(screen, px, topleft, prior)
    return topleft + bottomright

def RGBtoGrayScale (image):
	return image.convert("F")
	
def Sobel ( image ):
	sobel_arr = generic_gradient_magnitude(image, derivative=sobel)
	gradient = Image.new("I", image.size)
	gradient.putdata(list(sobel_arr.flat))
	return gradient
	
def Transpose(image):
	image_width, image_height = image.size
	image_arr = np.reshape(image.getdata( ),(image_height, image_width))
	image_arr = np.transpose(image_arr)
	image = Image.new(image.mode,(image_height, image_width))	
	image.putdata( list( image_arr.flat))
	return image

def Draw_Seam (image, path):
	pix = image.load()
	path = flatten(path)
	if image.mode == "RGB": 
		for pixel in path:
			for each in pixel:
				pix[each] = (255,255,255)
	else:
		for pixel in path:
			pix[pixel] = 255
	return image

def average_vectors (u, v):
	w = list(u)
	for i in range(len(u)):
		w[i] = (u[i] + v[i]) / 2
	return tuple(w)

def flatten(lst):
	for i in lst:
	    if type(i) == list:
	        for i in flatten(i):
				yield i
		else:
			yield i
			
def find_horizontal_seam ( image, left, upper, right, lower, choice):
	image_width, image_height = image.size 
	dynamicBoard = np.zeros( image.size ) 
	image_arr = np.reshape( image.getdata( ), (image_height, image_width) )
	image_arr = np.transpose(image_arr)
	if choice == 2:
		for row in range(left,right):
			for column in range(upper, lower):
				image_arr[row,column] = -10000
				print left, upper, right, lower


	for column in range(image_height):
		dynamicBoard[0,column] = image_arr[0, column]
	

	for row in range(1, image_width):
		for column in range(image_height):
			if column == 0:
				min_val = min( dynamicBoard[row-1,column], dynamicBoard[row-1,column+1] )
			elif column < image_height - 2:
				min_val = min( dynamicBoard[row-1,column], dynamicBoard[row-1,column+1] )
				min_val = min( min_val, dynamicBoard[row-1,column-1] )
			else:
				min_val = min( dynamicBoard[row-1,column], dynamicBoard[row-1,column-1] )
			dynamicBoard[row,column] = image_arr[row,column] + min_val

	min_val = 1e1000
	path = [ ]

	for column in range(image_height):
		if dynamicBoard[image_width-1,column] < min_val:
			min_val = dynamicBoard[image_width-1,column]
			min_val_pos = column

	pos =(image_width-1,min_val_pos)
	path.append(pos) 
	while pos[0] != 0:
		val = dynamicBoard[pos] - image_arr[pos]
		row,column = pos
		if column == 0:
			if val == dynamicBoard[row-1,column+1]:
				pos = (row-1,column+1) 
			else:
				pos = (row-1,column)
		elif column < image_height - 2:
			if val == dynamicBoard[row-1,column+1]:
				pos = (row-1,column+1) 	
			elif val == dynamicBoard[row-1,column]:
				pos = (row-1,column)
			else:
				pos = (row-1,column-1)
		else:
			if val == dynamicBoard[row-1,column]:
				pos = (row-1,column)
			else:
				pos = (row-1,column-1) 

		path.append(pos)
 
	return path
	
def find_vertical_seam ( image ,left, upper, right, lower,choice): 
	img = Transpose(image)

	u = find_horizontal_seam(img,upper, left, lower, right,choice)
	for i in range(len(u)):
		temp = list(u[i])
		temp.reverse()
		u[i] = tuple(temp)
	return u
	
def delete_horizontal_seam (image, path):

	image_width, image_height = image.size
	i = Image.new(image.mode, (image_width, image_height-1))
	input  = image.load()
	output = i.load()
	seam_path = path
	seam_pos = set()
	for column in range(image_height):
		for row in range(image_width):
			if (row,column) not in seam_path and row not in seam_pos:
				output[row,column] = input[row,column]
			elif (row,column) in seam_path:
				seam_pos.add(row)
			else:
				output[row,column-1] = input[row,column]
	return i
			
def delete_vertical_seam (image, path):
	image_width, image_height = image.size
	i = Image.new(image.mode, (image_width-1, image_height))
	input  = image.load()
	output = i.load()
	seam_path = set(path)
	seam_pos = set()
	for row in range(image_width):
		for column in range(image_height):
			if (row,column) not in seam_path and column not in seam_pos:
				output[row,column] = input[row,column]
			elif (row,column) in seam_path:
				seam_pos.add(column)
			else:
				output[row-1,column] = input[row,column]
	return i
	
def add_vertical_seam(image, path):
	image_width, image_height = image.size
	i = Image.new(image.mode, (image_width + 1, image_height) )
	input  = image.load()
	output = i.load()
	seam_path = set(path)
	seam_pos = set()
	for row in range(image_width):
		for column in range(image_height):
			if (row,column) not in seam_path and column not in seam_pos:
				output[row,column] = input[row,column]
			elif (row,column) in seam_path and column not in seam_pos:
				output[row,column] = input[row,column]
				seam_pos.add( column )
				if row < image_width -2:
					output[row+1,column] = average_vectors(input[row,column], input[row+1,column])
				else:
					output[row+1,column] = average_vectors(input[row,column], input[row-1,column])
			else:
				output[row+1,column] = input[row,column]		
	return i
	
def add_horizontal_seam(image, path):
	image_width, image_height = image.size
	i = Image.new(image.mode, (image_width, image_height+1) )
	input  = image.load()
	output = i.load()
	seam_path = set(path)
	seam_pos = set()
	for column in range(image_height):
		for row in range(image_width):
			if (row,column) not in seam_path and row not in seam_pos:
				output[row,column] = input[row,column]
			elif (row,column) in seam_path and row not in seam_pos:
				output[row,column] = input[row,column]
				seam_pos.add( row )
				if column < image_height -2:
					output[row,column+1] = average_vectors(input[row,column], input[row,column+1])
				else:
					output[row,column+1] = average_vectors(input[row,column], input[row,column-1])
			else:
				output[row,column+1] = input[row,column]
	return i		
					
def SeamCarving(input_image, resolution, output, choice):

	if choice == 2:
		global left
		global upper  
		global right
		global lower
	else:
		left=upper=right=lower=0
	input = Image.open(input_image)
	im_width, im_height = input.size
	marked = [ ]
	while im_width > resolution[0]:
		u = find_vertical_seam(Sobel(RGBtoGrayScale(input)),left, upper, right, lower,choice)
		if choice == 2:
			right = right - 1
		marked.append(u)
		input = delete_vertical_seam(input, u)
		im_width = input.size[0]

	while im_width < resolution[0]:
		u = find_vertical_seam(Sobel(RGBtoGrayScale(input)),left, upper, right, lower, choice)
		input = add_vertical_seam(input, u)
		im_width = input.size[0]

	while im_height > resolution[1]:
		v = find_horizontal_seam(Sobel(RGBtoGrayScale(input)),left, upper, right, lower,choice)
		if choice == 2:
			upper = upper - 1
		marked.append(v)
		input = delete_horizontal_seam(input,v)
		im_height = input.size[1]

	while im_height < resolution[1]:
		v = find_horizontal_seam(Sobel(RGBtoGrayScale(input)),left, upper, right, lower, choice)
		input = add_horizontal_seam(input,v)
		im_height = input.size[1]
		
	input.save(output, "jpeg")
	if(marked != []):
		Draw_Seam(Image.open(input_image), marked).show( )
		

# print left,right,upper,lower
# print image.size[0]-(right-left+1),image.size[1]

# SeamCarving(input_loc,(image.size[0]-(right-left),image.size[1]),"nbeach.jpeg")
choice = 0
while choice!=-1:
	print "What do you want to do?"
	print "--1-- Resize Image"
	print "--2-- Crop Object/People"

	choice = input()
	print "**********************************************************"
	print "Name of Image: "
	inputimage = str(raw_input("Input Name Image:"))
	if choice==1:
		width = int(raw_input("Input Width For Your Ouput Image:"))
		height = int(raw_input("Input Height For Your Ouput Image:"))
		SeamCarving(inputimage,(width,height),"choice.jpg",choice)
	elif choice==2:
		import pygame, sys
		image = Image.open(inputimage)

		pygame.init()
		screen, px = setup(inputimage)
		left, upper, right, lower = mainLoop(screen, px)
		if right < left:
			left, right = right, left
		if lower < upper:
			lower, upper = upper, lower
		im = Image.open(inputimage)
		im = im.crop(( left, upper, right, lower))
		pygame.display.quit()
		SeamCarving(inputimage,(image.size[0]-(right-left),image.size[1]),"choice2.jpeg",choice)
		pygame.quit()
	else:
		choice = 0
	
	