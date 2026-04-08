from six.moves.urllib import response
import streamlit as st
import requests
from config import headers, search_url, lyrics_url

st.title("Music Metadata")
inpt = st.text_input(label="Search", type="default", help="Type in your favourite artist and see what results you get.", placeholder="Search for a song or an artist", icon="🔎")

@st.cache_data
def search(query_value):
    params = {
    "query": f'(primarytype:album OR primarytype:single) AND status:official AND "{query_value}"~',
    "fmt": "json",
    "limit": 100
    }

    response = requests.get(search_url + "recording/", params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None

if inpt:
    result = search(inpt.strip())
    songs = []

    if result:
        for i in result["recordings"][:100]:
            artist_info = i.get("artist-credit", [{}])
            release_info = i.get("releases", [{}])
            release_count = len(release_info)

            first_release = release_info[0] if release_info else {}

            song_data = {
                "Song": i.get("title", "Unknown"),
                "Artist": artist_info[0].get("name", "Unknown Artist"),
                "Album": first_release.get("title", "Single"),
                "Release Date": first_release.get("date", "No date"),
                "Internal Popularity": release_count,
                "Score": int(i.get("score", 0))
            }

            songs.append(song_data)

        songs.sort(key=lambda x: (x["Internal Popularity"], x["Score"]), reverse=True)

        for x in songs:
            del x["Score"]
            del x["Internal Popularity"]
        st.table(songs[:25], border="horizontal")

    else:
        st.info("No Entries.")

# lyrics = f"https://api.lyrics.ovh/v1/{artist}/{song}"
# show_lyrics = requests.get(lyrics)