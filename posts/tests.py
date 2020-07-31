from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Post, Group
from users import views


class TestStringMethods(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='peter',
            email='capaldi@gmail.com',
        )
        self.group = Group.objects.create(
            title="Восток",
            slug="east"
        )

        self.client_auth = Client()
        self.client_auth.force_login(self.user)

        self.client_unauth = Client()

    def get_the_urls(self, user, post, group):
        """Вспомогательный метод для сбора url"""
        urls = [reverse('index'),
                reverse('profile', kwargs={'username': user.username}),
                reverse('post', kwargs={'username': user.username,
                                        'post_id': post.id}),
                reverse('group', kwargs={'slug': self.group.slug})]
        return urls

    def check_post_values(self, post, text, author, group):
        self.assertEqual(post.text, text, "Check text failed")
        self.assertEqual(post.author, author, "Check author failed")
        self.assertEqual(post.group, group, "Check group failed")

    def check_post_on_page(self, url, text, author, group):
        """Вспомогательный метод для проверки наличия поста и паджинатора"""
        response = self.client_auth.post(url)
        if 'paginator' in response.context:
            posts_list = response.context['paginator'].object_list
            posts_count = response.context['paginator'].count
            self.assertEqual(posts_count, 1)
            self.check_post_values(posts_list[0], text, author, group)
        else:
            self.check_post_values(response.context['post'],
                                   text, author, group)

    def test_post_exists(self):
        """Проверка наличия поста"""
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group)
        urls = self.get_the_urls(user=self.user, post=post, group=self.group)
        for url in urls:
            self.check_post_on_page(
                url=url,
                text=post.text,
                author=post.author,
                group=post.group)

    def test_edit_post(self):
        """Проверка на редактирование поста"""
        post = Post.objects.create(
            text='тестовый пост',
            author=self.user,
            group=self.group)

        group_new = Group.objects.create(
            title="Запад",
            slug="west")

        kwargs = {'username': self.user.username, 'post_id': post.id}
        path = reverse('post_edit', kwargs=kwargs)
        data = {'text': 'Новый текст поста!!!!', 'group': group_new.id}
        response = self.client_auth.post(path, data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        urls = self.get_the_urls(user=self.user, post=post, group=group_new)
        for url in urls:
            self.check_post_on_page(url=url, text=data['text'],
                                    author=self.user, group=group_new)

    def test_no_new_post(self):
        """Проверка не невозможность создать пост"""
        response = self.client_unauth.post(reverse('new_post'),
                                           data={
                                               'text': 'какой-то текст',
                                               'group': self.group},
                                           Follow=True)
        self.assertEqual(response.status_code, 302)
        posts = Post.objects.count()
        self.assertEqual(posts, 0)

        login = reverse('login')
        new = reverse('new_post')
        self.assertRedirects(response, f'{login}?next={new}')

# Для своего локального проекта напишите тест: возвращает ли сервер код 404, если страница не найдена.