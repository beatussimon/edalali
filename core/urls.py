from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('listings/', views.listing_list, name='listing_list'),
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('create-listing/', views.create_listing, name='create_listing'),
    path('book/<int:pk>/', views.book_listing, name='book_listing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('set-availability/<int:pk>/', views.set_availability, name='set_availability'),
    path('pay/<int:pk>/', views.pay_booking, name='pay_booking'),
    path('review/<int:pk>/', views.leave_review, name='leave_review'),
    path('message/<int:pk>/', views.send_message, name='send_message'),
    path('messages/', views.messages, name='messages'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='core/logout.html'), name='logout'),
    path('signup/', views.signup, name='signup'),
]