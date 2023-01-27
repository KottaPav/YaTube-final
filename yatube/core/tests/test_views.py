from django.test import Client, TestCase


class ProjectViewTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()

    def test_404_uses_correct_template(self):
        """URL-адрес страницы 404 использует соответствующий шаблон."""
        response = self.guest_client.get('/unexisting_pages/')
        self.assertTemplateUsed(response, 'core/404.html')
