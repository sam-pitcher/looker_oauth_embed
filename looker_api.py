import looker_sdk
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import datetime
import json

with open('looker_api_creds.json', 'r') as f:
    looker_api_creds = json.load(f)
os.environ['LOOKERSDK_BASE_URL'] = looker_api_creds["LOOKERSDK_BASE_URL"]
os.environ['LOOKERSDK_CLIENT_ID'] = looker_api_creds["LOOKERSDK_CLIENT_ID"]
os.environ['LOOKERSDK_CLIENT_SECRET'] = looker_api_creds["LOOKERSDK_CLIENT_SECRET"]

os.environ['LOOKERSDK_VERIFY_SSL']= 'False'
os.environ['LOOKERSDK_API_VERSION']= '4.0'
os.environ["LOOKERSDK_TIMEOUT"] = "120"

sdk = looker_sdk.init40()

# print(sdk.all_external_oauth_applications())

def looker_create_sso_url(user_id, dashboard_url):
    body=looker_sdk.models40.EmbedSsoParams(
        target_url=f"{dashboard_url}",
        session_length=600,
        force_logout_login=True,
        external_user_id=user_id,
        first_name="Sam",
        last_name="iFrame",
        permissions=[
        'explore',
        'embed_browse_spaces',
        'access_data',
        'create_alerts',
        'download_without_limit',
        'schedule_look_emails',
        'see_drill_overlay',
        'see_lookml_dashboards',
        'see_looks',
        'see_user_dashboards',
        'send_to_integration',
        'save_content',
        'see_sql'
        ],
        models=["looker_oauth_embed"],
        group_ids=["1"],
        external_group_id="iFrame"
      )
    response = sdk.create_sso_embed_url(body)
    return response

def looker_create_oauth_application_user_state(user_id, oauth_application_id, access_token, access_token_expires_at):
    looker_user = sdk.user_for_credential('embed', user_id)
    print("-------")
    print(f"user_id: {user_id}")
    print(f"looker_user: {looker_user}")
    print("-------")
    looker_user_id = looker_user.id
    # print(looker_user_id)
    body = looker_sdk.models40.CreateOAuthApplicationUserStateRequest(
        user_id=looker_user_id,
        oauth_application_id=oauth_application_id,
        access_token=access_token,
        access_token_expires_at=access_token_expires_at,
        refresh_token=access_token,
        refresh_token_expires_at=access_token_expires_at
    )
    # print(body)
    a = sdk.create_oauth_application_user_state(body)
    # print(a)
    # print(dir(sdk))
    return a

