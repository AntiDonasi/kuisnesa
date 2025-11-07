import os
import httpx
from itsdangerous import URLSafeSerializer
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

serializer = URLSafeSerializer(os.getenv("SECRET_KEY", "supersecret"))

def get_login_url(state: str):
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&state={state}"
        f"&hd=unesa.ac.id"
    )

async def get_user_info(code: str):
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        access_token = token_res.json().get("access_token")
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return userinfo_res.json()
