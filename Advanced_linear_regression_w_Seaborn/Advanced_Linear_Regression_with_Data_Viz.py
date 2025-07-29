import pandas as pd
import matplotlib.pyplot as plt

import seaborn as sns
from sklearn.linear_model import LinearRegression

pd.options.display.float_format = '{:,.2f}'.format

#present notebook
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
#read data
data = pd.read_csv('cost_revenue_dirty.csv')

#explore and clean the data
print(data.shape)
print(data.sample(5))
print(data.tail())

print(f'Any NaN values among the data? {data.isna().values.any()}')
print(f'Any duplicates? {data.duplicated().values.any()}')

duplicated_rows = data[data.duplicated()]
print(f'Number of duplicates: {len(duplicated_rows)}')

#show NAN values and dtypes per column
print(data.info())

#dtype conversions
chars_to_remove = [',', '$']
columns_to_clean = ['USD_Production_Budget',
                    'USD_Worldwide_Gross',
                    'USD_Domestic_Gross']

for col in columns_to_clean:
    for char in chars_to_remove:
        #replace char w/ empty string
        data[col] = data[col].astype(str).str.replace(char, "")
    #convert column to numeric dtype
    data[col] = pd.to_numeric(data[col])

print(data.head())
#convert column to datetime dtype
data.Release_Date = pd.to_datetime(data.Release_Date)
data.head()
print(data.info())

#descriptive statistics
print(data.describe())

#how many filmes grossed zero dollar in the us?
zero_domestic = data[data.USD_Domestic_Gross == 0]
print(f'Number of films that grossed $0 domestically {len(zero_domestic)}')
zero_domestic.sort_values('USD_Production_Budget', ascending=False)

#how many films grossed zero dollars worldwide?
zero_worldwide = data[data.USD_Worldwide_Gross == 0]
print(f'Number of films that grossed $0 worldwide {len(zero_worldwide)}')
zero_worldwide.sort_values('USD_Production_Budget', ascending=False)

#filtering on our newly found metrics
international_releases = data.loc[(data.USD_Domestic_Gross == 0) &
                                  (data.USD_Worldwide_Gross != 0)]
print(f'Number of international releases: {len(international_releases)}')
international_releases.head()
#here is another more "SQL" language way of filtering the same thing!
international_releases = data.query('USD_Domestic_Gross == 0 and USD_Worldwide_Gross != 0')
print(f'Number of international releases: {len(international_releases)}')
international_releases.tail()

#identify unreleased films as of the time our dataset was built from 2018-05-01
scrape_date = pd.Timestamp('2018-5-1')

future_releases = data[data.Release_Date >= scrape_date]
print(f'Number of unreleased movies: {len(future_releases)}')
future_releases

#exclude any future releases
data_clean = data.drop(future_releases.index)
#identifying the numerical differences between unreleased and future released
data.shape[0] - data_clean.shape[0]

#percentage of films that lost money
money_losing = data_clean.loc[data_clean.USD_Production_Budget > data_clean.USD_Worldwide_Gross]
print(len(money_losing)/len(data_clean))
#another way to do this by using .query()
money_losing = data_clean.query('USD_Production_Budget > USD_Worldwide_Gross')
print(money_losing.shape[0]/data_clean.shape[0])

# revenue vs budget seaborn scatterplot
plt.figure(figsize=(8,4), dpi=200)

ax = sns.scatterplot(data=data_clean,
                     x='USD_Production_Budget',
                     y='USD_Worldwide_Gross',
                     hue='USD_Worldwide_Gross',  #change colour
                     size='USD_Worldwide_Gross',) #change size of dot


ax.set(ylim=(0, 3000000000),
       xlim=(0, 450000000),
       ylabel='Revenue in $ billions',
       xlabel='Budget in $100 millions')

plt.show()

#plotting movie releases over time
plt.figure(figsize=(8,4), dpi=200)

with sns.axes_style("darkgrid"):
    ax = sns.scatterplot(data=data_clean,
                    x='Release_Date',
                    y='USD_Production_Budget',
                    hue='USD_Worldwide_Gross',
                    size='USD_Worldwide_Gross',)

    ax.set(ylim=(0, 450000000),
           xlim=(data_clean.Release_Date.min(), data_clean.Release_Date.max()),
           xlabel='Year',
           ylabel='Budget in $100 millions')

#create a column that has the movie release for decades
dt_index = pd.DatetimeIndex(data_clean.Release_Date)
years = dt_index.year

#conversion math
decades = years//10*10
data_clean['Decade'] = decades

#separate movies <= 1969 as 'old' and >= 1970 as 'new'
old_films = data_clean[data_clean.Decade <= 1960]
new_films = data_clean[data_clean.Decade > 1960]
print(old_films.describe())

print(old_films.sort_values('USD_Production_Budget', ascending=False).head())

#regression plotting for budget vs revenue
plt.figure(figsize=(8, 4), dpi=200)
with sns.axes_style('darkgrid'):
    ax = sns.regplot(data=new_films,
                     x='USD_Production_Budget',
                     y='USD_Worldwide_Gross',
                     color='#2f4b7c',
                     scatter_kws={'alpha': 0.3},
                     line_kws={'color': '#ff7c43'})

    ax.set(ylim=(0, 3000000000),
           xlim=(0, 450000000),
           ylabel='Revenue in $ billions',
           xlabel='Budget in $100 millions')

#run a regression using scikit
regression = LinearRegression()
#explanatory value
X = pd.DataFrame(new_films, columns=['USD_Production_Budget'])
#response variable
y = pd.DataFrame(new_films, columns=['USD_Worldwide_Gross'])

#find the line of best fit
regression.fit(X, y)
#find the theta zero
print(regression.intercept_)
#find the theta one
print(regression.coef_)
#find R squared
print(regression.score(X, y))

#calculate the intercept, slope and r squared for old films
X = pd.DataFrame(old_films, columns=['USD_Production_Budget'])
y = pd.DataFrame(old_films, columns=['USD_Worldwide_Gross'])
regression.fit(X, y)
print(f'The slope coefficient is: {regression.coef_[0]}')
print(f'The intercept is: {regression.intercept_[0]}')
print(f'The r-squared is: {regression.score(X, y)}')

#givwen our answers, how much global revenue does our model estimate for a film with a budget of 350 million?
(22821538 + 1.64771314) * 350000000

budget = 350000000
revenue_estimate = regression.intercept_[0] + regression.coef_[0,0]*budget
revenue_estimate = round(revenue_estimate, -6)
print(f'The estimated revenue for a $350 film is around ${revenue_estimate:.10}.')