import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os

def load_yaml():
    # Load credentials
    with open("./cred.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    return config

def save_yaml(config):
    # Update the YAML file
    with open('./cred.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def load_authenticator(config):
    authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'])

    return authenticator
