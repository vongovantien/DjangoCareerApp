import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from careerapp.admin import admin_site

admin.site.site_header = "HỆ THỐNG QUẢN LÍ TRANG TUYỂN DỤNG"
admin.site.site_title = "Admin"
admin.site.index_title = "CareerApp"

urlpatterns = [
    path('admin/', admin_site.urls),
    # path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('careerapp.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

]
