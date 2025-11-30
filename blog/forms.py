from django import forms  # Импорт модуля форм Django
from django.contrib.auth.forms import UserCreationForm  # Встроенная форма регистрации Django
from django.contrib.auth.models import User  # Модель пользователя Django
from django.core.exceptions import ValidationError  # Исключения валидации
from .models import Post, Comment, UserProfile, Category  # Модели приложения blog

# Форма регистрации нового пользователя
class RegisterForm(UserCreationForm):  # Наследуемся от UserCreationForm для добавления поля email
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'matrix-input'}))  # Поле email с стилизацией Matrix
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))  # Поле username с стилизацией Matrix
    
    class Meta:  # Метаданные формы
        model = User  # Модель, связанная с формой
        fields = ['username', 'email', 'password1', 'password2']  # Отображаемые поля (password1 - пароль, password2 - подтверждение пароля)
        
    def __init__(self, *args, **kwargs):  # Инициализация формы
        super().__init__(*args, **kwargs)  # Вызов родительского конструктора
        for field_name, field in self.fields.items():  # Перебор всех полей формы
            if field_name not in ['username', 'email']:  # Если поле не username и не email
                field.widget.attrs.update({'class': 'matrix-input'})  # Добавляем CSS класс для стилизации
    
    def clean_email(self):  # Кастомная валидация поля email
        email = self.cleaned_data.get('email')  # Получаем очищенное значение email
        if User.objects.filter(email=email).exists():  # Проверяем, существует ли пользователь с таким email
            raise ValidationError("This email is already registered.")  # Выдаем ошибку валидации
        return email  # Возвращаем email если он уникален

# Форма входа пользователя
class LoginForm(forms.Form):  # Простая форма для входа
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))  # Поле логина
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'matrix-input'}))  # Поле пароля (скрытый ввод)
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'matrix-checkbox'}))  # Чекбокс "запомнить меня"

# Форма создания/редактирования поста
class PostForm(forms.ModelForm):  # Форма на основе модели Post
    class Meta:  # Метаданные формы
        model = Post  # Модель Post
        fields = ['title', 'content', 'excerpt', 'category', 'image', 'tags', 'status']  # Поля для редактирования
        widgets = {  # Настройки виджетов для стилизации
            'title': forms.TextInput(attrs={'class': 'matrix-input'}),  # Заголовок поста
            'content': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 12}),  # Содержимое поста (большое текстовое поле)
            'excerpt': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 3}),  # Краткое описание
            'tags': forms.TextInput(attrs={'class': 'matrix-input'}),  # Теги поста
            'status': forms.Select(attrs={'class': 'matrix-input'}),  # Статус публикации (выпадающий список)
            'category': forms.Select(attrs={'class': 'matrix-input'}),  # Категория поста (выпадающий список)
        }

# Форма создания комментария
class CommentForm(forms.ModelForm):  # Форма для создания комментария
    class Meta:
        model = Comment
        fields = ['text']  # Только текст комментария
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'matrix-input'})  # Текстовое поле для комментария
        }

# Форма ответа на комментарий
class ReplyForm(forms.ModelForm):  # Форма для ответа на комментарий (более короткая)
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'matrix-input'})  # Меньше строк для ответа
        }

# Форма редактирования профиля пользователя
class UserProfileForm(forms.ModelForm):  # Форма для редактирования профиля
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'website', 'avatar', 'birth_date']  # Поля профиля
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 4}),  # Биография (текстовое поле)
            'location': forms.TextInput(attrs={'class': 'matrix-input'}),  # Местоположение
            'website': forms.URLInput(attrs={'class': 'matrix-input'}),  # Сайт (валидация URL)
            'birth_date': forms.DateInput(attrs={'class': 'matrix-input', 'type': 'date'}),  # Дата рождения (календарь)
        }

# Форма обновления данных пользователя
class UserUpdateForm(forms.ModelForm):  # Форма для редактирования данных пользователя Django
    email = forms.EmailField()  # Поле email (переопределяем стандартное)
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']  # Основные поля пользователя
        widgets = {
            'username': forms.TextInput(attrs={'class': 'matrix-input'}),  # Логин
            'email': forms.EmailInput(attrs={'class': 'matrix-input'}),  # Email
            'first_name': forms.TextInput(attrs={'class': 'matrix-input'}),  # Имя
            'last_name': forms.TextInput(attrs={'class': 'matrix-input'}),  # Фамилия
        }

# Форма поиска
class SearchForm(forms.Form):  # Форма для поиска по сайту
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'matrix-input'}))  # Поисковый запрос (необязательное поле)
    search_in = forms.ChoiceField(choices=[('all', 'All'), ('posts', 'Posts'), ('users', 'Users')], initial='all', widget=forms.Select(attrs={'class': 'matrix-input'}))  # Где искать

# Форма обратной связи
class ContactForm(forms.Form):  # Форма для отправки сообщений администрации
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))  # Имя отправителя
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'matrix-input'}))  # Email отправителя
    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))  # Тема сообщения
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'matrix-input', 'rows': 5}))  # Текст сообщения
