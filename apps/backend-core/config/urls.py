from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.authtoken.views import obtain_auth_token
from django.views.static import serve

from unpod.users.admin_view.views import AdminLogin

# fmt:off
favicon_view = RedirectView.as_view(url='static/favicon.ico', permanent=True)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),

    path(f"{settings.ADMIN_URL}login/", AdminLogin.as_view(), name='admin-login'),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include("unpod.apiV1.urls"), name="allow-all"),
    path("api/v2/platform/", include("unpod.apiV2Platform.urls"), name="api-v2-platform"),
    path("api/v1/accounts/", include("allauth.urls")),
    re_path(r'^favicon\.ico$', favicon_view)

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})]

urlpatterns += [
# DRF auth token
    path("auth-token/", obtain_auth_token),
    # OpenAPI 3 Schema endpoints for API V2 Platform
    path("api/v2/platform/schema/", SpectacularAPIView.as_view(), name="api-v2-schema"),
    path("api/v2/platform/docs/", SpectacularSwaggerView.as_view(url_name="api-v2-schema"), name="api-v2-docs"),
    path("api/v2/platform/redoc/", SpectacularRedocView.as_view(url_name="api-v2-schema"), name="api-v2-redoc"),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS and getattr(settings, 'ENABLE_DEBUG_TOOLBAR', False):
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
