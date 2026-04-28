import streamlit as st

def get_twilio_credentials():
    return {
        "account_sid": st.secrets["TWILIO_ACCOUNT_SID"],
        "auth_token": st.secrets["TWILIO_AUTH_TOKEN"]
    }