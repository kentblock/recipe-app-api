from django.contrib.auth import get_user_model
from django.urls import reverse 
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')

class PublicIngredientApiTests(TestCase):
	"""Test publically available ingredient API"""

	def setUp(self):
		self.client = APIClient()

	def test_login_required(self):
		res = self.client.get(INGREDIENT_URL)
		self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateApiTests(TestCase):
	"""Test ingredients can be retrieved by authorized user"""

	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			'jonsnow@westeros.ca',
			'ghost'
		)
		self.client.force_authenticate(self.user)


	def test_retrieve_ingredient_list(self):
		"""Test retrieving ingredient list"""
		Ingredient.objects.create(user=self.user, name='Oatmeal')
		Ingredient.objects.create(user=self.user, name='Coconut')

		res = self.client.get(INGREDIENT_URL)

		ingredients = Ingredient.objects.all().order_by('-name')
		serializer = IngredientSerializer(ingredients, many=True)
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data, serializer.data)
		
	def test_ingredients_limited_to_user(self):
		"""Test only ingredients for authenticated user are returned"""

		user2 = get_user_model().objects.create_user(
			'sandor@chickens.ca',
			'ihatefire'
		)
		ingredient = Ingredient.objects.create(user=self.user, name='Oatmeal')
		Ingredient.objects.create(user=user2, name='chicken')
		
		res = self.client.get(INGREDIENT_URL)

		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(len(res.data), 1)
		self.assertEqual(res.data[0]['name'], ingredient.name)

	def test_create_ingredient_successful(self):
		"""Test creating ingredient is successful"""

		payload = {'name':'testingredient'}
		self.client.post(INGREDIENT_URL, payload)
		exists = Ingredient.objects.filter(
			user=self.user,
			name=payload['name']
		).exists()
		self.assertTrue(exists)


	def test_create_ingredient_invalid(self):
		"""Test creating new ingredient with invalid payload"""
		payload = {'name':''}
		res = self.client.post(INGREDIENT_URL, payload)
		self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

