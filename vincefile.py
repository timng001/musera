import csv
import pandas as pd
import datetime as dt
from tabulate import tabulate

pd.set_option('display.expand_frame_repr', False)


# reading csv file
data = pd.read_csv("Hot Stuff.csv")
color = pd.read_excel("Hot 100 Audio Features.xlsx")

# trim color data
valence = color[["Performer", "Song", "valence"]]

# switch dates from str to date objects
datetimes = pd.to_datetime(data["WeekID"])
data["WeekID"] = datetimes

# sort dates
data = data.sort_values(by="WeekID")

# adding valence col to main song data
result = pd.merge(data,
                 color[['SongID', 'Performer', 'valence']],
                 on=['SongID', 'Performer'],
                 how='left')

# print the organized data frame
result.to_csv('Top Songs Database.csv')

# create randomly sampled subset
mini = result.sample(10)
print(mini)

# trimmed song and artist columns
def songinfo(df, y):

    for x in len(df.index):
        if x == y:
            basic = df.loc[[x]]
            return basic[["Song", "Performer"]]

