from django.contrib import admin
from django.urls import path

from apps.identity.views import home, case_demo, demo_form

urlpatterns = [
    path('', home, name='home'),
    path('cases/<int:case_id>/', case_demo, name='case_demo'),
    path('demo-form/', demo_form, name='demo_form'),
    path('admin/', admin.site.urls),
]
