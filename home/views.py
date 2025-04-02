from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Blog, Comment, BlogLike, CommentLike
from .serializers import BlogSerializer, CommentSerializer
from collections import defaultdict


class BlogPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

class BlogLikeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        blog = get_object_or_404(Blog, uid=request.data.get('blog_id'))
        blog_like, created = BlogLike.objects.get_or_create(user_id=request.user, blog_id=blog)
        if not created:
            blog_like.like_status = 1 if blog_like.like_status == 0 else 0
            blog_like.save()
        
        return Response({'message': 'Blog like status updated'}, status=status.HTTP_200_OK)

class CommentLikeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        comment = get_object_or_404(Comment, uid=request.data.get('comment_id'))
        comment_like, created = CommentLike.objects.get_or_create(user_id=request.user, comment_id=comment)
        if not created:
            comment_like.like_status = 1 if comment_like.like_status == 0 else 0
            comment_like.save()
        
        return Response({'message': 'Comment like status updated'}, status=status.HTTP_200_OK)

class PublicBlogView(APIView):
    pagination_class = BlogPagination
    permission_classes = [AllowAny]

    def get(self, request):
        blogs = Blog.objects.prefetch_related('comments').annotate(
            total_likes=Count('likes', filter=Q(likes__like_status=1)),
            total_dislikes=Count('likes', filter=Q(likes__like_status=-1))
        )
        search_query = request.GET.get('search')
        if search_query:
            blogs = blogs.filter(Q(title__icontains=search_query) | Q(blog_text__icontains=search_query))

        paginator = self.pagination_class()
        paginated_blogs = paginator.paginate_queryset(blogs, request)
        serializer = BlogSerializer(paginated_blogs, many=True)
        return paginator.get_paginated_response(serializer.data)


class BlogView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = BlogPagination

    def get(self, request):
        blogs = Blog.objects.filter(user_id=request.user).prefetch_related('comments').annotate(
            total_likes=Count('likes', filter=Q(likes__like_status=1)),
            total_dislikes=Count('likes', filter=Q(likes__like_status=-1))
        )
        search_query = request.GET.get('search')
        if search_query:
            blogs = blogs.filter(Q(title__icontains=search_query) | Q(blog_text__icontains=search_query))
        
        paginator = self.pagination_class()
        paginated_blogs = paginator.paginate_queryset(blogs, request)
        serializer = BlogSerializer(paginated_blogs, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data["user_id"] = request.user.id 
        serializer = BlogSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user_id=request.user)
            return Response({'data': serializer.data, 'message': 'Blog created successfully'}, status=status.HTTP_201_CREATED)
        return Response({'data': serializer.errors, 'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    
    # def patch(self, request, blog_id):
    #     blog = get_object_or_404(Blog, uid=blog_id)
    def patch(self, request):
        blog = get_object_or_404(Blog, uid=request.data.get('blog_id')) 
        if request.user != blog.user_id:
            return Response({'message': 'Unauthorized: You can only edit your own blogs'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Blog updated successfully'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    # def delete(self, request, blog_id):
    #     blog = get_object_or_404(Blog, uid=blog_id)
    def delete(self, request):
        blog = get_object_or_404(Blog, uid=request.data.get('blog_id')) 
        if request.user != blog.user_id:
            return Response({'message': 'Unauthorized: You can only delete your own blogs'}, status=status.HTTP_403_FORBIDDEN)

        blog.delete()
        return Response({'message': 'Blog deleted successfully'}, status=status.HTTP_200_OK)
class AllCommentsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        comments = Comment.objects.annotate(
            total_likes=Count('likes', filter=Q(likes__like_status=1)),
            total_dislikes=Count('likes', filter=Q(likes__like_status=-1))
        ).values(
            "uid", "blog_id", "blog_id__title", "created_at", "comment_text",
            "user_id", "user_id__username", "total_likes", "total_dislikes"
        )
        grouped_comments = defaultdict(list)
        for comment in comments:
            grouped_comments[comment["user_id"]].append({
                "uid": comment["uid"],
                "blog_id": comment["blog_id"],
                "created_at": comment["created_at"],
                "comment_text": comment["comment_text"],
                "likes": comment["total_likes"],
                "dislikes": comment["total_dislikes"]
            })

        response_data = [
            {
                "user_id": user_id,
                "title": comment["blog_id__title"],
                "commented_by": comments.filter(user_id=user_id).first()["user_id__username"],
                "comments": user_comments
            }
            for user_id, user_comments in grouped_comments.items()
           ]
        return Response({'data': response_data, 'message': 'All comments grouped by user retrieved successfully'}, status=status.HTTP_200_OK)
    
class CommentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Fetch comments made by the authenticated user
        comments = Comment.objects.filter(user_id=request.user.id).annotate(
            total_likes=Count('likes', filter=Q(likes__like_status=1)),
            total_dislikes=Count('likes', filter=Q(likes__like_status=-1))
        ).values(
            "uid", "blog_id", "blog_id__title", "created_at", "comment_text",
            "user_id", "user_id__username", "total_likes", "total_dislikes"
        )

        user = request.user  
        
        grouped_comments = defaultdict(list)
        for comment in comments:
            grouped_comments[comment["blog_id__title"]].append({
                "uid": comment["uid"],
                "created_at": comment["created_at"],
                "comment_text": comment["comment_text"],
                "likes": comment["total_likes"],
                "dislikes": comment["total_dislikes"]
            })

        
        response_data = [
            {
                "user_id": user.id,  
                "title": blog_title,
                "commented_by": user.username, 
                "comments": comments_list
            }
            for blog_title, comments_list in grouped_comments.items()
        ]

        return Response({'data': response_data, 'message': 'Your comments retrieved successfully'}, status=status.HTTP_200_OK)
    def post(self, request):
        blog = get_object_or_404(Blog, uid=request.data.get('blog_id'))
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user, blog_id=blog)
            return Response({'data': serializer.data, 'message': 'Comment added successfully'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        comment = get_object_or_404(Comment, uid=request.data.get('comment_id')) 
        if request.user != comment.user_id:
            return Response({'message': 'Unauthorized: You can only edit your own comments'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Comment updated successfully'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        comment = get_object_or_404(Comment, uid=request.data.get('comment_id')) 
        if request.user != comment.user_id:
            return Response({'message': 'Unauthorized: You can only delete your own comments'}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({'message': 'Comment deleted successfully'}, status=status.HTTP_200_OK)