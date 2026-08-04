from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.telemetry.urls')),
    path('api/', include('apps.faults.urls')),
    path('api/', include('apps.simulator.urls')),
    path('api/', include('apps.ai_assistant.urls')),
]
