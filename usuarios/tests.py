from django.test import TestCase
from django.urls import reverse

from .models import Usuario, Post


class DeletePostViewTests(TestCase):
	def setUp(self):
		self.author = Usuario.objects.create(
			nome='Autor', telefone='123456', email='autor@example.com', senha='senha'
		)
		self.other_user = Usuario.objects.create(
			nome='Outro', telefone='654321', email='outro@example.com', senha='senha'
		)
		self.post = Post.objects.create(autor=self.author, texto='Post para deletar')

	def _login_as(self, user):
		session = self.client.session
		session['usuario_id'] = user.id
		session.save()

	def test_author_can_delete_post(self):
		self._login_as(self.author)
		response = self.client.post(reverse('delete_post', args=[self.post.id]))
		self.assertRedirects(response, reverse('social'))
		self.assertFalse(Post.objects.filter(id=self.post.id).exists())

	def test_non_author_cannot_delete_post(self):
		self._login_as(self.other_user)
		response = self.client.post(reverse('delete_post', args=[self.post.id]))
		self.assertRedirects(response, reverse('social'))
		self.assertTrue(Post.objects.filter(id=self.post.id).exists())


class UsernameGenerationTests(TestCase):
	def test_username_auto_generated_and_unique(self):
		first_user = Usuario.objects.create(
			nome='Joelyson Silva', telefone='111', email='joelyson@example.com', senha='senha'
		)
		second_user = Usuario.objects.create(
			nome='Joelyson Silva', telefone='222', email='joelyson2@example.com', senha='senha'
		)
		self.assertTrue(first_user.username)
		self.assertTrue(second_user.username)
		self.assertNotEqual(first_user.username, second_user.username)


class LoginWithUsernameTests(TestCase):
	def setUp(self):
		self.user = Usuario(nome='Maria', telefone='123', email='maria@example.com')
		self.user.set_password('segredo123')
		self.user.username = 'maria-000001'
		self.user.save()

	def test_login_using_handle_with_at_symbol(self):
		response = self.client.post(reverse('login'), {
			'email': '@maria-000001',
			'password': 'segredo123'
		})
		self.assertRedirects(response, reverse('dashboard'))
		self.assertEqual(self.client.session.get('usuario_id'), self.user.id)

	def test_login_using_handle_without_at_symbol(self):
		response = self.client.post(reverse('login'), {
			'email': 'maria-000001',
			'password': 'segredo123'
		})
		self.assertRedirects(response, reverse('dashboard'))
		self.assertEqual(self.client.session.get('usuario_id'), self.user.id)
