#Day_3_Project Treasure Island Game

print("Welcome to Treasure Island. \n Your mission is to find the treasure. \n")
choice1 = input('You\'re at a crossroad. Where do you want to go? Type "left" or "right". ').lower()
if choice1 == "left":
    choice2 = input('You\'ve come to a lake. there is an island in the middle of the lake. Type "wait" to wait for a boat. Type "swim" to swim across.').lower()
    if choice2 == "wait":
        choice3 = input("You arrive at the island unharmed. There is a house with 3 doors, one red, one yellow, and one blue. Which color do you choose?").lower()
        if choice3 == "yellow":
            print('You open the door and find the room to be filled with treasure. \n Congratulations You\'ve won the game!')
        else:
            print("You attempt to open the door and find that it is locked. Game Over.")
    else:
        print("You swim across the water and get eaten by an alligator. Game Over.")
else:
    print("You get stuck in quicksand. Game Over.")







