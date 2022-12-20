#turtle race game

######################################
#IMPORTS
from turtle import Turtle, Screen
import random

########################################
#direcion position

#east = 0
#north = 90
#west = 180 
#south = 270

########################################
#ASSIGNMENTS AND SETUP:

is_race_on = False

screen = Screen()
screen.setup(width = 500, height = 400)
user_bet = screen.textinput(title = "Place your bet", prompt = "Which turtle do you think will win the race? Enter a color:\n Choose either 'red', 'green', 'blue', 'black', 'purple' or 'yellow'")
colors = ["red", "green", "blue", "black", "purple", "yellow"]
#testing code:
# print(user_bet)

#for placing the turtle in racing position
y_positions = [-70, -40, -10, 20, 50, 80]
all_turtles = []

for turtle_index in range(0, 5): #range function doesn't include six so you use 5 as the function includes the zero position
    new_turtle = Turtle(shape = "turtle")
    new_turtle.penup()
    #determines the location and direction of the turtle
    #the x position is the starting position
    new_turtle.color(colors[turtle_index])
    new_turtle.goto(x = -230, y = y_positions[turtle_index])
    all_turtles.append(new_turtle)

if user_bet:
    is_race_on = True

while is_race_on:
    for turtle in all_turtles:
        #230 is 250 - half the width of the turtle.(40)
         #xcor is tracking the x coordinate of the turtles position. 
        if turtle.xcor() > 230:
            is_race_on = False
            winning_color = turtle.pencolor()
            if winning_color == user_bet:
                print(f"You've won! The {winning_color} turtle is the winner!")
            else:
                print(f"You've lost! The {winning_color} turtle is the winner!")

        #Make each turtle move a random amount.
        rand_distance = random.randint(0, 10) #this is inclusive and DOES include the number 10 position
        turtle.forward(rand_distance)





screen.exitonclick()


############################################
#TURTLES AND THEIR COLORS
###########################################
# timmy.color = green
