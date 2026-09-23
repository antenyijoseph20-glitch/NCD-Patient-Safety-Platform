from django.contrib import admin
from django.urls import path

from apps.identity.views import home, case_demo

urlpatterns = [
    path('', home, name='home'),
    path('cases/<int:case_id>/', case_demo, name='case_demo'),
    path('admin/', admin.site.urls),
]
