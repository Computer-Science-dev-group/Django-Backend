from rest_framework import serializers

from .models import CustomUser, Link


class LinkSerializer(serializers.ModelSerializer):
    """ Serializer for the Link model """

    class Meta:
        model = Link
        fields = '__all__'


class CustomUserProfileSerializer(serializers.ModelSerializer):
    """ Serializer fro the Custom User model """

    id = serializers.UUIDField(read_only=True)
    year_of_graduation = serializers.CharField(read_only=True)
    department = serializers.CharField(read_only=True)
    faculty_or_college = serializers.CharField(read_only=True)

    links = LinkSerializer(many=True, read_only=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'email', 'profile_picture', 'cover_photo',
                  'year_of_graduation', 'department', 'faculty_or_college', 'phone_number',
                  'display_name', 'is_active', 'is_verified', 'bio', 'last_login', 'created_datetime',
                  'updated_datetime', 'app_version', 'gender', 'date_of_birth', 'links')
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'required': False},
            'is_verified': {'required': False},
            'links': {'required': False},
            'profile_picture': {'required': False},
            'cover_photo': {'required': False},
            'display_name': {'required': False},
            'bio': {'required': False},
            'gender': {'required': False},
            'date_of_birth': {'required': False},
            'app_version': {'required': False},
        }

    def create(self, validated_data):
        """
        Create and return a new `CustomUser` instance, given the validated data.
        """
        return CustomUser.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `CustomUser` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
