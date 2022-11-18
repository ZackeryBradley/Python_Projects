print("Welcome to the roller coaster!")
height = int(input("What is your height in inches?"))
bill = 0

if height >= 60:
    print("You are able to ride the roller coaster!")
    age = int(input("What is your age?  "))
    if age < 12:
        bill = 5
        print("Please pay $5.")
    elif age <= 18:
        bill = 7
        print("Please pay $7.")
    else: 
        bill = 12
        print("Please pay $12.")

    wants_photo = input("Do you want a photo taken? Please type Y or N.")
    if wants_photo == "Y":
        bill += 3 #adding $3 to a photo if they decided they wanted a photo
    print(f"Your final bill is ${bill}.")    #nest the bill into the sub if statement bc there is no bill if the person cannot ride!
else: 
    print("I'm sorry, you are not tall enough to ride the roller coaster yet.")