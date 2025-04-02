from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework import status

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Your account has been created'}, status=status.HTTP_201_CREATED)
        return Response({'data': serializer.errors, 'message': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            response = serializer.get_jwt_token(serializer.validated_data['user'])
            return Response(response, status=status.HTTP_200_OK)
        return Response({'data': serializer.errors, 'message': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)
