# looker_oauth_embed
A demo to Embed Looker in an web application where Looker is connected to BigQuery via OAuth and the Authenication to the Application is also OAuth.

### The Goal
To have a web application that a user logs into via OAuth2. The OAuth2 client handles the connection to BigQuery from Looker and it handles the login to the web application.
The goal is to enable the user to access the application via OAuth2 and not have to login via OAuth2 again when presented with a dashboard.

## What's happening?
We essentially need to let our app:
- Embed a Dashboard
- Handle an OAuth2 Google login
- Parse the tokens to the Looker Embed User, which is the same as the Application User

---
## Steps
Firstly, Looker will need to have a BigQuery connection set up in the Admin Panel via OAuth. This will involve setting up an OAuth Consent Screen and then a set of Credentials. Note: These credentials (CLIENT_ID, CLIENT_SECRET) will be used for both Authenticating Looker to BigQuery and your Application to Looker.

#### Step 1
* Fork this repo.
* pip install the requirements.txt file in a Virtual Environment.

#### Step 2
* Connect Looker to BigQuery, use [this documentation](https://cloud.google.com/looker/docs/db-config-google-bigquery#authentication_with_oauth).
* Take note of the CLIENT_ID and CLIENT_SECRET and store them in a file called google_creds.json (.gitignore)
```
{
    "GOOGLE_CLIENT_ID": "YOUR_GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET": "YOUR_GOOGLE_CLIENT_SECRET"
}
```
* Check this has been registered as an external_oauth_application using `sdk.all_external_oauth_applications()`. Take note of the ID and change line 36 `LOOKER_OAUTH_APPLICATION_ID` in `main.py`.
* In your [Credential Settings](https://console.cloud.google.com/apis/credentials) for Looker App, add another Authorized JavaScript origins `http://127.0.0.1:5000` and add another Authorized redirect URIs `http://127.0.0.1:5000/login/callback`.

#### Step 3
* Create a model in Looker and use this connection. The model in my set up is called `looker_oauth_embed`.
* Create a Dashboard built off an Explore using your OAuth Connection. (My dashboard has `ID=2`).

#### Step 4
* Change line 37 in main.py to your LOOKER_DASHBOARD_ID. `LOOKER_DASHBOARD_ID='2'`
* As it stands. We only have one html page in our Application `index.html`. This page handles the login, logout of the User and also displays the dashboard.
Note that you will most likely have Dashboards on different pages; when an iFrame with a Signed URL for a Looker dashboard is loaded, the User is created as an Embed Looker User in Looker. So, when you first open this application, there will be an iframe that explains the User cannot see the information (before they have logged into the App.) This doesn't error due to the "handler" in `main.py` 
```
try:
    user_id = current_user.id
except:
    user_id = "anon"
```
So technically, everytime someone opens the app and is not logged in, they are viewing the <em>non-loaded</em> dashboard as the Looker Embed User with `user_id="anon"`.

#### Step 5
We need to handle the <em>state</em> of the User in the Application. This is done via `Flask-Login`. When a User logs in via the `/login` route, they are then logged in until they hit the `/logout` route. When they login, this triggers the OAuth login to Google as well. Then we recieve an access_token and parse this to Looker via the Looker API.
* Create API credentials for an Admin Looker User. Can use [this documentation](https://cloud.google.com/looker/docs/api-auth#authentication_with_an_sdk).
* Store these in a file called `looker_api_credentials.json`
```
{
    "LOOKERSDK_BASE_URL": "https://YOUR_DOMAIN.cloud.looker.com",
    "LOOKERSDK_CLIENT_ID": "LOOKERSDK_CLIENT_ID",
    "LOOKERSDK_CLIENT_SECRET": "LOOKERSDK_CLIENT_SECRET"
}
```
This means that when the User logs into your application, the application can parse the tokens that are received to Looker via Looker's API SDK.

#### Step 6
* run `$ export FLASK_APP=main.py`
* run `$ flask run`
* Test it works!