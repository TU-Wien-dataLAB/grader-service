import jwt
import time
import requests
import uuid

# Constants
PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
"""
CLIENT_ID = "grader-service"  # The issuer (iss claim)
SUBJECT = "uhD99LSS6QurKAK"  # The client_id (sub claim)
TOKEN_URL = "https://tuwel.tuwien.ac.at/mod/lti/token.php"  # The token endpoint URL
AUDIENCE = [TOKEN_URL]  # The authorization server identifier (aud claim)
SCOPE = ("https://purl.imsglobal.org/spec/lti-ags/scope/lineitem "
         "https://purl.imsglobal.org/spec/lti-ags/scope/result/read")

# Generate the JWT
def create_jwt():
    current_time = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": SUBJECT,
        "aud": AUDIENCE,
        "iat": current_time,
        "exp": current_time + 300,  # Token valid for 5 minutes
        "jti": str(uuid.uuid4())  # Unique identifier for the token
    }
    # Create the JWT
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token

# Request an access token
def get_access_token():
    jwt_token = create_jwt()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token,
        "scope": SCOPE,
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

# Example usage
if __name__ == "__main__":
    try:
        token_response = get_access_token()
        print("Access Token:", token_response["access_token"])
    except requests.exceptions.RequestException as e:
        print("Error obtaining access token:", e.response.text)
