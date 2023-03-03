# Python standard libraries
import json
import os

# Third-party libraries
from flask import Flask, redirect, request, url_for, render_template
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from oauthlib.oauth2 import WebApplicationClient
import requests

import datetime

from looker_api import looker_create_oauth_application_user_state as looker_coaus, looker_create_sso_url as looker_create_sso_url

# this is needed as normally oauth2 would require https, and we are using http
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# You need to set up an OAuth2 Client/App in GCP console
# https://cloud.google.com/looker/docs/db-config-google-bigquery#authentication_with_oauth
with open('google_creds.json', 'r') as f:
    google_creds = json.load(f)
GOOGLE_CLIENT_ID = google_creds["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = google_creds["GOOGLE_CLIENT_SECRET"]

# Looker OAuth Application ID
# Take oauth_application_id from running print(sdk.all_external_oauth_applications())
# after Connecting Looker to BigQuery.
LOOKER_OAUTH_APPLICATION_ID = 2
LOOKER_DASHBOARD_ID = '2'

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# User Class
class User(UserMixin):
    pass

# Flask-Login helper
@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

@app.route("/")
@app.route("/index")
def index():
    dashboard_url=f"{os.environ['LOOKERSDK_BASE_URL']}/dashboards/{LOOKER_DASHBOARD_ID}"
    try:
        user_id = current_user.id
    except:
        user_id = "anon"
    url = looker_create_sso_url(user_id, dashboard_url).url
    # print(url)
    return render_template('index.html', current_user=current_user, url=url)

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    # print(authorization_endpoint)

    # Use library to construct the request for Google login and provide scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/bigquery.readonly"],
    )
    # print(request_uri)
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for things on behalf of a user
    google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    response = client.parse_request_body_response(json.dumps(token_response.json()))
    print("-----")
    print("Response:")
    for k, v in response.items():
        print(k, v)
    print("-----")
    id_token = response['id_token']
    access_token = response['access_token']
    expires_at = int(response['expires_at'])
    expires_at_datetime = datetime.datetime.fromtimestamp(expires_at)

    # Now that you have tokens (yay) let's find and hit the URL from Google that gives you the user's profile information, including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified. The user authenticated with Google, authorized your app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        # users_name = userinfo_response.json()["given_name"]
        user = User()
        user.id = users_email
        # print(user)
        login_user(user)
    else:
        return "User email not available or not verified by Google.", 400

    looker_coaus(
        user_id=current_user.id,
        oauth_application_id=LOOKER_OAUTH_APPLICATION_ID,
        access_token=access_token,
        access_token_expires_at=expires_at_datetime
        )

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()