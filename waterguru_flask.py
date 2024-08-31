#!/usr/local/bin/python
import logging
import os
import traceback

import boto3
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, Response, jsonify
from redis import Redis
from requests_aws4auth import AWS4Auth
from warrant import Cognito
from warrant.aws_srp import AWSSRP

# Original REPO
# 8/2021 - https://github.com/bdwilson/waterguru-api
# 3/1/24 - https://github.com/pysanders/waterguru-api - some minor adjustments to support Unraid
# and caching tokens


# App config.
DEBUG = os.environ.get('DEBUG', False)
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

r = Redis(host=os.environ.get('REDIS', '192.168.1.3'),
          db=int(os.environ.get('REDIS_DB', 0)),
          decode_responses=True)

config = {
    "port": 53255,  # port for your service to run on
    "user": os.environ['WG_USER'],
    "pass": os.environ['WG_PASS']
}

app.logger.info(f"Running with user: {config['user']}")


def wg_auth():
    wg_userId = r.get('wg_userId')
    wg_access_key_id = r.get('wg_access_key_id')
    wg_secret_key = r.get('wg_secret_key')
    wg_session_token = r.get('wg_session_token')

    if not wg_userId or not wg_access_key_id or not wg_secret_key or not wg_session_token:
        app.logger.info("Getting Auth as not in Redis")
        region_name = "us-west-2"
        pool_id = "us-west-2_icsnuWQWw"
        identity_pool_id = "us-west-2:691e3287-5776-40f2-a502-759de65a8f1c"
        client_id = "7pk5du7fitqb419oabb3r92lni"
        idp_pool = "cognito-idp.us-west-2.amazonaws.com/" + pool_id

        boto3.setup_default_session(region_name=region_name)
        client = boto3.client('cognito-idp', region_name=region_name)
        # REFRESH_TOKEN_AUTH flow doesn't exist yet in warrant lib https://github.com/capless/warrant/issues/33
        # would love it if someone could figure out proper refresh.
        aws = AWSSRP(username=config['user'], password=config['pass'], pool_id=pool_id, client_id=client_id,
                     client=client)
        tokens = aws.authenticate_user()

        id_token = tokens['AuthenticationResult']['IdToken']
        refresh_token = tokens['AuthenticationResult']['RefreshToken']
        access_token = tokens['AuthenticationResult']['AccessToken']
        token_type = tokens['AuthenticationResult']['TokenType']

        u = Cognito(pool_id, client_id, id_token=id_token, refresh_token=refresh_token, access_token=access_token)
        user = u.get_user()
        user_id = user._metadata['username']

        boto3.setup_default_session(region_name=region_name)
        identity_client = boto3.client('cognito-identity', region_name=region_name)
        identity_response = identity_client.get_id(IdentityPoolId=identity_pool_id)
        identity_id = identity_response['IdentityId']

        credentials_response = identity_client.get_credentials_for_identity(IdentityId=identity_id,
                                                                            Logins={idp_pool: id_token})
        credentials = credentials_response['Credentials']
        access_key_id = credentials['AccessKeyId']
        secret_key = credentials['SecretKey']
        service = 'lambda'
        session_token = credentials['SessionToken']
        expiration = credentials['Expiration']


        # Convert expiration to a timezone-aware datetime with EST offset
        expiration = expiration.astimezone(timezone(timedelta(hours=-5)))
        current_datetime = datetime.now(timezone.utc)
        time_difference = expiration - current_datetime
        difference_in_seconds = round(time_difference.total_seconds())
        token_life = difference_in_seconds - 300

        r.setex('wg_userId', token_life, user_id)
        r.setex('wg_access_key_id', token_life, access_key_id)
        r.setex('wg_secret_key', token_life, secret_key)
        r.setex('wg_session_token', token_life, session_token)
        r.setex('wg_refresh_token', token_life, refresh_token)
        r.setex('wg_access_token', token_life, access_token)
        r.setex('wg_id_token', token_life, id_token)

        wg_userId = user_id
        wg_access_key_id = access_key_id
        wg_secret_key = secret_key
        wg_session_token = session_token

    else:
        app.logger.info("Using Cached Auth")

    return wg_userId, wg_access_key_id, wg_secret_key, wg_session_token


def get_wg():
    user_id, access_key_id, secret_key, session_token = wg_auth()

    method = 'POST'
    headers = {'User-Agent': 'aws-sdk-iOS/2.24.3 iOS/14.7.1 en_US invoker',
               'Content-Type': 'application/x-amz-json-1.0'}
    body = {"userId": user_id, "clientType": "WEB_APP", "clientVersion": "0.2.3"}
    service = 'lambda'
    url = 'https://lambda.us-west-2.amazonaws.com/2015-03-31/functions/prod-getDashboardView/invocations'
    region = 'us-west-2'

    auth = AWS4Auth(access_key_id, secret_key, region, service, session_token=session_token)
    response = requests.request(method, url, auth=auth, json=body, headers=headers)
    return (response.text)


@app.errorhandler(Exception)
def handle_exception(err):
    """Return JSON instead of HTML for any other server error"""
    app.logger.error(f"Unknown Exception: {str(err)}")
    if DEBUG:
        traceback_str = ''.join(traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__))
    else:
        traceback_str = "Not in DEBUG"
    response = {"error": str(err), "traceback": traceback_str}
    return jsonify(response), 500


@app.route("/", methods=['GET'])
def info():
    return ("Try: /api/wg")


@app.route("/api/wg", methods=['GET'])
def api():
    val = get_wg()
    if val:
        return Response(val, mimetype='application/json')
    else:
        return Response("")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=config['port'], debug=DEBUG)
