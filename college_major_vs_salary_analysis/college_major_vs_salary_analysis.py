import pandas as pd
df = pd.read_csv('salaries_by_college_major.csv')

# @snapshot of data
print(df.head())

#print columns and rows
print(df.shape)

#print column names within data
print(df.columns)

#identifying junk data
print(df.isna())
#tail of data view
print(df.tail())

#drop na values
clean_df = df.dropna()
print(clean_df.tail())

#identifying the starting median salary
print(clean_df['Starting Median Salary'])
#identifying the highest salary
print(f" The highest salary is: {clean_df['Starting Median Salary'].max()}")
#identify the row number of the highest salary
print(f"The index with the highest salary is: {clean_df['Starting Median Salary'].idxmax()}")
#find the major of the higest salary
print(f"the major with the highest salary is {clean_df['Undergraduate Major'].loc[43]}")
#looking at the entire row for the highest salary
print(clean_df.loc[43])

#highest mid career salary
print(clean_df['Mid-Career Median Salary'].max())
print(f"Index for the max mid career salary: {clean_df['Mid-Career Median Salary'].idxmax()}")
#lowest starting career salary
print(clean_df['Starting Median Salary'].min())
#index with the lowest starting salary
print(f"The index for the lowest starting salary is: clean_df['Starting Median Salary'].idxmin()")

#most potential vs lowest risk
spread_col = clean_df['Mid-Career 90th Percentile Salary'] - clean_df['Mid-Career 10th Percentile Salary']
#insert new column
clean_df.insert(1, 'Spread', spread_col)
print(clean_df.head())

#sorting by the lowest spread
low_risk = clean_df.sort_values('Spread')
print(low_risk[['Undergraduate Major', 'Spread']].head())

#majors with the higest earning potential
highest_potential = clean_df.sort_values('Mid-Career 90th Percentile Salary', ascending=False)
print(highest_potential[['Undergraduate Major', 'Mid-Career 90th Percentile Salary']].head())
#majors with the higest spread ub salaries
highest_spread = clean_df.sort_values('Spread', ascending=False)
print(highest_spread[['Undergraduate Major', 'Spread']].head())
#getting the count of the majors within each category
print(clean_df.groupby('Group').count())
#getting the average salary of each group
#formatting the data in a currency format
pd.options.display.float_format = '{:,.2f}'.format
#getting only numeric columns in the data
numeric_cols = clean_df.select_dtypes(include='number').columns
#printing to find the number columns
print(clean_df.groupby('Group')[numeric_cols].mean())