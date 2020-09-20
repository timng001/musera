import base64
import requests
import datetime
from urllib.parse import urlencode
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv
import pandas as pd
import datetime as dt
from tabulate import tabulate

#Below is the spotify API
client_id="e78d1681d51f4d899b6bd2f8cc4a01c5"
client_secret="2499e0f0c7cb42a4a10f58a94f103824"
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id,
                                                           client_secret))
class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        """
        Returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
            # return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in']  # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')

    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')

    def base_search(self, query_params):  # type
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def search(self, query=None, operator=None, operator_query=None, search_type='artist'):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query, dict):
            query = " ".join([f"{k}:{v}" for k, v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query, "type": search_type.lower()})
        return self.base_search(query_params)

#_______________________________________________________________________
#Below: Using pandas to read in data from 1) weekly Billboard Top 100 data
#and 2) audio features of billboard hits
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
mini = result.sample(5)

# used to pull list of Song and Performer from data set
def songinfo(df):
    l1 = list(df['Song'])
    l2 = list(df['Performer'])
    return l1,l2
#______________________________________________________________________________________________________
# Below is the Search code that gathers song information using Spotify's API

def final_output(title, performer):
    spotify = SpotifyAPI(client_id, client_secret)
    mySPOT_dict = spotify.search({"track": title}, {"artist": performer}, search_type="track")
    temp_dict = mySPOT_dict['tracks']['items']

    # Below this is the uri code getter
    temp_list = []
    for inx, track in enumerate(temp_dict):
        if inx == 0:
            temp_list = list(track['uri'])
    temp_list = ''.join(temp_list)
    test = temp_list
    results = sp.track(test)
    list_track = test.split(":", 1)
    url_track = list_track[1].replace(':', '/')

    info = {
        'track': results['name'],
        'audio-link': 'https://open.spotify.com/' + url_track,
        'audio-snippet': results['preview_url'],
        'cover art': results['album']['images'][0]['url']
    }
    return info
#______________________________________________________________________
#Main
#So far prints data correctly.
x = songinfo(mini)
songs = x[0]
performers = x[1]
dead = {}
for i in range(5):
    title = songs[i]
    performer = performers[i]
    zed = dict(final_output(title,performer))
    dead.update(zed)
    print(dead)

