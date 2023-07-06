
# this is a simple  program that will identify whether a sequence of numbers could possibly be a phone number or not according to our criteria


def is_phone_number(text):
    if len(text) != 12:
        return False
    for i in range(0, 3):
        if not text[i].isdecimal():
            return False
    if text[3] != '-':
        return False
    for i in range(4, 7):
        if not text[i].isdecimal():
            return False
        for i in range(8, 12):
            if not text[i].isdecimal():
                return False
    return True

#examples of checking for a phone number
print('Is 415-555-4242 a phone number?')
print(is_phone_number('415-555-4242'))
print('Is Moshi moshi a phone number?')
print(is_phone_number('Moshi moshi'))


#message to identify a phone number
message = 'Call me at 415-555-1011 tomorrow.'

for i in range(len(message)):
    chunk = message[i:i+12]
    if is_phone_number(chunk):
        print('Phone number found: ' + chunk)
print('Done')