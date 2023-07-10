# guessing game:
import random

number = random.randint(1, 100)
print("Welcome to the Guessing game!")
print("Please pick a number between 1 and 100.")

# ask the player 5 guesses
for guess_taken in range(1, 6):
    print("Take a guess.")
    guess = int(input())

    if guess < number:
        print("Your guess is too low.")
    elif guess > number:
        print("Your number is too high.")
    else:
        break  # this condition is for the correct guess

if guess == number:
    print("Your guess is correct! You Win! You guessed in correct number in " + str(guess_taken) + 'gusses!')
else:
    print("Sorry, you have run out of chanes. The number I was thinking of was " + str(
        number) + ". Better luck next time!")



