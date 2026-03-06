import streamlit as st
import requests

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

LOGO_PATH = Path(__file__).parent / "assets" / "Logo_Red&Black.png"
st.image(LOGO_PATH)
st.set_page_config(page_title="Le Wagon Taxi", page_icon=str(LOGO_PATH), layout="centered")

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

    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': f'{address}, New York, USA',
        'format': 'json',
        'limit': 1,
        'countrycodes': 'us'
    }
    headers = {'User-Agent': 'taxifare-app/1.0'}

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    results = r.json()

    if not results:
        return None

    lat = float(results[0]['lat'])
    lon = float(results[0]['lon'])
    return lon, lat


pu_address = st.text_input('street address at which we should pick you up :')
pickup_longitude, pickup_latitude = geocode_ny_address(pu_address)

do_address = st.text_input('street address at which we should drop you off :')
dropoff_longitude, dropoff_latitude = geocode_ny_address(do_address)

pax_nbr = st.number_input('number of passengers :', min_value=1, max_value=8, step=1)

url = 'https://taxifare.lewagon.ai/predict'
params = {'pickup_datetime': pickup_datetime,
        'pickup_longitude': pickup_longitude, 'pickup_latitude': pickup_latitude,
        'dropoff_longitude': dropoff_longitude, 'dropoff_latitude': dropoff_latitude,
        'passenger_count': int(pax_nbr) }
headers = {'Accept': 'application/json'}

response = requests.get(url=url, params=params, headers=headers, timeout=15)
result = response.json()
fare = result.get('fare')
st.success(f'Estimated fare: ${fare:.2f}')
