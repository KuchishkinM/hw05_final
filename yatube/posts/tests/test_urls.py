from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Post, Group, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            slug='test_slug',
            title='Тестовый заголовок',
            description='Тестовое описание',
        )
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user}/', 'posts/profile.html'),
            (f'/posts/{cls.post.id}/', 'posts/post_detail.html'),
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_public_urls_work(self):
        for url, _ in PostURLTests.public_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_user_cannot_access_private_urls(self):
        for url, _ in PostURLTests.private_urls:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authenticated_author_can_access_private_urls(self):
        for url, _ in PostURLTests.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_use_correct_templates(self):
        for url, template in PostURLTests.public_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_use_correct_template_for_post_author(self):
        for url, template in PostURLTests.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_server_responds_404_for_unexisted_page(self):
        response = self.authorized_client.get('unexisted_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
