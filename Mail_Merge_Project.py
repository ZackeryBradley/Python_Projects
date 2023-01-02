#TODO:
#Create a letter used starting_letter.docx
#for each name in invited_names.txt
#reolace the [name] placeholder with the actual name
#save the letters in the folder "ReadyToSend"

#CONSTANTS
########################
PLACEHOLDER = "[name]"
########################

#IMPORTS
########################

with open("invited_names.py") as names_file:
    #the readlines command turns the names_file into a list!
    names = names_file.readlines()
    # print(names)

with open("starting_letter.py") as letter_file:
    letter_contents = letter_file.read()
#replaing the [name ] list with the called name
    for name in names:
        stripped_name = name.strip()
        new_letter = letter_contents.replace(PLACEHOLDER, stripped_name)
#taking away the spaces at the beginning or ending of a string
        print(new_letter)
        #importing the "ReadytoSend" files from the folder "ReadyToSend"
        with open(f"./ReadytoSend/letter_for_{stripped_name}.txt", mode = "w") as completed_letter:
            completed_letter.write(new_letter)
