
print("Welcome to the Love Calculator!")
name1 = input("What is your name? \n")
name2 = input("What is their name? \n")

couple_name = name1 + name2
lower_case_couple_name = couple_name.lower()
t = lower_case_couple_name.count("t")
r = lower_case_couple_name.count("r")
u = lower_case_couple_name.count("u")
e = lower_case_couple_name.count("e")

true = t + r + u + e 

l = lower_case_couple_name.count("l")
o = lower_case_couple_name.count("o")
v = lower_case_couple_name.count("v")
e = lower_case_couple_name.count("e")

love = l + o + v + e 

love_score = int(str(true) + str(love))

#int_score = int(love_score)
#print(love_score)

if love_score < 10 or love_score > 90:
    print(f"Your score is {love_score}, you go together like coke and mentos.")
elif love_score >= 40 and love_score <= 50:
    print(f"Your score is {love_score}, you are alright together.")
else:
    print(f"Your score is {love_score}.")