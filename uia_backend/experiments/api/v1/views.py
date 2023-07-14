from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.experiments.api.v1.serializers import (
    PreAplhaTestingPopulationSerializer,
)


class PreAplhaTestingPopulationAPIView(generics.GenericAPIView):
    serializer_class = PreAplhaTestingPopulationSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
