#fizzbuzz

#how it works:
#if a number if evenly divisible by 3, the script will print "fizz"
#if a number is evenly divisible by 5, the script will print "buzz"
#if a number is evenly divisible by both 3 and 5 the script will print "fizzbuzz"
#ths script will automatically print this out. and will evaluate all numbers between 1 and 100.

for number in range (1, 101):
    if number % 3 == 0 and number % 5== 0: #if the number if divisible by 3 and 5 and the answer equals zero
        print("FizzBuzz")
    elif number % 3 == 0:
        print("Fizz")
    elif number %  5 == 0:
        print("Buzz")
    else:
        print(number)