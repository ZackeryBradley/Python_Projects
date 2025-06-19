# import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By #used for extracting HTML

#set the internet browser
driver = webdriver.Edge()

#set up to keep webbrowser open after launch
edge_options = webdriver.EdgeOptions()
edge_options.add_experimental_option("detach", True)
#keep the webbrowser open after launch
driver = webdriver.Edge(options=edge_options)

#EXAMPLE USAGE FOR FINDING A REFERENCE IN PYTHON
driver.get("https://www.python.org/")

search_bar = driver.find_element(By.NAME, value="q")

print(search_bar)
#find the search placeholder
# print(search_bar.get_attribute("placeholder"))

button = driver.find_element(By.ID, value="submit")
#find the size of the button within python.org
# print(button.size)

#find a specific element with CSS
documentation_link= driver.find_element(By.CSS_SELECTOR, value=".documentation-widget a") #here we are looking for an anchor tags within the .documentation-widget class
# print(documentation_link.text)

#finding the time tags within the .event-widget class
event_times= driver.find_elements(By.CSS_SELECTOR, value=".event-widget time")

for time in event_times:
    print(time.text)
#find the event names within the website and finding the li interface within the anchor tag
event_names = driver.find_elements(By.CSS_SELECTOR, value=".event-widget li a")
#for loop to print all names in event_names
for name in event_names:
    print(name.text)

  #placing our events within a dictionaru
events ={}
#adding the event times and event names within the dictionary
for n in range(len(event_times)):
    events[n] = {
        "time": event_times[n].text,
        "name": event_names[n].text,
    }
print(events)


#close a particular tab
# driver.close()
#close the entire browser
driver.quit()



