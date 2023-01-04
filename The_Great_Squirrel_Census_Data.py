
import pandas

data = pandas.read_csv("2018_Central_Park_Squirrel_Census_-_Squirrel_Data.csv")


#ECTRACTING ALL THE GREY SQUIRRELS FROM THE DATA
#####################################################################################################

grey_squirrels = data[data["Primary Fur Color"] == "Gray"]
print(grey_squirrels)
#getting the count of the grey squirrels
grey_squirrels_count = len(data[data["Primary Fur Color"] == "Gray"])
print(grey_squirrels_count)

#getting different counts of squirrells based on fur color
red_squirrels_count = len(data[data["Primary Fur Color"] == "Cinnamon"])
black_squirrels_count = len(data[data["Primary Fur Color"] == "Black"])
print(red_squirrels_count)
print(black_squirrels_count)

#creating a dictionary of the data
data_dict = {
    "Fur Color": ["Gray", "Cinnamon", "Black"],
    "Count": [grey_squirrels_count, red_squirrels_count, black_squirrels_count]
}
print(data_dict)

#creating a dataframe from the dictionary
df = pandas.DataFrame(data_dict)

#putting the dataframe into a csv
df.to_csv("squirrel_count.csv")
