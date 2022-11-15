

print("Welcome to the tip calculator.")
total_bill = input("What was the total bill?")
tip_percentage = input("What percentage tip would you like to give? ")
number_of_people = input("How many people are splitting the bill?")

total_bill = float(total_bill)
tip_percentage = float(tip_percentage) / 100
number_of_people = int(number_of_people) 

final_bill = (total_bill * tip_percentage) + (total_bill) / number_of_people

final_bill = "{:.2f}".format(final_bill)

print(f'Each person should pay : ${final_bill}')