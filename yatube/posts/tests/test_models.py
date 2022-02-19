from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='к' * 20,
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у моделей  Group и Post корректно работает
         __str__."""
        str_post = PostModelTest.post.__str__()
        str_title = PostModelTest.group.__str__()
        self.assertEqual(str_post[:15], self.post.text[:15],
                         msg='Post text error!!!')
        self.assertEqual(str_title, self.group.title,
                         msg='Group title error!!!')
