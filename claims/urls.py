from django.urls import path
from claims import views  # import your views.py file
from django.contrib.auth import views as auth_views #used for log in/out

urlpatterns = [
    path("", views.home, name="home"),                                                                      # "" means this URL pattern matches the root of wherever this app is mounted -also used as table partial path-
    path("claim/<int:pk>/details/", views.claim_detail, name="claim_detail_partial"),                       #called by the view button for claim detail dashboard
    path('claim/<int:pk>/add-note/', views.add_note, name='add_note'),                                      #called by add note button to request POST method (adds to Note DB)
    path("claim/<int:pk>/notes/", views.claim_notes_partial, name="claim_notes_partial"),                   #called when view is pressed to show claim notes for claim 
    path("claim/<int:pk>/add-flag/", views.add_flag, name="add_flag"),                                      #called when add flag button is pressed for POST
    path("claim/<int:pk>/flags/", views.flag_partial, name="flag_partial"),                                 #called when view button is pressed to render flag panel
    path('claim/<int:pk>/actions/', views.quick_actions_partial, name='quick_actions_partial'),             #called when view is clicked for quick actions to receive claim id 
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),    #called upon loading default view due to @login_required
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),                       #called by logout button
    path("signup/", views.signup_view, name="signup"),                                                      #called by signup button in login page
]
