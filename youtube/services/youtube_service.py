import os
import json
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeService:
    TOKEN_FILE = os.path.join(settings.BASE_DIR, 'youtube_token.json')
    
    def __init__(self):
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "project_id": "youtube-backend",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [self.redirect_uri]
            }
        }

    def get_auth_url(self):
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.YOUTUBE_SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state, getattr(flow, 'code_verifier', None)

    def fetch_token(self, code, code_verifier=None):
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.YOUTUBE_SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        if code_verifier:
            flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        with open(self.TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
            
        return token_data

    def get_credentials(self):
        if not os.path.exists(self.TOKEN_FILE):
            return None
        with open(self.TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
            
        return Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )

    def upload_video(self, file_path, title="Test Video", description="Test Description", category_id="22", privacy_status="private"):
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("No credentials found. Please authenticate first by calling the connect endpoint.")

        youtube = build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["test", "api"],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = request.execute()
        return response.get("id")

    def get_channel_details(self):
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("No credentials found. Please authenticate first by calling the connect endpoint.")
        
        youtube = build("youtube", "v3", credentials=credentials)
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if not response.get('items'):
            return None
        return response['items'][0]

    def get_videos(self, limit=50):
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("No credentials found.")
            
        youtube = build("youtube", "v3", credentials=credentials)
        
        # First, ensure we get the user's channel to find their uploads playlist
        channel = self.get_channel_details()
        if not channel:
            return []
            
        uploads_playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
        
        request = youtube.playlistItems().list(
            part="snippet,contentDetails,status",
            playlistId=uploads_playlist_id,
            maxResults=limit
        )
        response = request.execute()
        
        videos = []
        for item in response.get('items', []):
            videos.append({
                'id': item['contentDetails']['videoId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'publishedAt': item['snippet']['publishedAt'],
                'thumbnails': item['snippet']['thumbnails'],
                'status': item['status']['privacyStatus']
            })
            
        return videos

    def update_video(self, video_id, title=None, description=None, category_id=None, privacy_status=None):
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("No credentials found.")
            
        youtube = build("youtube", "v3", credentials=credentials)
        
        # First get existing video details, since update requires the full snippet
        video_request = youtube.videos().list(
            part="snippet,status",
            id=video_id
        )
        video_response = video_request.execute()
        
        if not video_response.get('items'):
            raise Exception(f"Video {video_id} not found.")
            
        video = video_response['items'][0]
        
        if title:
            video['snippet']['title'] = title
        if description is not None:
            video['snippet']['description'] = description
        if category_id:
            video['snippet']['categoryId'] = category_id
        if privacy_status:
            video['status']['privacyStatus'] = privacy_status
            
        update_request = youtube.videos().update(
            part="snippet,status",
            body={
                "id": video_id,
                "snippet": video['snippet'],
                "status": video['status']
            }
        )
        update_response = update_request.execute()
        return update_response

    def delete_video(self, video_id):
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("No credentials found.")
            
        youtube = build("youtube", "v3", credentials=credentials)
        
        request = youtube.videos().delete(
            id=video_id
        )
        request.execute()
        return True
