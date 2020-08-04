from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image",)
        labels = {
            'group': "Группа (необязательно)",
            'text': "Текст",
            'image': "Загрузите изображение"
        }


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            "text": "Текст вашего комментария",
        }
