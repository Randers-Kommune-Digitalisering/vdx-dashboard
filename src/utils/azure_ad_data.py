from utils.api_requests import APIClient
import streamlit as st
from utils.config import API_SERVICE_URL


@st.cache_data
def get_user_department():
    try:
        client = APIClient(base_url=API_SERVICE_URL)
        response = client.make_request(path="api/azure/user-department", method="get")
        return response.get("user_department", [])
    except Exception as e:
        st.error(f"Kunne ikke hente Azure AD data: {e}")
        return []
