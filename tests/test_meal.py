import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from meal.forms import MealForm
from meal.models import Meal, Cook, Category


URL_MEAL_LIST = reverse("meal:menu")
URL_MEAL_DETAIL = "meal:meal-detail"
URL_MEAL_UPDATE = "meal:meal-update"
URL_MEAL_CREATE = "meal:meal-create"
URL_MEAL_DELETE = "meal:meal-delete"
URL_COOK_LIST = reverse("meal:team")
URL_LOGIN = reverse("users:login")
TEST_CATEGORY_DATA = {"name": "LUNCH"}
TEST_MEAL_DATA = {
    "name": "Pizza",
    "description": "The pizza from Italia and is very delicious.",
    "people": "2",
    "price": "10.00",
    "preparation_time": "15",
    "image": "meal/pizza.jpg",
    "category_id": None,
    "slug": "pizza"
}


class MealListViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name="LUNCH")
        self.meal_pizza = Meal.objects.create(
            name="Pizza",
            description="The pizza from Italia and is very delicious.",
            people=2,
            price=10,
            preparation_time=15,
            image="meal/pizza.jpg",
            category_id=category.id,
            slug="pizza"
        )
        self.meal_pasta = Meal.objects.create(
            name="Pasta",
            description="The pasta from Italia and is very delicious.",
            people=2,
            price=10,
            preparation_time=15,
            image="meal/pasta.jpg",
            category_id=category.id,
            slug="pasta"
        )

    def test_meal_list_view_should_return_200(self):
        response = self.client.get(URL_MEAL_LIST)
        self.assertEqual(response.status_code, 200)

    def test_meal_list_view_should_contain_meal_list_in_context(self):
        response = self.client.get(URL_MEAL_LIST)
        self.assertContains(response, self.meal_pizza)
        self.assertIn("meal_list", response.context)

    def test_meal_search_by_name(self):
        response = self.client.get(URL_MEAL_LIST, data={"name": "Pasta"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.meal_pasta.name)
        self.assertNotContains(response, self.meal_pizza.name)

        response = self.client.get(URL_MEAL_LIST, data={"name": "Pizza"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.meal_pizza.name)
        self.assertNotContains(response, self.meal_pasta.name)


class MealDetailViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(**TEST_CATEGORY_DATA)
        TEST_MEAL_DATA["category_id"] = category.id
        self.meal = Meal.objects.create(**TEST_MEAL_DATA)

    def test_meal_detail_view_should_return_200(self):
        response = self.client.get(reverse(URL_MEAL_DETAIL, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 200)

    def test_meal_detail_view_should_contain_meal_in_context(self):
        response = self.client.get(reverse(URL_MEAL_DETAIL, args=[self.meal.slug]))
        self.assertContains(response, self.meal)
        self.assertIn("meal", response.context)


class MealUpdateViewTest(TransactionTestCase):
    def setUp(self):
        category = Category.objects.create(**TEST_CATEGORY_DATA)
        TEST_MEAL_DATA["category_id"] = category.id
        self.meal = Meal.objects.create(**TEST_MEAL_DATA)

        self.admin_user = get_user_model().objects.create_superuser(username="Adminuser", password="testpassword")
        self.other_user = get_user_model().objects.create_user(username="Otheruser", password="testpassword")

    def test_meal_update_view_should_return_302_for_anonymous_user(self):
        response = self.client.get(reverse(URL_MEAL_UPDATE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 302)

    def test_meal_update_view_should_return_403_for_is_not_superuser(self):
        self.client.login(username="Otheruser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_UPDATE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 403)

    def test_meal_update_view_should_return_200_for_authenticated_superuser(self):
        self.client.login(username="Adminuser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_UPDATE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 200)

    def test_meal_update_view_should_update_meal_for_authenticated_superuser(self):
        self.client.login(username="Adminuser", password="testpassword")
        image_name = "test_image.png"
        image_path = f"media/{image_name}"

        image_file = SimpleUploadedFile(name=f"meal/{image_name}", content=open(image_path, "rb").read(),
                                        content_type="image/jpeg")

        new_name = "Pizza_updated"
        form_data = {
            "name": new_name,
            "description": self.meal.description,
            "people": "2",
            "price": "10.00",
            "preparation_time": "15",
            "category": str(self.meal.category.id),
            "slug": self.meal.slug,
        }

        form = MealForm(form_data, instance=self.meal, files={"image": image_file})

        response = self.client.post(
            reverse(URL_MEAL_UPDATE, args=[self.meal.slug]),
            data=form.data,
            files=form.files,
        )
        if form.is_valid():
            form.save()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(URL_MEAL_DETAIL, args=[self.meal.slug]))
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.name, new_name)
        self.assertEqual(self.meal.image.name, f"meal/{image_name}")
        self.assertEqual(self.meal.image.name, f"meal/{image_file.name}")

        os.remove(self.meal.image.path)


class MealCreateViewTest(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(username="Adminuser", password="testpassword")
        self.other_user = get_user_model().objects.create_user(username="Otheruser", password="testpassword")

    def test_meal_create_view_should_return_302_for_anonymous_user(self):
        response = self.client.get(reverse(URL_MEAL_CREATE))
        self.assertEqual(response.status_code, 302)

    def test_meal_create_view_should_return_403_for_is_not_superuser(self):
        self.client.login(username="Otheruser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_CREATE))
        self.assertEqual(response.status_code, 403)

    def test_meal_create_view_should_return_200_for_authenticated_superuser(self):
        self.client.login(username="Adminuser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_CREATE))
        self.assertEqual(response.status_code, 200)

    def test_meal_create_view_should_redirect_to_login_for_anonymous_user(self):
        response = self.client.post(reverse(URL_MEAL_CREATE), {})
        self.assertRedirects(response, URL_LOGIN + "?next=" + reverse(URL_MEAL_CREATE))

    def test_meal_create_view_should_create_meal_for_authenticated_superuser(self):
        self.client.login(username="Adminuser", password="testpassword")

        self.client.handler_class = MemoryFileUploadHandler
        image_path = "media/test_image.png"
        image_file = SimpleUploadedFile(name="meal/test_image.png", content=open(image_path, "rb").read(),
                                        content_type="image/jpeg")

        category = Category.objects.create(name="LUNCH")

        form_data = {
            "name": "Pizza",
            "description": "The pizza from Italia and is very delicious.",
            "people": "2",
            "price": "10.00",
            "preparation_time": "15",
            "image": image_file,
            "category": category.id,
            "slug": "pizza",
        }

        response = self.client.post(reverse(URL_MEAL_CREATE), data=form_data)

        new_meal = Meal.objects.filter(name=form_data["name"])
        current_meal = Meal.objects.get(name=form_data.get("name"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(new_meal.exists())

        os.remove(current_meal.image.path)

    def test_meal_create_form_validation_date_time(self):
        self.client.login(username="Adminuser", password="testpassword")

        self.client.handler_class = MemoryFileUploadHandler
        image_path = "media/test_image.png"
        image_file = SimpleUploadedFile(name="meal/test_image.png", content=open(image_path, "rb").read(),
                                        content_type="image/jpeg")

        form_data = {
            "name": "Pizza",
            "description": "The pizza from Italia and is very delicious.",
            "people": "2",
            "price": "10.00",
            "preparation_time": "15",
            "category": Category.objects.create(name="LUNCH").id,
            "slug": "pizza",
        }

        form = MealForm(form_data, files={"image": image_file})
        self.assertTrue(form.is_valid())

        form_data["price"] = "0.00"
        form = MealForm(form_data, files={"image": image_file})
        self.assertFalse(form.is_valid())

        form_data["price"] = "-1.00"
        form = MealForm(form_data, files={"image": image_file})
        self.assertFalse(form.is_valid())


class MealDeleteViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(**TEST_CATEGORY_DATA)
        TEST_MEAL_DATA["category_id"] = category.id
        self.meal = Meal.objects.create(**TEST_MEAL_DATA)

        self.admin_user = get_user_model().objects.create_superuser(username="Adminuser", password="testpassword")
        self.other_user = get_user_model().objects.create_user(username="Otheruser", password="testpassword")

    def test_meal_delete_view_should_return_302_for_anonymous_user(self):
        response = self.client.get(reverse(URL_MEAL_DELETE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 302)

    def test_meal_delete_view_should_return_403_for_is_not_superuser(self):
        self.client.login(username="Otheruser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_DELETE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 403)

    def test_meal_delete_view_should_return_200_for_authenticated_superuser(self):
        self.client.login(username="Adminuser", password="testpassword")
        response = self.client.get(reverse(URL_MEAL_DELETE, args=[self.meal.slug]))
        self.assertEqual(response.status_code, 200)

    def test_meal_delete_view_should_redirect_to_login_for_anonymous_user(self):
        response = self.client.post(reverse(URL_MEAL_DELETE, args=[self.meal.slug]), {})
        self.assertRedirects(response, URL_LOGIN
                             + "?next="
                             + reverse(URL_MEAL_DELETE, args=[self.meal.slug]))

    def test_meal_delete_view_should_delete_meal_for_authenticated_user(self):
        self.client.login(username="Adminuser", password="testpassword")
        response = self.client.post(reverse(URL_MEAL_DELETE, args=[self.meal.slug]), {})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Meal.objects.filter(slug=self.meal.slug).exists())


class CookListViewTest(TestCase):
    def test_cook_list_view_should_return_200(self):
        response = self.client.get(URL_COOK_LIST)
        self.assertEqual(response.status_code, 200)

    def test_cook_list_view_should_contain_cook_list_in_context(self):
        cook = Cook.objects.create(
            first_name="Test",
            last_name="Cook",
            about="Some Chef",
            position="Chef",
            image="cooker/team1.jpg"
        )
        response = self.client.get(URL_COOK_LIST)
        self.assertContains(response, f"{cook.first_name} {cook.last_name}")
        self.assertIn("cook_list", response.context)
