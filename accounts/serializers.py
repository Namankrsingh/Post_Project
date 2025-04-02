from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.Serializer):
    first_name= serializers.CharField()
    last_name= serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError('username is already taken')
        
        return data
    
    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])  
        user.save()  
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        return {'user': user}

    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'message': 'Login successful',
            'data': {
                'token': {'refresh': str(refresh), 'access': str(refresh.access_token)}
            }
        }