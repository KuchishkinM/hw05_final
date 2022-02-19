import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            image='posts/small.gif',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.all().last().id
        self.assertTrue((Post.objects.filter(id=last_post)).exists())

    def test_post_edit(self):
        form_data = {
            'text': 'Тестовый текст измененный',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(form_data['group'], self.group.pk)
        self.assertNotEqual(Post.objects.get(id=self.post.id).text,
                            self.post.text)

    def test_comment_auth_user(self):
        """Комментировать посты может только авторизованный пользователь"""
        comment_count = Comment.objects.count()
        post_id = Post.objects.latest('pub_date').id
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_with_image(self):
        """Валидная форма создает запись c картинкой в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.pk,
            'text': self.post.text,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text=self.post.text,
                image='posts/small.gif',
            ).exists()
        )

        response = self.client.get(reverse('posts:index'))
        image_object = response.context['page_obj'][0].image
        self.assertEqual(image_object, self.post.image)

        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        image_object = response.context['page_obj'][0].image
        self.assertEqual(image_object, self.post.image)

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Noname'}))
        image_object = response.context['page_obj'][0].image
        self.assertEqual(image_object, self.post.image)

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        image_object = response.context['post'].image
        self.assertEqual(image_object, self.post.image)
