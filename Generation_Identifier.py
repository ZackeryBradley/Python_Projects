#generation selector




logo = '''

   _____                           _   _               _____    _            _   _  __ _           
  / ____|                         | | (_)             |_   _|  | |          | | (_)/ _(_)          
 | |  __  ___ _ __   ___ _ __ __ _| |_ _  ___  _ __     | |  __| | ___ _ __ | |_ _| |_ _  ___ _ __ 
 | | |_ |/ _ \ '_ \ / _ \ '__/ _` | __| |/ _ \| '_ \    | | / _` |/ _ \ '_ \| __| |  _| |/ _ \ '__|
 | |__| |  __/ | | |  __/ | | (_| | |_| | (_) | | | |  _| || (_| |  __/ | | | |_| | | | |  __/ |   
  \_____|\___|_| |_|\___|_|  \__,_|\__|_|\___/|_| |_| |_____\__,_|\___|_| |_|\__|_|_| |_|\___|_|   
                                                                                                   
                                                                                                   
'''
print(logo)

print("Welcome to the generation finder!")
generation = int(input("What year where you born in?"))

if generation >= 1901 and generation <= 1924:
    print("You are part of the Greatest Generation (GI).")
elif generation >= 1928 and generation <= 1945:
    print("You are part of the Silent Generation.")
elif generation >= 1946 and generation <= 1964:
    print("You are part of the Baby Boomer Generation.")
elif generation >= 1965 and generation <= 1980:
    print("You are considered part of Generation X")
elif generation >= 1981 and generation <= 1996:
    print("You are a Millennial.")
elif generation >= 1997 and generation <= 2010:
    print("You are considered part of Generation Z")
elif generation >= 2010:
    print("You are considered part of the Generation Alpha")
else:
    print("You're generation has not been recognized!")