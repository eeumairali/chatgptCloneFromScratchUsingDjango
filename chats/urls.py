from django.urls import path
from .views import chat_home, new_chat_view, open_chat_view

urlpatterns = [
    path("", chat_home, name="chat"),
    path("new/", new_chat_view, name="chat_new"),
    path("c/<str:cid>/", open_chat_view, name="chat_open"),
]