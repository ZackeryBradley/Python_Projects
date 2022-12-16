#Python Turtle challenges
#NOTE: THESE NEED TO BE RAN ONE AT A TIME!!
##########################################
#1. draw a square with the turtle
#2. draw a dashed line with the turtle
#3. drawing different shapes
#4. draw a random walk
#5. draw a spirograph

# ###########################################

# ###########################################
# #IMPORTS AND CONFIGURATION:
# from turtle import Turtle, Screen

# tim = Turtle()
from turtle import Screen
import random
import turtle as t
tim = t.Turtle()
# #changing the screen image shape to "turtle"
tim.shape("turtle")
tim.color("green")

colours = ["CornflowerBlue", "DarkOrchid", "Red", "DeepSkyBlue", "LightSeaGreen", "wheat", "Slategray", "SeaGreen"]
#sets the size of the pen that the turtle is drawn with
tim.pensize(5)
#changing the speed in which the shape is drawn
tim.speed("fastest")

#generate a random color
def random_color():
    r= random.randint(0, 255)
    g= random.randint(0, 255)
    b= random.randint(0, 255)
    color = (r, g, b)
    return color


# ###########################################
#Challenge #1   draw a square with the turtle
#using a for loop to draw a square with the turtle
for _ in range(4):      #telling the command to run 4 times.
    tim.forward(100)
    tim.right(90)
screen = t.Screen()
screen.exitonclick()
###########################################

###########################################
#Challenge #2   draw a dashed line with the turtle
# import turtle as t
# tim = t.Turtle()

for _ in range(15):
    tim.forward(10)
    tim.penup()
    tim.forward(10)
    tim.pendown()

screen = t.Screen()
screen.exitonclick()
###########################################

###########################################
#Challenge #3   drawing different shapes
import turtle as t
tim = t.Turtle()
def draw_shape(num_sides):
    for _ in range(num_sides):
        angle = 360 / num_sides 
        tim.forward(100)
        tim.right(angle)

for shape_side_n in range(3, 11):
    #making every shape a different color
    tim.color(random.choice(colours))
    draw_shape(shape_side_n)


screen = t.Screen()
screen.exitonclick()

###########################################

###########################################
#Challenge #4    draw a random walk

directions = [0, 90, 180, 270] #east, north, west, south

for _ in range(200):
    tim.color(random.choice(colours))
    tim.forward(30)
    #pick a random direction for the turtle to go in
    tim.setheading(random.choice(directions))

screen = t.Screen()
screen.exitonclick()
###########################################

###########################################
#Challenge #5   draw a spirograph

def draw_spirograph(size_of_gap):
    for _ in range(int(360 / size_of_gap)):
        # tim.color(random_color())
        tim.circle(100)
        #making the circle offset
        tim.setheading(tim.heading() + size_of_gap)

draw_spirograph(5)


#getting the screen to close on click
screen = t.Screen()
screen.exitonclick()



############################################