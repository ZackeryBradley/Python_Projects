import pandas as pd
import plotly.express as px

df = pd.read_csv('apps.csv')
print(df)
print(df.shape)
#remove unwanted columns
df.drop(['Last_Updated', 'Android_Ver'], axis=1, inplace=True)
print(df.head)

#removing uneeded rows
nan_rows = df[df.isna()]
print(nan_rows.shape)
print(nan_rows.head)

df_clean = df.dropna()
print(df_clean.shape)

#remove duplicated rows
duplicated_rows = df_clean[df_clean.duplicated()]
print(duplicated_rows)
print(duplicated_rows.head)

df_clean = df_clean.drop_duplicates(subset=['App', 'Type', 'Price'])
print(df_clean[df_clean.App== 'Instagram'])

print(df_clean.sort_values('Rating', ascending=False).head())
print(df_clean.sort_values('Size_MBs', ascending=False).head())
print(df_clean.sort_values('Reviews', ascending=False).head())

ratings= df_clean.Content_Rating.value_counts()
print(ratings)

#building donut chart chart

fig= px.pie(labels=ratings.index,
            values=ratings.values,
            title="Content Rating",
            names= ratings.index,
            hole = 0.6 #needed to build donut
            )
fig.update_traces(textposition='inside',textfont_size= 15, textinfo='percent+label')
fig.show()

#cleaning and converting data
print(df_clean.Installs.describe())
print(df_clean.info)

#clean up the group by by removing the comma
df_clean.Installs = df_clean.Installs.astype(str).str.replace(',',"")
#convert dtype to numeric
df_clean.Installs = pd.to_numeric(df_clean.Installs)
print(df_clean[['App', 'Installs']].groupby('Installs').count())

#clean the price column
df_clean.Price = df_clean.Price.astype(str).str.replace('$', "")
df_clean.Price = pd.to_numeric(df_clean.Price)
print(df_clean.sort_values('Price', ascending=False).head(20))

#remove bad data in the price column
df_clean = df_clean[df_clean['Price'] < 250]
print(df_clean.sort_values('Price', ascending=False).head(5))

#highest grossing paid apps
df_clean['Revenue_Estimate'] = df_clean.Installs.mul(df_clean.Price)
print(df_clean.sort_values('Revenue_Estimate', ascending=False)[:10])

#number of unique categories
print(df_clean.Category.nunique())
#calculate number of apps per category
top10_category = df_clean.Category.value_counts()[:10]

#plot our metrics in a bar chart
bar = px.bar(x= top10_category.index,
             y= top10_category.values)
bar.show()
#group apps by categorya dn then sum the number of installations
category_installs = df_clean.groupby('Category').agg({'Installs': pd.Series.sum})
category_installs.sort_values('Installs', ascending=True, inplace=True)

#plot our metrics in a horizontal bar chart
h_bar = px.bar(x=category_installs.Installs,
               y=category_installs.index,
               orientation='h')
#add labels and titles
h_bar.update_layout(xaxis_title='Number of Downloads', yaxis_title='Category')
h_bar.show()

#scatter plot build
#grab the nu,ber or apps in each category
cat_number = df_clean.groupby('Category').agg({'App': pd.Series.count})
#merge the two dataframes together
cat_merged_df = pd.merge(cat_number, category_installs, on='Category', how="inner")
print(f'The dimensions of the DataFrame are: {cat_merged_df.shape}')
cat_merged_df.sort_values('Installs', ascending=False)

#create the scatterplot
scatter = px.scatter(cat_merged_df,  # data
                     x='App',  # column name
                     y='Installs',
                     title='Category Concentration',
                     size='App',
                     hover_name=cat_merged_df.index,
                     color='Installs')

scatter.update_layout(xaxis_title="Number of Apps (Lower=More Concentrated)",
                      yaxis_title="Installs",
                      yaxis=dict(type='log'))

scatter.show()

#split strings on the semi-colon and then using the .stack gunction to dtavk them
stack = df_clean.Genres.str.split(';', expand=True).stack()
print(f'We now have a single column with shape: {stack.shape}')
num_genres = stack.value_counts()
print(f'Number of genres: {len(num_genres)}')

#create a bar chart with custom coloration
bar = px.bar(x=num_genres.index[:15],  #index = category name
             y=num_genres.values[:15],
             title='Top Genres',
             hover_name=num_genres.index[:15],
             color=num_genres.values[:15],
             color_continuous_scale='Agsunset')

bar.update_layout(xaxis_title='Genre',
                  yaxis_title='Number of Apps',
                  coloraxis_showscale=False)

bar.show()

#categorizing by type
df_free_vs_paid = df_clean.groupby(["Category", "Type"], as_index=False).agg({'App': pd.Series.count})
print(df_free_vs_paid.head())

#using collor to contrast free versus paid apps
g_bar = px.bar(df_free_vs_paid,
               x='Category',
               y='App',
               title='Free vs Paid Apps by Category',
               color='Type',
               barmode='group')

g_bar.update_layout(xaxis_title='Category',
                    yaxis_title='Number of Apps',
                    xaxis={'categoryorder': 'total descending'},
                    yaxis=dict(type='log'))

g_bar.show()

#box plot creation to show the number of installs by type
box = px.box(df_clean,
             y='Installs',
             x='Type',
             color='Type',
             notched=True,
             points='all',
             title='How Many Downloads are Paid Apps Giving Up?')

box.update_layout(yaxis=dict(type='log'))

box.show()

#box plot for app revenue by category
df_paid_apps = df_clean[df_clean['Type'] == 'Paid']
box = px.box(df_paid_apps,
             x='Category',
             y='Revenue_Estimate',
             title='How Much Can Paid Apps Earn?')

box.update_layout(xaxis_title='Category',
                  yaxis_title='Paid App Ballpark Revenue',
                  xaxis={'categoryorder': 'min ascending'},
                  yaxis=dict(type='log'))

box.show()

#app pricing by category boxplot
box = px.box(df_paid_apps,
             x='Category',
             y="Price",
             title='Price per Category')

box.update_layout(xaxis_title='Category',
                  yaxis_title='Paid App Price',
                  xaxis={'categoryorder': 'max descending'},
                  yaxis=dict(type='log'))

box.show()