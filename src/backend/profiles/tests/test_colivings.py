from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profiles.constants import Restrictions
from profiles.models import Coliving, ColivingTypes, Location, UserFromTelegram


class ColivingAPITest(APITestCase):
    """Тесты для проверки ресурса Coliving."""

    OWNER_1_TELEGRAM_ID = 111
    MSK_LOCATION_NAME = "Москва"
    OWNER_1_ABOUT = "Уютное пространство..."

    OWNER_2_TELEGRAM_ID = 222
    SPB_LOCATION_NAME = "Санкт-Петербург"

    UNKNOWN_LOCATION = "UNKNOWN_LOCATION"

    @classmethod
    def setUpTestData(cls):
        Coliving.objects.create(
            host=UserFromTelegram.objects.create(telegram_id=cls.OWNER_1_TELEGRAM_ID),
            price=Restrictions.PRICE_MIN,
            room_type=ColivingTypes.ROOM,
            location=Location.objects.create(name=cls.MSK_LOCATION_NAME),
            about=cls.OWNER_1_ABOUT,
        )
        Coliving.objects.create(
            host=UserFromTelegram.objects.create(telegram_id=cls.OWNER_2_TELEGRAM_ID),
            price=Restrictions.PRICE_MIN,
            room_type=ColivingTypes.ROOM,
            location=Location.objects.create(name=cls.SPB_LOCATION_NAME),
        )

    def test_create_coliving(self):
        """Тест на создание Coliving с валидными данными."""
        url = reverse("api-v1:profiles:colivings-list")
        data = {
            "host": self.OWNER_1_TELEGRAM_ID,
            "location": self.MSK_LOCATION_NAME,
            "price": Restrictions.PRICE_MAX,
            "room_type": ColivingTypes.ROOM,
            "about": "Some text",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_coliving_invalid_data(self):
        """Тест на создание Coliving с невалидными данными."""
        url = reverse("api-v1:profiles:colivings-list")
        data = {
            "host": self.OWNER_1_TELEGRAM_ID,
            "room_type": ColivingTypes.ROOM,
            "about": "Some text",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_coliving(self):
        """Тест на получение cписка Coliving."""
        url = reverse("api-v1:profiles:colivings-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_coliving_id(self):
        """Тест на получение данных Coliving."""
        url = reverse("api-v1:profiles:colivings-detail", args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_coliving(self):
        """Тест на обновление Coliving с валидными данными."""
        url = reverse("api-v1:profiles:colivings-detail", args=[1])
        data_list = [
            {"price": Restrictions.PRICE_MIN},
            {"price": Restrictions.PRICE_MAX},
        ]

        for data in data_list:
            with self.subTest(data=data):
                response = self.client.patch(
                    url,
                    data,
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_coliving__invalid_data(self):
        """Тест на обновление Coliving с невалидными данными."""
        url = reverse("api-v1:profiles:colivings-detail", args=[1])
        data = {"location": self.UNKNOWN_LOCATION}
        response = self.client.patch(
            url,
            data,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filters_coliving(self):
        """Тест на фильтрацию данных Coliving."""
        response = self.client.get(
            reverse("api-v1:profiles:colivings-list"),
            {
                "location": self.MSK_LOCATION_NAME,
                "room_type": ColivingTypes.ROOM,
                "min_price": Restrictions.PRICE_MIN,
                "max_price ": Restrictions.PRICE_MIN + 1,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {
                    "id": 1,
                    "host": self.OWNER_1_TELEGRAM_ID,
                    "location": self.MSK_LOCATION_NAME,
                    "price": Restrictions.PRICE_MIN,
                    "room_type": ColivingTypes.ROOM,
                    "about": self.OWNER_1_ABOUT,
                    "is_visible": True,
                    "images": [],
                }
            ],
        )
        self.assertEqual(len(response.data), 1)

    def test_filters_owner_coliving(self):
        """Тест на фильтрацию данных Coliving."""
        response = self.client.get(
            reverse("api-v1:profiles:colivings-list"),
            {"owner": self.OWNER_2_TELEGRAM_ID},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class UserResidenceUpdateAPITestCase(APITestCase):
    """
    Тестовые случаи для обновления информации о проживании пользователей.
    """

    OWNER_TELEGRAM_ID = 100
    INVALID_COLIVING_PK = 999
    LOCATION_NAME = "Москва"

    @classmethod
    def setUpTestData(cls):
        Coliving.objects.create(
            host=UserFromTelegram.objects.create(telegram_id=cls.OWNER_TELEGRAM_ID),
            price=Restrictions.PRICE_MIN,
            room_type=ColivingTypes.ROOM,
            location=Location.objects.create(name=cls.LOCATION_NAME),
        )

    def test_attach_user_to_coliving(self):
        """Тест на прикрепление пользователя к коливингу."""
        coliving = Coliving.objects.filter(
            host__telegram_id=self.OWNER_TELEGRAM_ID
        ).first()
        url = reverse(
            "api-v1:profiles:users-detail",
            kwargs={"telegram_id": self.OWNER_TELEGRAM_ID},
        )
        data = {"residence": coliving.id}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = UserFromTelegram.objects.get(telegram_id=self.OWNER_TELEGRAM_ID)
        self.assertEqual(user.residence.id, coliving.id)

    def test_detach_user_from_coliving(self):
        """Тест на открепление пользователя от коливинга."""
        user = UserFromTelegram.objects.get(telegram_id=self.OWNER_TELEGRAM_ID)
        user.residence = Coliving.objects.filter(
            host__telegram_id=self.OWNER_TELEGRAM_ID
        ).first()
        user.save()

        url = reverse(
            "api-v1:profiles:users-detail",
            kwargs={"telegram_id": self.OWNER_TELEGRAM_ID},
        )
        data = {"residence": None}
        response = self.client.patch(url, data)

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(user.residence)

    def test_update_with_invalid_telegram_id(self):
        """Тест обновления с невалидным telegram_id."""
        url = reverse(
            "api-v1:profiles:users-detail",
            kwargs={"telegram_id": self.INVALID_COLIVING_PK},
        )
        data = {"residence": 1}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_with_invalid_residence_id(self):
        """Тест обновления с невалидным residence_id."""
        user_telegram_id = self.OWNER_TELEGRAM_ID
        url = reverse(
            "api-v1:profiles:users-detail", kwargs={"telegram_id": user_telegram_id}
        )
        data = {"residence": self.INVALID_COLIVING_PK}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
