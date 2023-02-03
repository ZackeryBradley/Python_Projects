##
#LEARNING MATERIALS IN THIS SCRIPT
#1. stored_functions - goes over the stored functions in python
#2. collection_methods- goes over how each stored function can perform collection techniques
#3. organization_methods - goes over how each stored function can organize data
#4. count_methods - goes over how each stored function can performing counting measures

STORED_FUNCTIONS = {
    "list": 'A list of ordered data, normally to store needed characters or numbers[]',
    "tuple": 'An ordered collection of data normally used to store information()',
    "sets": 'an unordered collection normally used to as a constant{}',
    "dictionaries": 'an unordered collection of data that stores daya in key value pairs, like this dictionary{}'
}

# print(STORED_FUNCTIONS)


####
# EXAMPLES OF A LIST
#**These can be concatenated with other lists!**
# numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# print(sum(numbers))
# print(numbers[3])

###
# EXAMPLES OF A TUPLE
#**These can be concatenated with other tuples!**
# random_info = ("hello", 42, 35, "how are you?")
# print(random_info[0])
# print(random_info[3])

####
#EXAMPLE OF A SET
# random_set = {1, 2, 3, 4, 5}
# print(random_set)

####
# EXAMPLE OF A DICTIONARY
# random_dict = {
#     "value0": 0,
#     "value1": 1,
#     "value2": 2,
#     "value3": 3
# }
# print(random_dict.keys()) #all the keys are printed
# print(random_dict.values()) #all the values are printed
# print(random_dict) #printing the entire dictionary
# print(random_dict["value0"]) #only printing one value

############################################################################
# LIST_COLLECTION_METHODS = {
#     "append": 'append adds a single item at the of a LIST without modifying the original list. append()',
#     "pop": 'removes the item at the given index from the LIST and returns it. pop()'
# }
# print(LIST_COLLECTION_METHODS)

#EXAMPLES OF LIST_COLLECTION_METHODS
#append()
# list1 = ["zack", "todd", "blake"]
# list1.append("charles")
# print(list1)
#
# # pop()
# list1.pop()
# print(list1)
############################################################################

############################################################################

SET_COLLECTION_METHODS = {
    "add": 'adds a given element to a SET. add()',
    "pop": 'removes a random item from a SET. pop()'
}
# print(SET_COLLECTION_METHODS)

#EXAMPLES OF SET COLLECTION METHODS
# set1= {"protein", "carbs", "sugars"}
# set1.add("starches")
# print(set1)
#
# set1.pop()
# print(set1)
############################################################################

############################################################################

DICTIONARY_COLLECTION_METHODS = {
    "update": 'updates the DICTIONARY with the specified key-value pairs. update()',
    "pop": 'removes the specified item from the DICTIONARY. pop()'
}

#EXAMPLES OF DICTIONARY COLLECTIONARY METHODS
# dict1 = {
#     "fruit1": "apple",
#     "fruit2": "banana",
#     "fruit3": "strawberry"
# }
#
# dict1.update({"fruit4": "orange"})
# print(dict1)
#
# dict1.pop("fruit4")
# print(dict1)
############################################################################

############################################################################
#ORGANIZATION_METHODS

LIST_ORGANIZATION = {
    "sort": "sorts the elements of a given list in a specific ascending or descending order. sort()",
    "index":  "searches for a given element from the start of the list and returns the lowest index where the element appears"

}

#EXAMPLES OF LIST_ORGANIZATION

# print(list1.index("zack"))

############################################################################


TUPLE_ORGANIZATION = {
    "index": "searches for a given element from the start of the list and returns the specific index where the element appears"
}

#EXAMPLES OF TUPLE_ORGANIZATION
# tuple1 = (1, 3, 5, 7, 9)
# print(tuple1.index(7)) #this will return 3
#
# DICTIONARY_ORGANIZATION = {
#     "get": "returns the value of the specific item"
# }
# print(dict1.get("fruit1"))
############################################################################

LIST_COUNT_METHODS = {
    "count": "returns the number of times the specified element appears in the list",
    "reverse": "reverses the elements of a list"
}

#EXAMPLE OF LIST COUNT METHODS
# list2 = [0, 1, 2, 3]
# print(list2.count(0))
#
# print(list2.reverse())