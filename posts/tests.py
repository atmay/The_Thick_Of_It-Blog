from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from .models import User, Post, Group, Comment, Follow


class TestStringMethods(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='peter',
            email='capaldi@gmail.com',
        )

        self.user2 = User.objects.create_user(
            username='marco',
            email='spada@roh.com'
        )

        self.group = Group.objects.create(
            title="Восток",
            slug="east"
        )

        self.client_auth = Client()
        self.client_auth.force_login(self.user)

        self.followee = Client()
        self.followee.force_login(self.user2)

        self.client_unauth = Client()

    def get_the_urls(self, user, post, group):
        """Вспомогательный метод для сбора url"""
        urls = [reverse('index'),
                reverse('profile', kwargs={'username': user.username}),
                reverse('post', kwargs={'username': user.username,
                                        'post_id': post.id}),
                reverse('group', kwargs={'slug': group.slug})]
        return urls

    def check_post_values(self, post, text, author, group, image):
        """Вспомогательный метод для проверки содержимого поста"""
        self.assertEqual(post.text, text, "Check text failed")
        self.assertEqual(post.author, author, "Check author failed")
        self.assertEqual(post.group, group, "Check group failed")
        self.assertEqual(post.image, image, "Check image failed")

    def check_post_on_page(self, url, text, author, group, image):
        """Вспомогательный метод для проверки наличия поста и паджинатора"""
        response = self.client_auth.post(url)
        if 'paginator' in response.context:
            posts_list = response.context['paginator'].object_list
            posts_count = response.context['paginator'].count
            self.assertEqual(posts_count, 1)
            self.check_post_values(posts_list[0], text, author, group, image)
        else:
            self.check_post_values(response.context['post'],
                                   text, author, group, image)

    def add_post_with_file(self, filename):
        with open(filename, 'rb') as img:
            post_with_file = self.client_auth.post(
                reverse('new_post'),
                data={
                    'author': self.user,
                    'text': 'post text',
                    'group': self.group.id,
                    'image': img
                })
            return post_with_file

    def test_post_exists(self):
        """Проверка наличия поста со всеми полями"""
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group,
            image='./static/Image.jpg')
        urls = self.get_the_urls(user=self.user, post=post, group=self.group)
        for url in urls:
            self.check_post_on_page(
                url=url,
                text=post.text,
                author=post.author,
                group=post.group,
                image=post.image)

    def test_edit_post(self):
        """Проверка на редактирование поста"""
        post = Post.objects.create(
            text='тестовый пост',
            author=self.user,
            group=self.group,
            image='image.jpg')

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
                                    author=self.user, group=group_new,
                                    image='image.jpg')

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

    def test_404(self):
        response = self.client.get('nonexisting/address')
        self.assertEqual(response.status_code, 404)

    def test_cache_on_mainpage(self):
        """Проверка работы кэша"""
        self.client.get(reverse('index'))
        new_post = Post.objects.create(text='Пост для проверки кэширования',
                                       author=self.user,
                                       group=self.group)
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, new_post.text)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, new_post.text)

    def test_uploading_nonimage(self):
        """Проверка на тип загружаемого в качестве картинки объекта"""
        cache.clear()
        # проверяем что картинок нет
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'img')

        cache.clear()
        # пробуем добавить пост с НЕПРАВИЛЬНОЙ картинкой
        self.add_post_with_file('./static/NotImage.txt')

        cache.clear()
        # Проверяем что картинки ВСЁ ЕЩЁ НЕТ
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'img')

        cache.clear()
        # пробуем добавить пост с ПРАВИЛЬНОЙ картинкой
        self.add_post_with_file('./static/Image.jpg')

        cache.clear()
        # Проверяем что картинка УЖЕ есть
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'img')

    def test_following_unfollowing(self):
        """Проверка на возможность подписки и отписки"""
        # проверяем исходное количество
        count_follow_before = Follow.objects.all().count()
        self.assertEqual(count_follow_before, 0)

        # пробуем подписать одного юзера на другого и проверяем успех
        kwargs = {'username': self.user2.username}
        path_to_follow = reverse('profile_follow', kwargs=kwargs)
        self.client_auth.get(path_to_follow)
        count_follow_after = Follow.objects.all().count()
        self.assertEqual(count_follow_after, 1)

        # пробуем отписать юзера и проверяем успех
        path_to_unfollow = reverse('profile_unfollow', kwargs=kwargs)
        self.client_auth.get(path_to_unfollow)
        count_unfollow_after = Follow.objects.all().count()
        self.assertEqual(count_unfollow_after, 0)

    def test_showing_posts_of_followee(self):
        """Проверка на персонализированность ленты"""
        # подписываем юзера на автора
        kwargs = {'username': self.user2.username}
        path_to_follow = reverse('profile_follow', kwargs=kwargs)
        self.client_auth.get(path_to_follow)
        # создаем пост от лица автора
        post_of_followee = Post.objects.create(text='Пост для ленты',
                                               author=self.user2,
                                               group=self.group)
        # проверяем ленту подписок юзера, пост есть
        response = self.client_auth.get(reverse('follow_index'))
        self.assertContains(response, post_of_followee)
        # отписываем юзера, проверяем ленту, поста в ней нет
        path_to_unfollow = reverse('profile_unfollow', kwargs=kwargs)
        self.client_auth.get(path_to_unfollow)
        response = self.client_auth.get(reverse('follow_index'))
        self.assertNotContains(response, post_of_followee)

    def test_no_comment_if_unauth(self):
        """Проверка возможности добавления комментариев"""
        post = Post.objects.create(text='рандомный текст',
                                   author=self.user,
                                   group=self.group)
        kwargs = {'username': self.user.username, 'post_id': post.id}
        path = reverse('add_comment', kwargs=kwargs)
        data = {'text': 'комментарий авторизованного пользователя'}

        self.client_unauth.post(path, data=data, follow=True)
        self.assertEqual(Comment.objects.count(), 0)

        response = self.client_auth.post(path, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().text,
                         'комментарий авторизованного пользователя')
