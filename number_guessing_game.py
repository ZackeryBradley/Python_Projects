#the number guessing game

from random import randint


# print("Welcome to the number guessing game!\n I'm thinking of a number between 1 and 100.")
# print("I'm thinking of a number between 1 and 100")
Logo = r"""

 ________                                __  .__                                 ___.                 
 /  _____/ __ __   ____   ______ ______ _/  |_|  |__   ____     ____  __ __  _____\_ |__   ___________ 
/   \  ___|  |  \_/ __ \ /  ___//  ___/ \   __\  |  \_/ __ \   /    \|  |  \/     \| __ \_/ __ \_  __ \
\    \_\  \  |  /\  ___/ \___ \ \___ \   |  | |   Y  \  ___/  |   |  \  |  /  Y Y  \ \_\ \  ___/|  | \/
 \______  /____/  \___  >____  >____  >  |__| |___|  /\___  > |___|  /____/|__|_|  /___  /\___  >__|   
        \/            \/     \/     \/             \/     \/       \/            \/    \/     \/    
"""

print(Logo)


#global constant to switch game around
EASY_LEVEL_TURNS = 10
HARD_LEVEL_TURNS = 5


#function to check users guess against actual answer

def check_answer(guess, answer, turns):
    """checks answer against guess and returns the number of turns remaining."""
    if guess > answer:
        print("Your guess is too high.")
        return turns - 1
    elif guess < answer:
        print("Your guess is too low. ")
        return turns - 1
    else:
        print(f"Congratulations, you win! The answer was {answer}")


#make a function to set the difficulty
def set_difficulty():
    level = input("Choose a difficulty. Type 'easy' or 'hard':")
    if level == 'easy':
        return EASY_LEVEL_TURNS
    else:
        return HARD_LEVEL_TURNS



def game():      
#choose a random number between 1 and 100
    print(logo)
    print("Welcome to the number guessing game!\n I'm thinking of a number between 1 and 100.")
    print("I'm thinking of a number between 1 and 100")

    answer = randint(1, 101)

#testing code
    #print(f"psst The correct answer is {answer}")
    
    turns = set_difficulty()

#repeat the guessing functionality if they get it wrong
    guess = 0
    while guess != answer:
        print(f" You have {turns} attempts remaining to guess the number.")


#let the user guess a number    
        guess = int(input("Guess a number between 1 and 100: "))

#to call the script to check the answer after the user performs a guess
        turns = check_answer(guess, answer, turns)
        if turns == 0:
            print("You have run out of guesses. You lose.")
            #this code will end the game since the game is inside of a function
            return
        elif guess != answer:
            ("Guess again.")


#track the number of guesses and reduce the guesses by 1 if they get it wrong

game()



