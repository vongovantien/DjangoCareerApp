from django.urls import path, re_path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from . import views
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings


router = DefaultRouter()
router.register('employers', views.EmployerViewSet, basename='employer')
router.register('posts', views.PostViewSet, basename='post')
router.register('users', views.UserViewSet, basename='user')
router.register('categories', views.CategoryList, basename="category")
router.register('candidates', views.CandidateViewSet, basename="candidate")
router.register('comments', views.CommentViewSet, basename="comment")

schema_view = get_schema_view(
    openapi.Info(
        title="CareerApp API",
        default_version='v1',
        description="APIs for CareerApp",
        contact=openapi.Contact(email="vongovantien@gmail.com"),
        license=openapi.License(name="VO NGO VAN TIEN @2021"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),

)
urlpatterns = [
    path('', include(router.urls)),
    path('oauth2-info/', views.AuthInfo.as_view()),
    path('reset-password/', views.ResetPassword.as_view()),
    path('change-password/', views.ChangePassword.as_view()),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
