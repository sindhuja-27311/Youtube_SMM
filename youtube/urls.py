from django.urls import path
from youtube.views import (
    YoutubeConnectView, 
    YoutubeCallbackView, 
    YoutubeTestUploadView,
    YoutubeChannelView,
    YoutubeVideosView,
    YoutubeVideoDetailView
)

urlpatterns = [
    path('connect/', YoutubeConnectView.as_view(), name='youtube-connect'),
    path('oauth2callback/', YoutubeCallbackView.as_view(), name='youtube-callback'),
    path('test-upload/', YoutubeTestUploadView.as_view(), name='youtube-test-upload'),
    
    # New CRUD endpoints
    path('channel/', YoutubeChannelView.as_view(), name='youtube-channel'),
    path('videos/', YoutubeVideosView.as_view(), name='youtube-videos'),
    path('videos/<str:video_id>/', YoutubeVideoDetailView.as_view(), name='youtube-video-detail'),
]
