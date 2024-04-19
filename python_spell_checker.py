#this script is intended to correct spelling errors for you. simply type a word in and the automation will then correct the spelling of the word!
from spellchecker import SpellChecker
corrector = SpellChecker()

word = input("Enter a Word : ")
if word in corrector:
    print("Correct")
else:
    correct_word = corrector.correction(word)
    print("Correct Spelling is ", correct_word)