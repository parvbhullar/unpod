# unpod/channels/urls.py
from django.urls import path
from .views import GoogleAppConnector, AppsView, OutlookAppConnector, AppConfigLinkView
from .views import GoogleAppConnector, AppsView, OutlookAppConnector, AppConfigLinkView, TwitterAuthConnector

app_name = "channels"

urlpatterns = [
    path('google-auth/', GoogleAppConnector.as_view({'post': 'google_auth'}), name='google_auth_login'),
    path('google-auth-callback/', GoogleAppConnector.as_view({'get': 'google_auth_callback'}), name='google_auth_callback'),
    path('apps/', AppsView.as_view({'get': 'list_apps'}), name='list_apps'),

    # link Config Views
    path('app-link/update-link-config/<int:app_link_id>/', AppConfigLinkView.as_view({'post': 'update_link_config'}), name='update_link_config'),
    path('app-link/get-link-config/<int:app_link_id>/', AppConfigLinkView.as_view({'get': 'retrieve'}), name='get_link_config'),

    # path("config/<int:app_config_id>/", GoogleAppConnector.as_view(), name="get_app_config"),

    path('outlook-auth/', OutlookAppConnector.as_view({'post': 'outlook_auth'}), name='outlook_auth_login'),
    path('outlook-auth-callback/', OutlookAppConnector.as_view({'get': 'outlook_auth_callback'}), name='outlook_auth_callback'),


    # Twitter OAuth endpoints
    path('twitter/login/', TwitterAuthConnector.as_view({'post': 'twitter_auth'}), name='twitter_auth_login'),
    path('twitter/callback/', TwitterAuthConnector.as_view({'get': 'twitter_callback'}), name='twitter_callback'),
]


