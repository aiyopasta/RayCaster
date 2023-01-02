# By Aditya Abhyankar, September 2022
# When this program runs, the left side of the window shows the actual
# 2D ray-casting algorithm at play. The right side shows the resulting 3D rendering.

# Using a virtual environment with numpy install through pycharm as for some reason,
# numpy installed using pip3 does not work, and if you use numpy installed from pycharm
# on the globally installed python, numpy no longer works in Jupyter Notebook.

from tkinter import *
import numpy as np
import copy
import time

# Window size. Note: 1920/2 = 960 will be the width of each half of the display (2D | 3D)
window_w = int(1700)
window_h = int(1000)

# Tkinter Setup
root = Tk()
root.title("Ray caster")
root.attributes("-topmost", True)
root.geometry(str(window_w) + "x" + str(window_h))  # window size hardcoded

w = Canvas(root, width=window_w, height=window_h)

# Basic parameters
cellsize = 60
cubesize = window_h
ratio = cubesize / cellsize  # 3D to 2D (i.e. multiplication: 2D -> 3D)
rows, cols = int(np.floor(window_h / cellsize)), int(np.floor((window_w / 2) / cellsize))

# Player / camera variables
pos = 500, 600 #np.array([window_w/4, window_h/2])
dir = np.array([-1., -1.]); dir /= np.linalg.norm(dir)
focus = 35  # You can lower this more, but then make max cube height smaller too!
tangent = np.array([-dir[1], dir[0]])
screen = (window_w/2) / ratio
radius = 15
pointer = 25


def closer(p1, p2, pos):
    if np.linalg.norm(p1 - pos) < np.linalg.norm(p2 - pos):
        return p1

    return p2


class FilledSquare:
    def __init__(self, row, col, size, color='blue'):
        self.row, self.col = row, col
        self.size = size
        self.color = color

    def __str__(self):
        return str(self.row) + ', ' + str(self.col)

    def bbox(self):
        minX = self.col * self.size
        minY = self.row * self.size
        return minX, minY, minX+self.size, minY+self.size

    def intersects(self, origin, raydir):
        x, y = origin[0], origin[1]
        minX, minY, maxX, maxY = self.bbox()
        rise, run = raydir[1], raydir[0]

        point = np.array([1e16, 1e16])  # arbitrarily far value
        if rise == 0:
            if run == 1 and x < minX and minY <= y <= maxY:
                point[0], point[1] = minX, y

            elif run == -1 and maxX < x and minY <= y <= maxY:
                point[0], point[1] = maxX, y

        elif run == 0:
            if rise == 1 and y < minY and minX <= x <= maxX:
                point[0], point[1] = x, minY

            elif rise == -1 and maxY < y and minX <= x <= maxX:
                point[0], point[1] = x, maxY

        else:
            m = rise / run
            b = y - (m * x)

            xtemp = (minY - b)/m
            if minX <= xtemp <= maxX:
                temppoint = np.array([xtemp, minY])
                if np.dot(raydir, temppoint-pos) > 0:
                    point = temppoint

            xtemp = (maxY - b)/m
            if minX <= xtemp <= maxX:
                temppoint = closer(np.array([xtemp, maxY]), point, pos)
                if np.dot(raydir, temppoint-pos) > 0:
                    point = temppoint

            ytemp = (m * minX) + b
            if minY <= ytemp <= maxY:
                temppoint = closer(np.array([minX, ytemp]), point, pos)
                if np.dot(raydir, temppoint-pos) > 0:
                    point = temppoint

            ytemp = (m * maxX) + b
            if minY <= ytemp <= maxY:
                temppoint = closer(np.array([maxX, ytemp]), point, pos)
                if np.dot(raydir, temppoint-pos) > 0:
                    point = temppoint

        return point


# Grid storage (list of coords (row, col) corresponding to filled-in squares)
coords = [[3, 3], [4, 3], [5, 3], [6, 3], [4, 6], [8, 5], [2, 7], [7, 7]]
colors = ['orange', 'green', 'cyan', 'yellow', 'blue']
squares = [FilledSquare(*coords[i], cellsize, color=colors[np.random.randint(len(colors))]) for i in range(len(coords))]


# Main runner
def runstep():
    global pos, dir, tangent

    w.configure(background='black')
    w.delete('all')
    # DRAW 2D DISPLAY ——————————————————————————————————————————————————————————————————————
    # Draw filled in squares
    for square in squares:
        x, y = square.col*cellsize, square.row*cellsize
        w.create_rectangle(x, y, x+cellsize, y+cellsize, fill=square.color)

    # Draw grid
    for r in range(rows+1):
        w.create_line(0, r*cellsize, cols*cellsize, r*cellsize, fill='gray')
    for c in range(cols+1):
        w.create_line(c*cellsize, 0, c*cellsize, rows*cellsize, fill='gray')

    w.create_line(window_w/2, window_h/2, window_w, window_h/2, fill='red')
    # ———————————————————————————————————————————————————————————————————————————————————————————————
    # MAIN ALGORITHM
    n_pixels = int(window_w/2)
    spacing = screen / (n_pixels-1)
    for i in range(n_pixels):
        # 1. Find intersection point, could be infinity
        raydir = (dir * focus) - (screen*tangent/2) + (i*spacing*tangent)

        point = np.array([1e16, 1e16])
        epicsquare = None
        for square in squares:
            tempPoint = copy.deepcopy(point)
            point = closer(square.intersects(pos, raydir), point, pos)
            if not np.array_equal(tempPoint, point):
                epicsquare = square


        if np.linalg.norm(point) < window_w:
            # w.create_oval(point[0]-10, point[1]-10, point[0]+10, point[1]+10, fill='red')
            w.create_line(*pos, *point, fill='red')
        else:
            w.create_line(*pos, *(pos+(raydir*window_w)), fill='red')


        # 2. Draw the corresponding column, if any.
        if np.linalg.norm(point) < window_w:
            perpdist = (np.linalg.norm(np.dot(point - pos, dir)) - focus) * ratio
            height = min((500*cubesize) / perpdist, cubesize)
            w.create_line((window_w/2) + i, (-height/2) + (window_h/2), (window_w/2) + i, (height/2) + (window_h/2), fill=epicsquare.color)

        # ———————————————————————————————————————————————————————————————————————————————————————————————
        # Draw player
        w.create_oval(pos[0] - radius, pos[1] - radius, pos[0] + radius, pos[1] + radius, fill='green')
        w.create_line(*pos, *(pos + (dir * pointer)), fill='white')
        w.create_line(*(pos + (dir * focus) + (screen * tangent / 2)), *(pos + (dir * focus) - (screen * tangent / 2)), fill='cyan', width='4')

    w.update()


def rotate(angle):
    global dir, tangent
    dir = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]).dot(dir)
    tangent = np.array([-dir[1], dir[0]])


# Key bind
def key_pressed(event):
    global pos
    dtheta = np.pi / 100
    dpos = 5.
    if event.char == 'p':
        rotate(dtheta)

    if event.char == 'o':
        rotate(-dtheta)

    if event.char == 'w':
        pos += dpos * dir

    if event.char == 's':
        pos -= dpos * dir

    if event.char == 'a':
        pos -= dpos * tangent

    if event.char == 'd':
        pos += dpos * tangent


    runstep()


root.bind("<KeyPress>", key_pressed)
w.pack()

# We call the main function
if __name__ == '__main__':
    runstep()

# Necessary line for Tkinter
mainloop()