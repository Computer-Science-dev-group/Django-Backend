from django.urls import path

from uia_backend.messaging.api.v1.views import (
    CommentListAPIView,
    FileUploadAPIView,
    PostDetailsAPIView,
    PostListAPIView,
    RepliesListAPIView,
)

urlpatterns = [
    path(
        "<uuid:cluster_id>/posts/",
        PostListAPIView.as_view(),
        name="cluster_post_list",
    ),
    path(
        "<uuid:cluster_id>/posts/<uuid:post_id>/",
        PostDetailsAPIView.as_view(),
        name="cluster_post_details",
    ),
    path(
        "<uuid:cluster_id>/posts/<uuid:post_id>/comments/",
        CommentListAPIView.as_view(),
        name="post_list_comments",
    ),
    path(
        "<uuid:cluster_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/",
        RepliesListAPIView.as_view(),
        name="comment_reply_list",
    ),
    path(
        "uploads/",
        FileUploadAPIView.as_view(),
        name="file_upload",
    ),
]
