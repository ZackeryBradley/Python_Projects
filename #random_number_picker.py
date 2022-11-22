#random_number_picker

import random

print("I'm thinking of a number....")

user_input = int(input("Pick a number 1 - 10."))

if user_input > 10 or user_input < 0:
    print("That is an invalid number.")

computer_input = random.randint(0, 10)
# print("The number I was thinking of was:")

if user_input == computer_input:
    print("That's the number I was thinking of! You're a mind reader!")
else:
    print(f"Sorry, the number I was thinking of is {computer_input}. Better luck next time!")