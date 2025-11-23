from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Post, Comment, UserProfile, Category

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'matrix-input'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['username', 'email']:
                field.widget.attrs.update({'class': 'matrix-input'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'matrix-input'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'matrix-checkbox'}))

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'excerpt', 'category', 'image', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'matrix-input'}),
            'content': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 12}),
            'excerpt': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 3}),
            'tags': forms.TextInput(attrs={'class': 'matrix-input'}),
            'status': forms.Select(attrs={'class': 'matrix-input'}),
            'category': forms.Select(attrs={'class': 'matrix-input'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'matrix-input'})
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'matrix-input'})
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'website', 'avatar', 'birth_date']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'matrix-input', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'matrix-input'}),
            'website': forms.URLInput(attrs={'class': 'matrix-input'}),
            'birth_date': forms.DateInput(attrs={'class': 'matrix-input', 'type': 'date'}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'matrix-input'}),
            'email': forms.EmailInput(attrs={'class': 'matrix-input'}),
            'first_name': forms.TextInput(attrs={'class': 'matrix-input'}),
            'last_name': forms.TextInput(attrs={'class': 'matrix-input'}),
        }

class SearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'matrix-input'}))
    search_in = forms.ChoiceField(choices=[('all', 'All'), ('posts', 'Posts'), ('users', 'Users')], initial='all', widget=forms.Select(attrs={'class': 'matrix-input'}))

class ContactForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'matrix-input'}))
    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'matrix-input'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'matrix-input', 'rows': 5}))
