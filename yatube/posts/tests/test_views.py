import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Follow, Post, User
from ..utils import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POSTS_FOR_TEST = 15


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='HasNoName'
        )
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_url_notauthorized_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}): 'posts/'
                                                            'group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user.username}'}): 'posts/'
                                                       'profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}): 'posts/'
                                                            'post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)

    def test_url_authorized_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        address = reverse('posts:post_create')
        template = 'posts/post_create.html'
        response = self.authorized_client.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, 200)

    def test_url_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        address = reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{self.post.id}'}
        )
        template = 'posts/post_create.html'
        response = self.authorized_client_author.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, 200)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = (self.guest_client.get(reverse('posts:index')))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.author}'}
        )))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'}
        )))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})))
        self.assertIn('post', response.context)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(reverse(
            "posts:post_edit", kwargs={"post_id": self.post.id}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly_new_user(self):
        """Пост при создании виден на главной, в группе и профиле,
        но не появляется у других."""
        cache.clear()
        post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group)
        responces = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'})
        )
        for responce in responces:
            post_list = self.authorized_client.get(responce)
            page_object = post_list.context['page_obj']
            self.assertIn(post, page_object)

    def test_cache_index(self):
        """Проверка кэша. При удалении запись остается до очистки кэша."""
        posts1 = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.filter(id=1).delete()
        posts2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertTrue(posts1 == posts2)
        cache.clear()
        posts3 = self.authorized_client.get(reverse('posts:index')).content
        self.assertFalse(posts1 == posts3)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='HasNoName'
        )
        cls.author = User.objects.create_user(
            username='Автор'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(POSTS_FOR_TEST):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.author,
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()

    def test_correct_paginator(self):
        """Проверка работы paginator на страницах проекта."""
        cache.clear()
        pages = (reverse('posts:index'),
                 reverse('posts:profile',
                         kwargs={'username': f'{self.author}'}),
                 reverse('posts:group_list',
                         kwargs={'slug': f'{self.group.slug}'}))
        for page in pages:
            with self.subTest(page=page):
                response_p1 = self.guest_client.get(page)
                response_p2 = self.guest_client.get(page + '?page=2')
                count_posts_p1 = len(response_p1.context['page_obj'])
                count_posts_p2 = len(response_p2.context['page_obj'])
                self.assertEqual(count_posts_p1, POSTS_PER_PAGE)
                self.assertEqual(count_posts_p2,
                                 POSTS_FOR_TEST - POSTS_PER_PAGE)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.following = User.objects.create_user(username='Автор')
        cls.follower = User.objects.create_user(username='Подписчик')
        cls.post = Post.objects.create(
            author=cls.following,
            text='Тестовый текст'
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.following)
        self.follower_client.force_login(self.follower)

    def test_follow(self):
        """Проверка подписки."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following}
        ))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Проверка отписки."""
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following}
        ))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_following_post_display(self):
        """Пост появляется на странице подписчиков."""
        posts = self.post
        follow = Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response2.context['page_obj']), 0)
