from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Blog, CustomUser, Tag
from .views import recommend_blogs
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile


class RegistrationTest(TestCase):
    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'phone_number': '+380991112233',
            'nickname': 'TestUser',
            'password1': 'StrongPassword123',
            'password2': 'StrongPassword123',
        })

        self.assertEqual(response.status_code, 302)  # Перевірка редиректу
        self.assertTrue(get_user_model().objects.filter(phone_number='+380991112233').exists())


class BlogTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+380991112200',
            password='testpass',
            nickname='BlogUser',
            is_active=True
        )
        self.client.login(phone_number='+380991112200', password='testpass')
    
    def test_blog_creation(self):
        # Створюємо реальне зображення в памʼяті
        image_io = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="red")
        image.save(image_io, format='JPEG')
        image_io.seek(0)

        uploaded_image = SimpleUploadedFile("test.jpg", image_io.read(), content_type="image/jpeg")

        url = reverse('create_blog', args=[self.user.id])
        response = self.client.post(url, {
            'topic': 'Test Blog Topic',
            'text': 'This is some blog text',
            'tags': 'django, python',
            'image': uploaded_image,
        })

        # Вивід HTML у разі помилки
        if response.status_code != 302:
            print(response.content.decode())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Blog.objects.filter(topic='Test Blog Topic').exists())





class RecommendationTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+380991112244',
            password='reco1234',
            nickname='RecoUser',
            is_active=True
        )

        # Створюємо блоги з тегами
        for i in range(5):
            tag = Tag.objects.create(name=f"tag{i}")
            blog = Blog.objects.create(
                author=self.user,
                topic=f"Blog {i}",
                text="Some text",
                image='path/to/image.jpg'
            )
            blog.tags.add(tag)

    def test_recommend_blogs(self):
        recommended = recommend_blogs(self.user)
        self.assertIsInstance(recommended, list)
        self.assertGreaterEqual(len(recommended), 0)
