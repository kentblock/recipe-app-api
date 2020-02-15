from django.contrib.auth import get_user_model
from django.urls import reverse 
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
	"""Return recipe detail url"""
	return reverse('recipe:recipe-detail', args=[recipe_id])

def sample_tag(user, name='Main Course'):
	"""Create and return a sample tag"""
	return Tag.objects.create(user=user, name=name)

def sample_ingredient(user, name='Oregano'):
	"""Create and return a sample ingredient"""
	return Ingredient.objects.create(user=user, name=name)

def sample_recipe(user, **params):
	"""Create and return a sample recipe"""

	defaults = {
		'title':'Sample recipe',
		'time_minutes':10,
		'price':5.00
	}
	defaults.update(params)
	return Recipe.objects.create(user=user, **defaults)


class PublicApiTests(TestCase):
	"""Test unauthenticated API access"""

	def setUp(self):
		self.client = APIClient()

	def test_unauthorized_recipe_retrieval(self):
		"""Test that authentication is required"""
		res = self.client.get(RECIPE_URL)
		self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateApiTests(TestCase):
	"""Test authenticated API access"""

	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			'jonsnow@westeros.ca',
			'ghost'
		)
		self.client.force_authenticate(self.user)

	def test_recipe_retrieval(self):
		"""Test that authentication is required"""
		sample_recipe(self.user, title='Chicken Pot Pie')
		sample_recipe(self.user, title='Apple Crisp')

		res = self.client.get(RECIPE_URL)

		recipes = Recipe.objects.all().order_by('-id')
		serializer = RecipeSerializer(recipes, many=True)
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data, serializer.data)

	def test_recipe_limited_to_user(self):
		"""Retrieving recipes for user"""
		user2 = get_user_model().objects.create_user(
			'sandor@clegane.ca',
			'chickens'
		)

		sample_recipe(user=user2, title='chickens')
		sample_recipe(user=self.user, title='not chickens')

		res = self.client.get(RECIPE_URL)
		recipes = Recipe.objects.filter(user=self.user)
		serializer = RecipeSerializer(recipes, many=True)
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(len(res.data), 1)
		self.assertEqual(res.data, serializer.data)

	def test_view_recipe_detail(self):
		"""Test viewing a recipe detail"""
		recipe = sample_recipe(user=self.user)
		recipe.tags.add(sample_tag(user=self.user))
		recipe.ingredients.add(sample_ingredient(user=self.user))

		url = detail_url(recipe.id)

		res = self.client.get(url)
		serializer = RecipeDetailSerializer(recipe)
		self.assertEqual(res.data, serializer.data)

	def test_create_basic_recipe(self):
		"""Test for creating basic recipe with no tags and no ingredients"""
		payload = {
			'title':'Chocolate Cake',
			'time_minutes':30,
			'price':10.00
		}

		res = self.client.post(RECIPE_URL, payload)
		self.assertEqual(res.status_code, status.HTTP_201_CREATED)

		recipe = Recipe.objects.get(id=res.data['id'])
		for key in payload.keys():
			self.assertEqual(payload[key], getattr(recipe, key))

	def test_create_recipe_with_tags(self):
		"""Test for creating with tags, but no ingredients"""
		tag1 = sample_tag(self.user, name='Vegan')
		tag2 = sample_tag(self.user, name='Dessert')
		payload = {
			'title':'Key Lime Pie',
			'time_minutes':60,
			'price':20.00,
			'tags':[tag1.id, tag2.id]
		}

		res = self.client.post(RECIPE_URL, payload)
		self.assertEqual(res.status_code, status.HTTP_201_CREATED)

		recipe = Recipe.objects.get(id=res.data['id'])
		tags = recipe.tags.all()
		self.assertEqual(tags.count(), 2)
		self.assertIn(tag1, tags)
		self.assertIn(tag2, tags)

	def test_create_recipe_with_ingredients(self):
		"""Test creating recipe with ingredients"""
		ingredient1 = sample_ingredient(self.user, name='Carrot')
		ingredient2 = sample_ingredient(self.user, name='Sauce')

		payload = {
			'title':'Roasted Carrots',
			'time_minutes':20,
			'price':10.00,
			'ingredients':[ingredient1.id, ingredient2.id]
		}

		res = self.client.post(RECIPE_URL, payload)
		self.assertEqual(res.status_code, status.HTTP_201_CREATED)

		recipe = Recipe.objects.get(id=res.data['id'])
		ingredients = recipe.ingredients.all()
		self.assertEqual(ingredients.count(), 2)
		self.assertIn(ingredient1, ingredients)
		self.assertIn(ingredient2, ingredients)



