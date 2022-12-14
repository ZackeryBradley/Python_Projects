#oop coffee machine

logo = """

             __  __                            _                  
            / _|/ _|                          | |                 
   ___ ___ | |_| |_ ___  ___    ___ __ _ _ __ | |_ ___  ___ _ __  
  / __/ _ \|  _|  _/ _ \/ _ \  / __/ _` | '_ \| __/ _ \/ _ \ '_ \ 
 | (_| (_) | | | ||  __/  __/ | (_| (_| | | | | ||  __/  __/ | | |
  \___\___/|_| |_| \___|\___|  \___\__,_|_| |_|\__\___|\___|_| |_|
                                                                  
                                                                  
"""


print("Welcome to The Coffee Canteen!\n It's a pleasure to serve you!")

######################################
#PROJECT STEPS
#1. Print Report
#2. Check Resources sufficient
#3. Process coins
#4. Check if transaction is successful
#5. make coffee

#######################################

#######################################
# IMPORTING PACKAGES
from menu import Menu,MenuItem
from coffee_maker import CoffeeMaker
from money_machine import MoneyMachine

#######################################

######################################
#1. Print Report/ Object Creation

#class = object
money_machine = MoneyMachine()
money_machine.report()

coffee_maker = CoffeeMaker()
coffee_maker.report()

menu = Menu()

######################################

#######################################
#2. Check Resources sufficient

is_on = True

while is_on:
    options = menu.get_items()
    choice = input(f"What would you like? ({options}): ")
    if choice == "off":
        is_on = False
    elif choice == "report'":
        coffee_maker.report()
        money_machine.report()
    else:
        drink = menu.find_drink(choice)
#######################################
#3. Process coins
#4. Check if transaction is successful
        if coffee_maker.is_resource_sufficient(drink) and money_machine.make_payment(drink.cost):
            # if money_machine.make_payment(drink.cost):
#######################################
#5. make coffee
                coffee_maker.make_coffee(drink)
            # print(money_machine.make_payment(drink.cost))
        # print(coffee_maker.is_resource_sufficient(drink))
#######################################
