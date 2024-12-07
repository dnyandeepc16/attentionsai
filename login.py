import streamlit as st
import yaml
from app import MainApp

st.set_page_config(layout="wide")

# Function to load credentials from the YAML file
def load_credentials():
    with open("D:/Attentions AI/codebase/cred.yaml", "r") as file:
        credentials = yaml.safe_load(file)
    return credentials

# Function to authenticate user
def authenticate(username, password):
    credentials = load_credentials()
    if username == credentials['username'] and password == credentials['password']:
        return True
    return False

# Streamlit app code
def login_page():
    # Check if the user is already logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.title("Login Page")
        
        # Get user input for username and password
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Check if user has submitted the form
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state['logged_in'] = True  # Set session state to logged in
                st.success("Login successful!")
                MainApp.run()  # Call MainApp function from app.py
            else:
                st.error("Invalid credentials. Please try again.")
    else:
        # If logged in, run MainApp directly
        MainApp.run()

if __name__ == "__main__":
    login_page()
