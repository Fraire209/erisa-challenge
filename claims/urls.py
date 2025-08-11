from django.urls import path
from claims import views  # import your views.py file

urlpatterns = [
    path("", views.home, name="home"),  # "" means this URL pattern matches the root of wherever this app is mounted
    path("claim/<int:pk>/", views.claim_detail, name="claim_detail_partial"), #called by the view button for claim detail dashboard
]
