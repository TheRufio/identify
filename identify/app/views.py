from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.views.decorators.http import require_POST
from django.db.models.signals import post_save
from django.db.models import Count, Q
from django.dispatch import receiver
from django.http import JsonResponse
from .forms import CustomAuthenticationForm, CustomUserCreationForm, BlogForm, ProfileForm, Blog_break
from .models import CustomUser, ProfileInformation, Blog, Tag, Break_rull_blogs, BlogView
from os import path, remove
from . import verify
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
import random

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect("tg_verify")
    else:
        form = CustomUserCreationForm()
    return render(request, "app/register.html", {"form" : form})

def tg_verify(request):    
    return render(request, "app/verify_tg.html")

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(
                    request,
                    'Ваш аккаунт не активовано. Перейдіть до телеграм боту identify'
                )
            else:
                login(request, user)
                return redirect("home")
    else:
        form = CustomAuthenticationForm()
        
    return render(request, "app/login.html", {"form" : form})

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url="login")
def create_blog(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    existing_tags = Tag.objects.values_list('name', flat=True)

    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            tag_names = form.cleaned_data['tags'].split(',')
            tag_names = [name.strip().lower() for name in tag_names if name.strip()]

            if not tag_names:  # Проверяем, указаны ли теги
                form.add_error('tags', 'Будь ласка вкажіть хоча б один тег')
            else:
                start_time = time.time()

                blog = form.save(commit=False)
                blog.author = user
                blog.save()

                for name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=name)
                    blog.tags.add(tag)
                end_time = time.time()
                print(f"[⏱ BLOG CREATE] Час створення блогу та тегів: {round(end_time - start_time, 4)} сек.")
                return redirect('profile', user_id=user.id)
    else:
        form = BlogForm()

    context = {
        'form': form,
        'existing_tags': list(existing_tags),
        'search_result': search_method()
    }

    return render(request, 'app/create_blog.jinja', context)


# def extract_tags_from_image(image_path):
#     detector = ObjectDetection()
#     model_path = path.join("app/yolo.h5")
#     detector.setModelTypeAsYOLOv3() 
#     detector.setModelPath(model_path)
#     detector.loadModel()
#     detections = detector.detectObjectsFromImage(input_image=image_path, output_image_path="app/detected.jpg")
#     tags = [detection['name'] for detection in detections]

#     return tags


@login_required(login_url='login')
def blog_redaction(request, user_id, blog_id):
    user = get_object_or_404(CustomUser, id=user_id)
    blog = get_object_or_404(Blog, id=blog_id, author=user)
    if request.method == 'POST':
        if 'delete' in request.POST:
            if blog.image:
                if path.isfile(blog.image.path):
                    remove(blog.image.path)
            blog.delete()
            return redirect('profile', user_id=user.id)
        
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = user
            blog.save()

            blog.tags.clear()
            tag_names = form.cleaned_data['tags'].split(',')
            for name in tag_names:
                name = name.strip().lower()
                if name:
                    tag, created = Tag.objects.get_or_create(name=name)
                    blog.tags.add(tag)
            
            return redirect(profile, user_id=user.id)
    else:
        form = BlogForm(instance=blog)
    
    context = {
        'form': form,
        'blog': blog,
        'search_result': search_method()
    }
    return render(request, 'app/blog_redaction.html', context)

@login_required(login_url='login')
def blog_view(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    # Перевіряємо, чи існує запис про перегляд
    blog_view, created = BlogView.objects.get_or_create(user=request.user, blog=blog)
    if not created:
        # Якщо запис існує, оновлюємо час перегляду
        blog_view.viewed_at = timezone.now()
        blog_view.save()

    context = {
        'blog': blog,
        'tags': blog.tags.all(),
        'search_result': search_method()
    }
    return render(request, 'app/blog_view.jinja', context)

@require_POST
@login_required(login_url='login')
def like_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)

    if request.user in blog.likers.all():
        blog.likers.remove(request.user)
        blog.like -= 1
        status = 'unliked'
    else:
        blog.likers.add(request.user)
        blog.like += 1
        status = 'liked'

    blog.save()
    blog.author.profile.update_blog_statistics()
    return JsonResponse({'status': status, 'likes': blog.like})

