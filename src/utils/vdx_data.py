from utils.api_requests import APIClient
from utils.config import VDX_API_URL, VDX_API_KEY
import pandas as pd
import streamlit as st
import re

api_client = APIClient(base_url=VDX_API_URL, api_key=VDX_API_KEY, use_bearer=True)


def get_vdx_data():
    try:
        query_params = {
            'start_time__gte': '2024-01-01T00:00:00Z',
        }
        response = api_client.make_request(method='get', params=query_params)
        if response:
            return pd.DataFrame(response)
        else:
            st.error("Failed to fetch data from the VDX API.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f'An error occurred: {e}')
        return pd.DataFrame()


def retrieve_weekday_names():
    weekday = {
        'Monday': 'Mandag',
        'Tuesday': 'Tirsdag',
        'Wednesday': 'Onsdag',
        'Thursday': 'Torsdag',
        'Friday': 'Fredag',
        'Saturday': 'Lørdag',
        'Sunday': 'Søndag'
    }
    return weekday


def extract_organizers_from_email(email):
    match = re.match(r'([^@]+)@', email)
    if match:
        name_parts = match.group(1).split('.')
        if len(name_parts) >= 2:
            return f"{name_parts[0].capitalize()} {name_parts[1].capitalize()}"
    return email


def get_quality_mapping():
    quality_mapping = {
        '0_unknown': 'Ukendt',
        '1_good': 'God',
        '2_ok': 'Ok'
    }
    return quality_mapping


def get_quality_percent(overall_quality_summary, quality):
    if quality in overall_quality_summary['overall_quality'].values:
        return overall_quality_summary.loc[overall_quality_summary['overall_quality'] == quality, 'overall_quality_percent'].values[0]
    else:
        return 0.0
