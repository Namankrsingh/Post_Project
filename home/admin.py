from django.contrib import admin
from .models import Blog
from .models import Comment

admin.site.register(Comment)
admin.site.register(Blog)