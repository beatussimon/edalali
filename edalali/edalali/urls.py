from django.contrib import admin
from django.urls import path, include  # Import include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include core app URLs
   # path('listings/', include('listings.urls')), #Add other apps later
   # path('bookings/', include('bookings.urls')),
    #path('reviews/', include('reviews.urls')),
    #path('messaging/', include('messaging.urls')),
    #path('payments/', include('payments.urls')),
]
# Add this block to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)