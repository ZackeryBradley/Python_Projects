#this program is intended to build a stopwatch using Python

import time

#display the instructions of the program

print('Press ENTER to begin. Afterward, press Enter to "click" the stopwatch. Press Ctrl-C to quit.')

input() #press enter to begin

print('The Stopwatch has started.')

start_time = time.time() #getting the first lap's start time
last_time = start_time
lap_num = 1

#start tracking the lap times.

try:
    while True:
        input()
        lap_time = round(time.time() - last_time, 2) #this will round the seconds to two deicmal places
        total_time = round(time.time() - start_time, 2)
        print('Lap #%s: %s (%s)' % (lap_num, total_time, lap_time), end = '')
        lap_num += 1
        last_time = time.time() #this will reset the last lap time
except KeyboardInterrupt:
    #Handle the Ctrl-C exception to keep its error message from displaying
    print('/nDone.')



