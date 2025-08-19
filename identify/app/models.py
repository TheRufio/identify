from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.timezone import now

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Користувач повинен мати номер телефону")
    
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Введите правильный номер телефона.')]
    )
    nickname = models.CharField(max_length=20, blank=False)
    # first_name = models.CharField(max_length=30, blank=True)
    # last_name = models.CharField(max_length=30, blank=True) # на майбутню інтеграцію партнерську)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    break_rull = models.IntegerField(default=0)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class ProfileInformation(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    likes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', default='default_avatars/logo1.png')
    description = models.TextField(default='', blank=True, null=True)
    main_color = models.CharField(max_length=7, default='#fdbac5')
    header_color = models.CharField(max_length=7, default='#fcdddd')
    text_color = models.CharField(max_length=7, default='#6A5ACD')

    def update_blog_statistics(self):
        blogs = self.user.blogs.filter(is_hidden=False)
        self.likes = sum(blog.like for blog in blogs)
        self.views = sum(blog.view for blog in blogs)
        self.save()

class Blog(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blogs'
    )
    image = models.ImageField(upload_to='blog_images/',)
    topic = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    like = models.IntegerField(default=0)
    view = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name='blogs', blank=False)
    viewers = models.ManyToManyField(
        CustomUser,
        related_name="viewed_blogs",
        through="BlogView"
    )
    likers = models.ManyToManyField(get_user_model(), related_name='liked_blogs', blank=True)

    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.topic} - {self.author.nickname}"

class BlogView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(default=now, null=True, blank=True)  # Час перегляду

class Break_rull_blogs(models.Model):
    blog = models.OneToOneField(Blog, on_delete=models.CASCADE, related_name='violation')
    reason = models.TextField()
    degree = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    bloked_at = models.DateTimeField(auto_now_add=True)
    appeal = models.TextField(blank=True)
    is_appealed = models.BooleanField(default=False)

@receiver(post_save, sender=Blog)
@receiver(post_delete, sender=Blog)
def cleanup_unused_tages(sender, instance, **kwargs):
    unused_tags = Tag.objects.annotate(blog_count=models.Count('blogs')).filter(blog_count=0)
    unused_tags.delete()