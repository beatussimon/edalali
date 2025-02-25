from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/', include('allauth.urls')), #allauth urls
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

]