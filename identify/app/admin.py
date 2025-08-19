from django.contrib import admin
from .models import CustomUser, ProfileInformation, Blog, Break_rull_blogs, Tag

admin.site.register((CustomUser, ProfileInformation, Blog, Break_rull_blogs, Tag))