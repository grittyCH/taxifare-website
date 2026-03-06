import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

from datetime import datetime
from pathlib import Path

LOGO_PATH = Path(__file__).parent / "assets" / "Logo_Red&Black.png"
st.set_page_config(page_title="Le Wagon Taxi", page_icon=str(LOGO_PATH), layout="centered")
st.image(LOGO_PATH)

'''
## lets you know upfront how much your ride should cost approximately
##### actuals costs may vary depending on actual traffic conditions during the ride
'''

st.subheader('your planned ride')

date = st.date_input('date of the ride (YY-MM-DDDD) :')
time = st.time_input('time of day (hh:mm) :')
pickup_datetime = datetime.combine(date, time)

def geocode_ny_address(address: str):
    if not address.strip():
        return None

    url = "https://photon.komoot.io/api/"
    params = {
        "q": f"{address}, New York, USA",
        "limit": 1,
        "lat": 40.7128,
        "lon": -74.0060}
    headers = {'User-Agent': 'taxifare-app/1.0'}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        features = r.json().get("features", [])
    except requests.RequestException:
        return None

    if not features:
        return None

    lon, lat = features[0]["geometry"]["coordinates"]
    return float(lon), float(lat)


def zoom_from_points(lat1, lon1, lat2, lon2):
    spread = max(abs(lat1 - lat2), abs(lon1 - lon2))
    if spread < 0.003:
        return 15
    if spread < 0.007:
        return 14
    if spread < 0.015:
        return 13
    if spread < 0.03:
        return 12
    return 11


with st.form("fare_form"):
    pu_address = st.text_input('NYC street address at which we should pick you up :')
    do_address = st.text_input('NYC street address at which we should drop you off :')
    pax_nbr = st.number_input('number of passengers :', min_value=1, max_value=8, step=1)
    submitted = st.form_submit_button('Estimate fare')

if submitted:
    if not pu_address.strip() or not do_address.strip():
        st.warning('Please enter both pickup and dropoff addresses.')
        st.stop()

    pickup_coords = geocode_ny_address(pu_address)
    dropoff_coords = geocode_ny_address(do_address)

    if pickup_coords is None:
        st.warning('Pickup address not found. Try a more precise NYC address.')
        st.stop()

    if dropoff_coords is None:
        st.warning('Dropoff address not found. Try a more precise NYC address.')
        st.stop()

    pickup_longitude, pickup_latitude = pickup_coords
    dropoff_longitude, dropoff_latitude = dropoff_coords

    ride_df = pd.DataFrame([
        {"label": "Pickup", "lat": pickup_latitude, "lon": pickup_longitude, "color": [230, 57, 70]},
        {"label": "Dropoff", "lat": dropoff_latitude, "lon": dropoff_longitude, "color": [29, 185, 84]} ])

    url = 'https://taxifare.lewagon.ai/predict'
    params = {
        'pickup_datetime': pickup_datetime.isoformat(),
        'pickup_longitude': pickup_longitude,
        'pickup_latitude': pickup_latitude,
        'dropoff_longitude': dropoff_longitude,
        'dropoff_latitude': dropoff_latitude,
        'passenger_count': int(pax_nbr)}
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(url=url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()
        fare = result.get('fare')
        st.success(f'Estimated fare: ${fare:.2f}')
    except requests.RequestException:
        st.error('Could not estimate fare right now. Please try again.')

    center_lat = (pickup_latitude + dropoff_latitude) / 2
    center_lon = (pickup_longitude + dropoff_longitude) / 2
    zoom = zoom_from_points(
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,)

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=ride_df,
            get_position='[lon, lat]',
            get_fill_color='color',
            get_radius=90,
            radius_min_pixels=7),
        pdk.Layer(
            "TextLayer",
            data=ride_df,
            get_position='[lon, lat]',
            get_text='label',
            get_color='[20, 20, 20]',
            get_size=16,
            get_alignment_baseline="'top'",)]

    st.pydeck_chart(
        pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=zoom,
                pitch=0),
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            tooltip={"text": "{label}"}))

    st.balloons()
