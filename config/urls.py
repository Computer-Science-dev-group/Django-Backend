from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path(
        "api/v1/accounts/",
        include(
            ("uia_backend.accounts.api.v1.urls", "accounts_api_v1"),
            namespace="accounts_api_v1",
        ),
    ),
    path(
        "api/v1/clusters/",
        include(
            ("uia_backend.cluster.api.v1.urls", "cluster_api_v1"),
            namespace="cluster_api_v1",
        ),
    ),
    path(
        "api/v1/notifications/",
        include(
            ("uia_backend.notification.api.v1.urls", "notification_api_v1"),
            namespace="notification_api_v1",
        ),
    ),
    path(
        "api/v1/messaging/",
        include(
            ("uia_backend.messaging.api.v1.urls", "messaging_api_v1"),
            namespace="messaging_api_v1",
        ),
    ),
    path(
        "api/v1/experiments/",
        include(
            ("uia_backend.experiments.api.v1.urls", "experiments_api_v1"),
            namespace="experiments_api_v1",
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("api/anymail-webhook/", include("anymail.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("__debug__/", include("debug_toolbar.urls")),
]
