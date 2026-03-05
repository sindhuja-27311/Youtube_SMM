import os
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.youtube_service import YouTubeService

class YoutubeConnectView(APIView):
    def get(self, request):
        service = YouTubeService()
        auth_url, state, code_verifier = service.get_auth_url()
        request.session['oauth_state'] = state
        request.session['code_verifier'] = code_verifier
        return redirect(auth_url)

class YoutubeCallbackView(APIView):
    def get(self, request):
        error = request.GET.get('error')
        if error:
            return Response({"error": f"OAuth error: {error}"}, status=status.HTTP_400_BAD_REQUEST)
            
        code = request.GET.get('code')
        if not code:
            return Response({"error": "No code provided in the callback"}, status=status.HTTP_400_BAD_REQUEST)
        
        state = request.GET.get('state')
        session_state = request.session.get('oauth_state')
        code_verifier = request.session.get('code_verifier')

        if session_state and state != session_state:
            return Response({"error": "State mismatch. Potential CSRF attack."}, status=status.HTTP_400_BAD_REQUEST)

        service = YouTubeService()
        try:
            token_data = service.fetch_token(code, code_verifier)
            return Response({
                "message": "Authentication successful. YouTube tokens have been securely stored.",
                "access_token": token_data.get("token"),
                "refresh_token": token_data.get("refresh_token")
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class YoutubeTestUploadView(APIView):
    def post(self, request):
        video_path = os.path.join(settings.BASE_DIR, 'test_video.mp4')
        if not os.path.exists(video_path):
            return Response(
                {"error": f"test_video.mp4 not found at {video_path}. Please place a test video in the project root."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = YouTubeService()
        try:
            video_id = service.upload_video(video_path)
            return Response({
                "message": "Video uploaded successfully!",
                "video_id": video_id,
                "youtube_url": f"https://youtu.be/{video_id}"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            return Response({"error": str(e), "repr": repr(e), "traceback": trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class YoutubeChannelView(APIView):
    def get(self, request):
        service = YouTubeService()
        try:
            channel_data = service.get_channel_details()
            if not channel_data:
                return Response({"error": "No YouTube channel found for this account."}, status=status.HTTP_404_NOT_FOUND)
            return Response(channel_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class YoutubeVideosView(APIView):
    def get(self, request):
        limit = request.GET.get('limit', 50)
        service = YouTubeService()
        try:
            videos = service.get_videos(limit=int(limit))
            return Response({"videos": videos}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class YoutubeVideoDetailView(APIView):
    def put(self, request, video_id):
        # Allow partial updates with PUT or PATCH logic here
        title = request.data.get('title')
        description = request.data.get('description')
        privacy_status = request.data.get('privacy_status')
        category_id = request.data.get('category_id')
        
        service = YouTubeService()
        try:
            updated_video = service.update_video(
                video_id=video_id,
                title=title,
                description=description,
                privacy_status=privacy_status,
                category_id=category_id
            )
            return Response({"message": "Video updated successfully", "video": updated_video}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    def delete(self, request, video_id):
        service = YouTubeService()
        try:
            service.delete_video(video_id=video_id)
            return Response({"message": "Video deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
