from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SignUpTests(TestCase):
    def test_signup_hashes_password_and_logs_in(self):
        response = self.client.post(reverse("accounts:signup"), {
            "username": "masha", "email": "masha@example.com", "first_name": "Маша",
            "password1": "Very-Strong-Pass-42", "password2": "Very-Strong-Pass-42",
        })
        self.assertRedirects(response, reverse("catalog:home"))
        user = User.objects.get(username="masha")
        self.assertNotEqual(user.password, "Very-Strong-Pass-42")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertFalse(user.is_staff)

    def test_logout_requires_post(self):
        user = User.objects.create_user("u", password="pass12345!")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
