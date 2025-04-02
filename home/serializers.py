from rest_framework import serializers
from .models import Blog, Comment, BlogLike, CommentLike

class CommentSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source="user_id.id") 
    blog_id = serializers.ReadOnlyField(source="blog_id.uid")
    created_by = serializers.ReadOnlyField(source='user_id.username')
    total_likes = serializers.SerializerMethodField()
    total_dislikes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['uid', 'user_id', 'blog_id', 'created_at', 'comment_text', 'created_by','total_likes', 'total_dislikes']
    
    def get_total_likes(self, obj):
        return obj.likes.filter(like_status=1).count()

    def get_total_dislikes(self, obj):
        return obj.likes.filter(like_status=-1).count()

class BlogSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='user_id.username') 
    user_id = serializers.ReadOnlyField(source="user_id.id")
    total_likes = serializers.SerializerMethodField()
    total_dislikes = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        fields = ['uid', 'user_id', 'created_at', 'title', 'blog_text', 'main_image', 'created_by','total_likes', 'total_dislikes','comments']
    
    def get_total_likes(self, obj):
        return obj.likes.filter(like_status=1).count()

    def get_total_dislikes(self, obj):
        return obj.likes.filter(like_status=-1).count()
