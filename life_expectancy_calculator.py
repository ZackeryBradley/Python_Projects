#life expectancy calculator 

age = input("What is your current age? ")
age = int(age)

age_estimate = input("How many total years do you expect to live to?")
age_estimate = int(age_estimate)

# life_expectancy = 90 - age

life_expectancy = age_estimate - age

days_remaining = life_expectancy * 365
weeks_remaining = life_expectancy * 52
months_remaining = life_expectancy * 12


print(f'you have {days_remaining} days, {weeks_remaining} weeks, and {months_remaining} months remaining.')