#higher or lower project

#display art
logo = """

  _    _ _       _                              _                        
 | |  | (_)     | |                            | |                       
 | |__| |_  __ _| |__   ___ _ __    ___  _ __  | | _____      _____ _ __ 
 |  __  | |/ _` | '_ \ / _ \ '__|  / _ \| '__| | |/ _ \ \ /\ / / _ \ '__|
 | |  | | | (_| | | | |  __/ |    | (_) | |    | | (_) \ V  V /  __/ |   
 |_|  |_|_|\__, |_| |_|\___|_|     \___/|_|    |_|\___/ \_/\_/ \___|_|   
            __/ |                                                        
           |___/                                                         
                                                  
"""
logo2 = """

           
__   _____ 
\ \ / / __|
 \ V /\__ |
  \_/ |___/
           
"""

print("Welcome to the Higher or Lower game! \n guess which celebrity has more Instagram followers!")
###################################

#testing the logos 

# print(logo)
# print(logo2)
###################################

#importing needed files
from game_data import data
import random
from replit import clear

##########################################

#Definitions Created:

#2. format the account data into printable format
#this will pull out the value of the "name" inside the imported game_data file
#creating an account def to call for account_a and account_b
"""Takes the account data and returns the  printable format."""
def format_data(account):
    account_name = account["name"]
    account_descr = account["description"]
    account_country = account["country"]
    return (f"{account_name}, a {account_descr}, from {account_country}")
###############################################################################


#6. use if statement to check if user is correct
"""Takes the user guess and follower counts and returns if they got it right."""
def check_answer(guess, a_followers, b_followers):
    if a_followers > b_followers:
        return guess == "a"
    else:
        return guess == "b"

#################################################################################
#Setting Parameters for variables
#8. score keeping
score = 0

#############################################
#steps for project

#1. generate a random account from the game data
#2. format the account data into printable format
#3. ask user for a guess
#4. check is user is correct
#5. get follower count of each account
#6. use if statement to check if user is correct
#7. give user feedback on their guess
#8. score keeping
#9. make game repeatable
############################################

#9. make game repeatable

game_should_continue = True
account_b = random.choice(data)
while game_should_continue:

#making account at position B become the next account at position A
#######################################################
#1. generate a random account from the game data
    account_a = account_b
    # account_a = random.choice(data)
    account_b = random.choice(data)

#implementing a fail safe in case the program tries to comparable two alike sources of data
    while account_a == account_b:
        account_b = random.choice(data)
    print(f" Compare A: {format_data(account_a)}")
    print(logo2)
    print(f" Against B: {format_data(account_b)}")
########################################################################

# #2. format the account data into printable format
# #this will pull out the value of the "name" inside the imported game_data file
# account_name = account_a["name"]
# account_descr = account_a["description"]
# account_country = account_a["country"]
# print(f"{account_name}, a {account_descr}, from {account_country}")
#######################################################################

#3. ask user for a guess

    guess = input("Who has more followers? Type 'A' or 'B': ").lower()

###########################################################
#5. get follower count of each account
#since our key is a string, we put use quotes inside the brackets to tap into it!
    a_follower_count = account_a["follower_count"]
    b_follower_count = account_b["follower_count"]

##############################################################

#6. use if statement to check if user is correct

    is_correct = check_answer(guess, a_follower_count, b_follower_count)

#clear the screen after rounds
    clear()
    print(logo2)

###############################################################

#7. give user feedback on their guess
    if is_correct:
        score += 1
        print(f"You're right! Current score: {score}")
    else:
        game_should_continue = False
        print(f"Sorry, that's wrong. Final Score: {score}")

###############################################################

