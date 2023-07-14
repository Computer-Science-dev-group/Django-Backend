from django.urls import path

from uia_backend.experiments.api.v1.views import PreAplhaTestingPopulationAPIView

urlpatterns = [
    path(
        "prealphatest/",
        PreAplhaTestingPopulationAPIView.as_view(),
        name="er001_population_details",
    ),
]
