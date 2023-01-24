#this is a flash card program meant to teach the user common words in french

from tkinter import *
import pandas
import random

BACKGROUND_COLOR = "#B1DDC6"
current_card = {}
to_learn = {}

try:
    data = pandas.read_csv("words_to_learn.csv")
    # print(data)
except FileNotFoundError:
    original_data = pandas.read_csv("french_words.csv")
    print(original_data)
    to_learn = original_data.to_dict(orient= "records")
else:
    #converting our data frame to a dictionary
    to_learn = data.to_dict(orient = "records")
    # print(to_learn)

# current_card = {}

def next_card():
    global current_card, flip_timer
    window.after_cancel(flip_timer)
    current_card = random.choice(to_learn)
    # print(current_card["French"])
    canvas.itemconfig(card_title, text= "French", fill = "black")
    canvas.itemconfig(card_word, text= current_card["French"], fill = "black")
    canvas.itemconfig(card_background, image = card_front_img)
    flip_timer = window.after(3000, func= flip_card)

#function for changing the card front to the card back
def flip_card():
    canvas.itemconfig(card_title, text = "English", fill = "white")
    canvas.itemconfig(card_word, text = current_card["English"], fill = "white")
    canvas.itemconfig(card_background, image= card_back_img)

def is_known():
    to_learn.remove(current_card)
    print(len(to_learn))
    data = pandas.DataFrame(to_learn)
    data.to_csv("words_to_learn.csv", index = False)
    next_card()

window = Tk()
window.title("Flash_Cards")
window.config(padx = 50, pady = 5, bg = BACKGROUND_COLOR)

#this will automatically switch the flashcsards around after 3 seconds
flip_timer = window.after(3000, func= flip_card)

#this will allow us to create the flashcards with the images

canvas = Canvas(width = 800, height = 526)
card_front_img = PhotoImage(file = "card_front.png")
card_back_img = PhotoImage(file = "card_back.png")
card_background = canvas.create_image(400, 263, image=card_front_img)
card_title = canvas.create_text(400, 150, text = "", font = ("Ariel", 40, "italic"))
card_word = canvas.create_text(400, 263, text = "", font=("Ariel", 60, "bold"))

canvas.config(bg=BACKGROUND_COLOR, highlightthickness= 0)
canvas.grid(row=0, column=0, columnspan=2)

#creating the 'wrong' image
cross_image = PhotoImage(file= "wrong.png")
unknown_button = Button(image = cross_image, highlightthickness=0, command=next_card)
unknown_button.grid(row = 1, column = 0)

#creating the checkmark image
check_image = PhotoImage(file = "right.png")
known_button = Button(image = check_image, highlightthickness= 0, command=is_known)
known_button.grid(row=1, column =1)

next_card()


window.mainloop()




