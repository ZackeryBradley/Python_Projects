#the secret auction

from replit import clear

#logo for the silent auction
logo = '''
                         ___________
                         \         /
                          )_______(
                          |"""""""|_.-._,.---------.,_.-._
                          |       | | |               | | ''-.
                          |       |_| |_             _| |_..-'
                          |_______| '-' `'---------'` '-'
                          )"""""""(
                         /_________\\
                       .-------------.
                      /_______________\\
'''

print(logo)

print("Welcome to the Silent Auction!")

bids = {}

bidding_finished =  False

def find_highest_bidder(bidding_record):
    highest_bid = 0

    winner = ""
    # bidding_record = {"zack": 123, "bradley": 321}
    for bidder in bidding_record:
        bid_amount = bidding_record[bidder]
        if bid_amount > highest_bid:
            highest_bid = bid_amount
            winner = bidder
    print(f"The winner is {winner} with a bid of ${highest_bid}")

    # bids = {
    #     "Zack": 123,
    #     "Bradley": 321,
    # }
# find_highest_bidder(bids)
    

while not bidding_finished:
    name = input("What is your name?: ")
    price = int(input("What is your bid?:  $"))
    
    #adding items to the dictionary
    bids[name] = price
    
    should_continue = input("Are there any other bidders? Type 'yes' or 'no'.\n")
    if should_continue ==  "no":
         bidding_finished = True
    elif should_continue == "Yes":
        clear()
        #final code that prints the winner:
    find_highest_bidder(bids)

