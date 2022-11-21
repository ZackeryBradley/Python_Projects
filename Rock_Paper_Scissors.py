

import random

rock = '''
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
'''

paper = '''
    _______
---'   ____)____
          ______)
          _______)
         _______)
---.__________)
'''

scissors = '''
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
'''

game_images = [rock, paper, scissors]

print("Let's play Rock, Paper, Scissors!")
user_choice = int(input("What do you choose? Type 0 for Rock, 1 for Paper, or 2 for Scissors.\n"))


#setting a stopgap in case the user types something outside of the parameters
#this need to be put at the top of the IF statements so python can check for this first!
#this also needs to be placed before the games_images execution so the user cannot choose a number that doesn't have an image.
if user_choice >= 3 or user_choice < 0:
    print("You typed an invalid number. You lose.")
else:
#this will print out the images from above
    print(game_images[user_choice])

computer_choice = random.randint(0, 2)
print("Computer chose:")
print(game_images[computer_choice])
# print(f"Computer chose {computer_choice}.")


if user_choice == 0 and computer_choice == 2:
    print(f"You chose {user_choice} and the computer chose {computer_choice}. You Win!")
elif computer_choice == 0 and user_choice == 2:
    print(f"You chose {user_choice} and the computer chose {computer_choice}. You lose.")

elif computer_choice > user_choice:
    print(f"You chose {user_choice} and the computer chose {computer_choice}. You lose.")
elif user_choice > computer_choice:
     print(f"You chose {user_choice} and the computer chose {computer_choice}. You Win!")

elif computer_choice == user_choice:
      print(f"You chose {user_choice} and the computer chose {computer_choice}. It's a draw!")








