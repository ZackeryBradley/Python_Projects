#Python_Etch_a_Sketch

################################
#CONTENT KEY:
# Up  = Forwards
# Down = Backwards
# Left = Counter-Clockwise
# Right = Clockwise
# c = Clear drawing
##################################

from turtle import Turtle, Screen

tim = Turtle()
screen = Screen()

def move_forwards():
    tim.forward(10)

def move_backwards():
    tim.backward(10)

def turn_left():
    new_heading = tim.heading() + 10 #adding 10 degrees
    tim.setheading(new_heading)

def turn_right():
    new_heading = tim.heading() - 10 #subtracting 10 degrees
    tim.setheading(new_heading)

def clear():
    tim.clear()
    tim.penup()
    tim.home()
    tim.pendown()

screen.listen()
screen.onkey(move_forwards, "Up") #the letter acts as the character that needs to be pressed to complete the command
screen.onkey(move_backwards, "Down")
screen.onkey(turn_left, "Left")
screen.onkey(turn_right, "Right")
screen.onkey(clear, "c")

screen.exitonclick()