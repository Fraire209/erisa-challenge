from django.urls import path
from claims import views  # import your views.py file

urlpatterns = [
    path("", views.home, name="home"),                                                      # "" means this URL pattern matches the root of wherever this app is mounted
    path("claim/<int:pk>/details/", views.claim_detail, name="claim_detail_partial"),       #called by the view button for claim detail dashboard
    path('claim/<int:pk>/add-note/', views.add_note, name='add_note'),                      #called by add note button to request POST method (adds to Note DB)
    path("claim/<int:pk>/notes/", views.claim_notes_partial, name="claim_notes_partial"),   #called when a new claim is in view to show related notes and flags
]
