#Coffee Machine Project

logo = """

             __  __                            _                  
            / _|/ _|                          | |                 
   ___ ___ | |_| |_ ___  ___    ___ __ _ _ __ | |_ ___  ___ _ __  
  / __/ _ \|  _|  _/ _ \/ _ \  / __/ _` | '_ \| __/ _ \/ _ \ '_ \ 
 | (_| (_) | | | ||  __/  __/ | (_| (_| | | | | ||  __/  __/ | | |
  \___\___/|_| |_| \___|\___|  \___\__,_|_| |_|\__\___|\___|_| |_|
                                                                  
                                                                  
"""

##########################################
#STEPS FOR PROJECT:

#1. print the report
#2. check if resources for coffee is sufficient
#3. Process coins (coin operated)
#4. check if transactions is successful 
#5. Make Coffee
############################################


print("Welcome to The Coffee Canteen!\n It's a pleasure to serve you!")
################################################
#2. check if resources for coffee is sufficient
MENU = {
    "espresso": {
        "ingredients": {
            "water": 50,
            "coffee": 18,
        },
        "cost": 1.5,
    },
    "latte": {
        "ingredients": {
            "water": 200,
            "milk": 150,
            "coffee": 24,
        },
        "cost": 2.5,
    },
    "cappuccino": {
        "ingredients": {
            "water": 250,
            "milk": 100,
            "coffee": 24,
        },
        "cost": 3.0,
    }
}

profit = 0
resources = {
    "water": 300,
    "milk": 200,
    "coffee": 100,
}
##################################################
#DEFINITION CREATION:

def is_resource_sufficient(order_ingredients):
    """Returns True when order can be made and False if ingredients are insufficient."""
    for item in order_ingredients:
      if  order_ingredients[item] > resources[item]:
            print(f"Sorry, there is not enough {item}.")
            return False
    return True
################################################
#3. Process coins (coin operated)
def process_coins():
    """Returns the total calculated from coins inserted."""
    print("Please insert coins.")
    total = int(input("how many quarters did you put in?:")) * 0.25
    total += int(input("how many dimes did you put in?:")) * .10
    total += int(input("how many nickles did you put in?:")) * .05
    total += int(input("how many pennies did you put in?:")) * .01
    return total

#check if transactions is successful 
def is_transactions_successful(money_received, drink_cost):
    """Return True when payment is accepted or False when payment is insufficient."""
    if money_received >=  drink_cost:
        change = round(money_received - drink_cost, 2) #rounding to 2 decimal places
        print(f" Here is ${change} in change.")
        global profit
        profit += drink_cost
        return True
    else:
        print("Sorry, that's not enough money. Your Money has been refunded.") 
        return False

def make_coffee(drink_name, order_ingredients):
    """Deduct the required ingredients from the resources."""
    for item in order_ingredients:
        resources[item] -= order_ingredients[item]
    print(f"here is your {drink_name} ☕️. Enjoy! ")


###################################################


#asking the user what coffee they would like
print(logo)
is_on = True

while is_on:
    choice = input("What would you like? We have Espresso, Latte, and Cappuccino: ").lower()
#turning the coffee machine off, ending the while loop.
    if choice == "off":
        is_on = False
################################################
#1. print the report:
#you can use SHIFT + ALT here and drag your cursor to edit multiple lines at once time!!
    elif choice == "report":
       print(f"Water: {resources['water']}ml")
       print(f"Milk: {resources['milk']}ml")
       print(f"Coffee: {resources['coffee']}g")
       print(f"Money: ${profit}")
################################################
#4. check if transactions is sufficient
    else:
        drink = MENU[choice]
        if is_resource_sufficient(drink["ingredients"]):
           payment = process_coins()
        if is_transactions_successful(payment, drink["cost"]):
           ################################################
#5. Make Coffee
           make_coffee(choice, drink["ingredients"])
################################################







