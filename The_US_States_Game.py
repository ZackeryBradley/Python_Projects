

#IMPORTS
#########################################################
import turtle
import pandas


#########################################################

screen = turtle.Screen()
screen.title("U.S. States Game")

#path to upload the image
image = "blank_states_img.gif"
screen.addshape(image)
turtle.shape(image)

#importing the excel file
data = pandas.read_csv("50_states.csv")
#pulling the state column from the csv and putting it into a list
all_states = data.state.to_list()
guessed_states = []

while len(guessed_states) < 50:
    answer_state = screen.textinput(title = f"{len(guessed_states)}/50 States Correct", prompt = "What's another state's name?").title()
    print(answer_state)



#if answer_state is one of the states in all the states of the 50_states.csv
#if they got it right:
#create a turtle to write the name of the states at the states x and y coordinate
    if answer_state == "Exit":
        missing_states = []
        for state in all_states:
            if state not in guessed_states:
                missing_states.append(state)
        new_data = pandas.DataFrame(missing_states)
        new_data.to_csv("states_to_learn.csv")
        # print(missing_states)
        break
    if answer_state in all_states:
        guessed_states.append(answer_state)
        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        state_data = data[data.state == answer_state]
        t.goto(int(state_data.x), int(state_data.y))
        t.write(answer_state)

#shows users which states they missed
# states_to_learn.csv

# def get_mouse_click_coor(x, y):
#     print(x, y)
# turtle.onscreenclick(get_mouse_click_coor)



#similiar to screen.exitonclick() command
turtle.mainloop()