@login_required(login_url='login')
def blog_break(request, user_id, blog_id):
    user = get_object_or_404(CustomUser, id=user_id)
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == 'POST':
        form = Blog_break(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            degree = form.cleaned_data['degree']

            violation = Break_rull_blogs.objects.create(
                blog=blog,
                reason=reason,
                degree=degree
            )

            # if path.isfile(blog.image.path):
            #         remove(blog.image.path)
            # blog.delete()
            blog.is_hidden = True
            blog.author.profile.update_blog_statistics()
            verify.report_user(blog.author.telegram_chat_id, reason)
            
            blog.author.break_rull += int(degree)
            
            if blog.author.break_rull >= 3:
                blog.author.is_active = False
                verify.disactive_account(blog.author.telegram_chat_id)
                
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                for session in sessions:
                    session_data = session.get_decoded()
                    if session_data.get('_auth_user_id') == str(blog.author.id):
                        session.delete()

            blog.author.save()
            return redirect('home')
    elif request.method == 'GET':
        form = Blog_break()

    context = {
        'user': user,
        'blog': blog,
        'form': form,
        'search_result': search_method()
    }
    return render(request, 'app/blog_break.jinja', context)

@login_required(login_url='login')
def profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    blogs = user.blogs.all()
    profile_info = user.profile
    context = {
        'user': user,
        'blogs': blogs,
        'profile_info': profile_info,
        'search_result': search_method()
    }
    return render(request,'app/profile.jinja', context)

@login_required(login_url='login')
def profile_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    profile_info = get_object_or_404(ProfileInformation, user=user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile_info)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.user.nickname = form.cleaned_data['nickname']
            profile.user.save()
            profile.save()
            return redirect('profile', user_id=user.id)
    elif request.method == 'GET':
        form = ProfileForm(instance=profile_info)
    
    context = {
        'user': user,
        'profile_info': profile_info,
        'form': form,
        'search_result': search_method()
    }
    return render(request, 'app/profile_edit.jinja', context)

@login_required(login_url='login')
def profile_view(request, user_id):
    user_view = get_object_or_404(CustomUser, id=user_id)
    if user_view == request.user:
        return redirect('profile', user_id=request.user.id)
    blogs = user_view.blogs.all()
    context = {
        'user_view': user_view,
        'blogs': blogs,
        'search_result': search_method()
    }
    return render(request, 'app/profile_view.jinja', context)

import random

@login_required(login_url="login")
def home(request):
    user = get_object_or_404(CustomUser, id=request.user.id)
    viewed_and_liked_blogs = Blog.objects.filter(viewers=user)
    
    if not viewed_and_liked_blogs.exists():
        all_tags = list(Tag.objects.all())
        if all_tags:
            random_tags = random.sample(all_tags, k=min(len(all_tags), len(all_tags)//2))
            
            blogs = Blog.objects.filter(tags__in=random_tags).distinct()
        else:
            blogs = Blog.objects.none() 
    else:
        blogs = recommend_blogs(user)
        print(f"Рекомендовані блоги: {blogs}")

    # print(f"Випадкові теги: {random_tags}")
    context = {
        'blogs': blogs,
        'search_result': search_method()
    }

    return render(request, 'app/home.html', context)

def recommend_blogs(user):
    import time
    start_time = time.time()

    last_viewed_blogs = BlogView.objects.filter(user=user).order_by('-viewed_at')[:5]

    if not last_viewed_blogs.exists():
        blogs = Blog.objects.exclude(author=user).distinct().order_by('?')
        print("[ℹ] Використано випадкові блоги")
        return list(blogs)

    last_viewed_tags = set()
    for blog_view in last_viewed_blogs:
        last_viewed_tags.update(blog_view.blog.tags.values_list('name', flat=True))

    blogs = list(Blog.objects.prefetch_related('tags').exclude(author=user))
    blog_texts = [
        ' '.join(blog.tags.values_list('name', flat=True))
        for blog in blogs
    ]

    if not blog_texts:
        return Blog.objects.none()

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(blog_texts)
    user_vector = vectorizer.transform([' '.join(last_viewed_tags)])
    similarity_scores = cosine_similarity(user_vector, tfidf_matrix)

    threshold = 0.1
    recommended_indices = [
        i for i, score in enumerate(similarity_scores[0]) if score > threshold
    ]
    recommended_blog_ids = {blogs[i].id for i in recommended_indices}
    recommended_blogs = Blog.objects.filter(id__in=recommended_blog_ids).exclude(author=user).distinct()
    random_blogs = Blog.objects.exclude(id__in=recommended_blog_ids).exclude(author=user).distinct().order_by('?')
    combined_blogs = list(recommended_blogs) + list(random_blogs)
    combined_blogs = list({blog.id: blog for blog in combined_blogs}.values())
    random.shuffle(combined_blogs)

    end_time = time.time()
    print(f"[⏱ RECOMMENDER] Час формування рекомендацій: {round(end_time - start_time, 4)} сек.")

    return combined_blogs

    
def search_method():
    topics = list(Blog.objects.values_list('topic', flat=True))
    tags = list(Tag.objects.values_list('name', flat=True))

    search_result = list(set(topics + tags))

    return search_result

@login_required(login_url='login')
def search_result(request):
    query = request.GET.get('query', '').strip()  # Отримуємо введений текст із параметра 'query'
    print(f"Пошуковий запит: {query}")

    # Пошук блогів за темою (topic) або тегами (tags)
    blogs = Blog.objects.filter(
        Q(topic__icontains=query) | Q(tags__name__icontains=query)).distinct()  # Використовуємо Q для комбінованого пошуку

    # Отримуємо всі доступні теги
    tags = Tag.objects.values_list('name', flat=True)

    context = {
        'blogs': blogs,
        'query': query,  # Передаємо введений текст назад у шаблон
        'search_result': tags,  # Передаємо теги для відображення у <datalist>
    }
    return render(request, 'app/home.html', context)

@login_required(login_url='login')
def violations(request):
    
    if request.method == 'GET':
        blogs = Break_rull_blogs.objects.all()

    context = {
        'blogs' : blogs,
        'search_result': search_method()
    }
    return render(request, 'app/violations.html', context)

@login_required(login_url='login')
def blog_verdict(request, user_id, blog_id):
    user = get_object_or_404(CustomUser, id=user_id)
    blog = get_object_or_404(Blog, id=blog_id, author=user)
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            verify.verdict_negative(user.telegram_chat_id, blog)
            if blog.image:
                if path.isfile(blog.image.path):
                    remove(blog.image.path)
            blog.delete()
            return redirect('violations')
        elif 'save' in request.POST:
            verify.verdict_positive(user.telegram_chat_id, blog)
            blog.is_hidden = False
            blog.save()
            blog.violation.delete()
            return redirect('violations')

    context = {
        'blog_view': blog,
        'user_view': user,
        'search_result': search_method()
    }
    return render(request, 'app/violation_verdict.jinja', context)

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        ProfileInformation.objects.create(user=instance)

