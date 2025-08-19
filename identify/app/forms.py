from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Blog, ProfileInformation, Break_rull_blogs
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        error_messages={
            'required': _('Це поле є обов’язковим!'),
        }
    )
    password2 = forms.CharField(
        label="Підтвердження пароля",
        widget=forms.PasswordInput,
        error_messages={
            'required': _('Це поле є обов’язковим!'),
        }
    )

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'nickname')
        error_messages = {
            'phone_number': {
                'required': _('Це поле є обов’язковим!'),
                'invalid': _('Введіть правильний номер телефону!'),
                'unique': _('Користувач з таким номером телефону вже існує!'),
            },
            'nickname': {
                'required': _('Це поле є обов’язковим!'),
                'unique': _('Цей нікнейм вже зайнятий!'),
            },
        }

    def clean_password2(self):
        """
        Перевіряє, чи паролі співпадають, і задає кастомне повідомлення у випадку помилки.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _("Паролі не співпадають!"),  # Ваш кастомний текст помилки
                code='password_mismatch',
            )
        
        if len(password1) < 8 or len(password2) < 8:
            raise forms.ValidationError(
                _('Пароль занадто коротки. Він повинен бути хочаб з 8 символів.'),
                code='password_too_short',
            )

        return password2


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'password')

    error_messages = {
        "invalid_login": ("Будь ласка, перевірте введені дані"),
    }


class BlogForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=200, 
        required=False, 
        help_text="Формат запису: тег, тег, тег",
        widget=forms.TextInput(attrs={'placeholder': 'Формат запису: тег, тег, тег'})
    )

    class Meta:
        model = Blog
        fields = ['topic','image', 'text', 'tags']
        widgets = {
            'topic': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

class Blog_break(forms.ModelForm):
    degree = forms.IntegerField(
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={'min': '1'})
    )

    class Meta:
        model = Break_rull_blogs
        fields = ['reason', 'degree']


class ProfileForm(forms.ModelForm):
    nickname = forms.CharField(max_length=20)

    # Используем виджет ColorInput для поля main_color
    main_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))
    
    # Используем виджет ColorInput для поля header_color
    header_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))

    text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))

    class Meta:
        model = ProfileInformation
        fields = ['avatar', 'description', 'main_color', 'header_color', 'text_color']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['nickname'].initial = self.instance.user.nickname
            self.fields['description'].initial = self.instance.description
            self.fields['avatar'].initial = self.instance.avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        if 'nickname' in self.cleaned_data:
            profile.user.nickname = self.cleaned_data['nickname']
            profile.user.save()
        if commit:
            profile.save()
        return profile