from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User, Follow


class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group = Group.objects.create(
            slug='test_slug',
            title='Тестовый заголовок',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'Noname'}): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})): 'posts/post_detail.html',
            (reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})): 'posts/create_post.html',
            (reverse('posts:post_create')): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        object = response.context['page_obj'][0]
        self.assertEqual(object, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertEqual(response.context['post'].group.title,
                         'Тестовый заголовок')
        self.assertEqual(response.context['post'].text, 'Тестовый текст')
        self.assertEqual(response.context['post'].group.slug, 'test_slug')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'Noname'}))
        object = response.context['page_obj'][0].author.username
        self.assertEqual(object, 'Noname')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail для создания поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post'].id
        self.assertEqual(post, self.post.id)
        self.assertEqual(post, 1)

    def test_post_edit_page_show_correct_context(self):
        """Проверка формы редактирования поста, отфильтрованного по ID"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_field_text = response.context['form'].initial['text']
        self.assertEqual(form_field_text, self.post.text)

    def test_create_post_page_show_correct_context(self):
        """Проверка формы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_cache_index_page(self):
        """Тестирование кеширования главной страницы."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        post = Post.objects.get(id=1)
        cache_save = response.content
        post.delete()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_save)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_save)


class FollowPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unfollower_user = User.objects.create_user(username='noname')
        cls.follower_user = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='following')
        cls.follow = Follow.objects.create(
            user=cls.follower_user,
            author=cls.author,
        )
        for post in range(2):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.author,
            )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower_user)
        self.unfollower_client = Client()
        self.unfollower_client.force_login(self.unfollower_user)

    def test_auth_user_follow_or_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        follow_count = Follow.objects.count()
        self.unfollower_client.get(
            reverse('posts:profile', kwargs={'username': self.author}))
        self.follow = Follow.objects.create(
            user=self.unfollower_user,
            author=self.author,
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.follow_del = Follow.objects.filter(
            user=self.unfollower_user,
            author=self.author,
        ).delete()
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_user_posts_in_line(self):
        """Новая запись пользователя появляется в ленте тех,
         кто подписан на этого пользователя."""
        response = self.follower_client.get(reverse('posts:follow_index'))
        follow_posts = len(response.context['page_obj'])
        posts = Post.objects.filter(author_id=self.author.id).count()
        self.assertEqual(follow_posts, posts)

    def test_unfollow_user_no_posts_in_line(self):
        """Новая запись пользователя не появляется в ленте тех,
         кто не подписан на этого пользователя."""
        response = self.unfollower_client.get(reverse('posts:follow_index'))
        follow_posts = len(response.context['page_obj'])
        self.assertEqual(follow_posts, 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group = Group.objects.create(
            slug='test_slug',
            title='Тестовый заголовок',
            description='Тестовое описание',
        )
        for post in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()

    def test_index_page_contains_ten_records(self):
        """Проверка, что на страницу index попадает 10 постов."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.COUNT_OF_POSTS_DEFAULT)

    def test_group_list_page_contains_ten_records(self):
        """Проверка, что на страницу group_list попадает 10 постов."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.COUNT_OF_POSTS_DEFAULT)

    def test_profile_page_contains_ten_records(self):
        """Проверка, что на страницу profile попадает 10 постов."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'Noname'}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.COUNT_OF_POSTS_DEFAULT)

    def test_index_second_page_contains_three_records(self):
        """Проверка, что на 2-ую страницу index попадает 3 поста."""
        response = self.client.get(reverse('posts:index'), {'page': '2'})
        self.assertEqual(len(response.context['page_obj']),
                         (Post.objects.count()
                          - settings.COUNT_OF_POSTS_DEFAULT))

    def test_group_list_second_page_contains_three_records(self):
        """Проверка, что на 2-ую страницу group_list попадает 3 поста."""
        response = self.client.get(reverse('posts:group_list', kwargs={
            'slug': 'test_slug'}), {'page': '2'})
        self.assertEqual(len(response.context['page_obj']),
                         (Post.objects.count()
                          - settings.COUNT_OF_POSTS_DEFAULT))

    def test_profile_second_page_contains_three_records(self):
        """Проверка, что на 2-ую страницу profile попадает 3 поста."""
        response = self.client.get(reverse('posts:profile', kwargs={
            'username': 'Noname'}), {'page': '2'})
        self.assertEqual(len(response.context['page_obj']),
                         (Post.objects.count()
                          - settings.COUNT_OF_POSTS_DEFAULT))
