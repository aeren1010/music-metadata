from streamlit import rerun
from urllib.parse import quote
import streamlit as st
import requests
from config import headers, search_url, lyrics_url

st.title("Music Metadata")

if st.session_state.get("song"):
    sng = st.session_state["song"]
    artist_info = sng.get("artist-credit", [{}])
    release_info = sng.get("releases", [])
    first_release = release_info[0] if release_info else {}
    mbid = first_release.get("id")
    cover_url = f"https://coverartarchive.org/release/{mbid}/front-500"
    new_cover = None

    st.header(f"Song: {sng["Song"]}")

    for release in release_info[:10]:
        rmbid = release.get("id")
        if rmbid:
            build_cover = f"https://coverartarchive.org/release/{rmbid}/front-500"
            response = requests.get(build_cover, timeout=3)
            if response.status_code == 200:
                new_cover = build_cover
                break

    if new_cover:
        st.image(new_cover)
    else:
        st.info("No cover found")

    if st.button("Return"):
        st.session_state["song"] = None
        st.rerun()


    selected_song_data = {
        "Song Name": sng["Song"],
                    "Artist": sng["Artist"],
                    "Second Artist": sng["Full Credits"][1].get("name", "None") if len(sng["Full Credits"]) > 1 else "None",
                    "Album": sng["Album"],
                    "Release Date": sng["Release Date"],
                    "Length": sng.get("Length"),
                    "ISRC": sng.get("ISRC"),
                    "Country": sng.get("Country"),
                    "Label": sng.get("Label"),
                    "Genres": sng.get("Genres"),
                    "Status": sng.get("Status"),
    }

    st.table(selected_song_data, border="horizontal")

    l_artist = sng["Artist"]
    l_song = sng["Song"]

    lyrics = f"https://api.lyrics.ovh/v1/{l_artist}/{l_song}"
    show_lyrics = requests.get(lyrics)
    raw_lyrics = show_lyrics.json()
    formatted_lyrics = raw_lyrics.get("lyrics", "No lyrics")

    song_query = f"{sng['Artist']} {sng['Song']}".replace(" ", "%20")
    spotify_link = f"https://open.spotify.com/search/{song_query}"
    youtube_link = f"https://www.youtube.com/results?search_query={song_query}"
    apple_link = f"https://music.apple.com/search?term={song_query}"

    st.subheader(f"Stream {sng["Song"]} on...")
    plat1, plat2, plat3 = st.columns(3)
    plat1.link_button("Spotify", spotify_link, use_container_width=True)
    plat2.link_button("YouTube", youtube_link, use_container_width=True)
    plat3.link_button("Apple Music", apple_link, use_container_width=True)

    if show_lyrics.status_code == 200:
        st.subheader("Lyrics")
        st.text(formatted_lyrics)

else:
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
                release_info = i.get("releases", [])
                release_count = len(release_info)

                first_release = release_info[0] if release_info else {}

                ms = i.get("length", 0)
                duration = f"{int(ms // 60000)}:{int((ms % 60000) // 1000):02d}" if ms else "No data"

                tags = i.get("tags", [])
                tags_str = ", ".join([tag.get("name") for tag in tags])

                country = first_release.get("country", "Unknown")
                if country == "XW":
                    country = "Worldwide"

                song_data = {
                    "Song": i.get("title", "Unknown"),
                    "Artist": artist_info[0].get("name", "Unknown Artist"),
                    "Album": first_release.get("title", "Single"),
                    "Release Date": first_release.get("date", "No date"),
                    "Full Credits": artist_info,
                    "Internal Popularity": release_count,
                    "Score": int(i.get("score", 0)),
                    "Length": duration,
                    "ISRC": i.get("isrcs", ["N/A"])[0],
                    "Country": country,
                    "Label": first_release.get("label-info", [{}])[0].get("label", {}).get("name", "Indie/Unknown"),
                    "Genres": tags_str,
                    "Release-ID": first_release.get("id"),
                    "Status": first_release.get("status", "Official")
                }

                songs.append(song_data)

            songs.sort(key=lambda x: (x["Internal Popularity"], x["Score"]), reverse=True)

            visualtable = []
            for x in songs:
                visualtable.append({
                    "Song": x["Song"],
                    "Artist": x["Artist"],
                    "Album": x["Album"],
                })
            stable = st.dataframe(visualtable[:25], on_select="rerun", selection_mode="single-row")
            
            if stable.selection.rows:
                selected_song = stable.selection.rows[0]
                st.session_state["song"] = songs[selected_song]
                st.rerun()

        else:
            st.info("No Entries.")