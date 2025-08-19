from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('home', views.home, name='home'),
    path('create_blog/<int:user_id>/', views.create_blog, name='create_blog'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/<int:user_id>/edit/<int:blog_id>', views.blog_redaction, name='blog_redaction'),
    path('profile/edit_profile/<int:user_id>', views.profile_edit, name='profile_edit'),
    path('profile/view_profile/<int:user_id>', views.profile_view, name='profile_view'),
    path('logout/', views.logout_view, name='logout'),
    path('blog/<int:blog_id>/', views.blog_view, name='blog_view'),
    path('blog/<int:blog_id>/like/', views.like_blog, name='like_blog'),
    path('blog/break/<int:user_id>/<int:blog_id>', views.blog_break, name='blog_break'),
    path('home/results/', views.search_result, name='search_result'),
    path('justice/', views.violations, name='violations'),
    path('justice/verdict/<int:user_id>/<int:blog_id>', views.blog_verdict, name='verdict'),
    path('tg_verify/', views.tg_verify, name='tg_verify')
]

# Додаємо налаштування для статичних і медіа файлів
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)