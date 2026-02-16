from django.urls import path

from unpod.knowledge_base import views as knowledge_base_views

# fmt:off
urlpatterns = [
    path("<str:token>/", knowledge_base_views.DataView.as_view(), name="data_upload"),
    path(
        "<str:token>/list/",
        knowledge_base_views.DataListView.as_view(),
        name="data_list",
    ),
    path(
        "<str:token>/index/",
        knowledge_base_views.DataIndexView.as_view({"get": "index"}),
        name="data-index",
    ),
    path(
        "<str:token>/collection-data/",
        knowledge_base_views.StoreServiceView.as_view({"get": "get_collection_data"}),
        name="collection_data",
    ),
    path(
        "<str:token>/upload-status/",
        knowledge_base_views.StoreServiceView.as_view({"get": "upload_status"}),
        name="data-index-upload-status",
    ),
    path("<str:token>/connector-data/", knowledge_base_views.StoreServiceView.as_view({"get": "get_connector_data"}), name="connector_data"),
    path("<str:token>/connector-doc-data/", knowledge_base_views.StoreServiceView.as_view({"post": "create_doc_data"}), name="create_doc_data"),
    path("<str:token>/connector-doc-data/<str:document_id>/", knowledge_base_views.StoreServiceView.as_view({
        "get": "get_doc_data",
        "put": "update_doc_data",
        "delete": "delete_doc_data"
    }), name="doc_data"),
    path(
        "<str:token>/connector-doc-data/<str:document_id>/tasks/",
        knowledge_base_views.StoreServiceView.as_view({"get": "get_document_tasks"}),
        name="get_document_tasks"
    ),
]
