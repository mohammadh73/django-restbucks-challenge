from django.contrib.auth import get_user_model
from django.test import TestCase
from ..serializers import (
    ProductListSerializer, RegisterSerializer, ShowCartsSerializer
)
from core.products.models import Product

User = get_user_model()


class TestProductListSerializer(TestCase):
    fixtures = ['products']

    def setUp(self):
        self.serializer_class = ProductListSerializer

    def test_fields(self):
        """Make sure serializer data contains primary product's columns"""
        instance = self.serializer_class(instance=Product.objects.first())
        self.assertEqual(
            {'title', 'price', 'option', 'items'}, set(instance.data.keys())
        )

    def test_items(self):
        """Make sure items converted to python's list"""
        instance = self.serializer_class(instance=Product.objects.first())
        self.assertIsInstance(
            instance.data['items'], list
        )

    def test_collection(self):
        from collections import OrderedDict

        products = Product.objects.all()

        result = [OrderedDict({'title': p.title, 'price': p.price, 'option': p.option, 'items': p.items})
                  for p in products]
        self.assertEqual(
            self.serializer_class(products, many=True).data, result
        )


class RegisterSerializerTest(TestCase):
    class TestRegistrationSerializer(TestCase):
        @classmethod
        def setUpTestData(cls):
            cls.user = User.objects.create_user(username='foo@email.com',
                                                email='foo@email.com',
                                                password='Aa12456789')
            cls.serializer = RegisterSerializer(instance=cls.user)

        def test_fields(self):
            """
            Password field must be read only, so serializer data contains only email field.
            """
            self.assertEqual(
                {'email'}, set(self.serializer.data.keys())
            )

        def test_email_validation(self):
            """
             Make sure the email validator checks for email's uniqueness/pattern.
            """
            invalid_serializer = RegisterSerializer(data={'email': 'foo@email.com',
                                                          'password': 'Abc12345678'})
            self.assertFalse(
                invalid_serializer.is_valid()
            )

            invalid_serializer = RegisterSerializer(data={'password': 'Abc12345678'})
            self.assertFalse(invalid_serializer.is_valid())

            invalid_serializer = RegisterSerializer(data={'email': 'valid@email.com'})
            self.assertFalse(invalid_serializer.is_valid())

            valid_serializer = RegisterSerializer(data={'email': 'valid@email.com',
                                                        'password': 'Abc12345678'})
            self.assertTrue(
                valid_serializer.is_valid()
            )

        def test_password_validation(self):
            """
            Make sure the password validator doesnt accept passwords that contains
            less than 8 letters.
            """
            s = RegisterSerializer(data={'email': 'john@email.com',
                                         'password': '1234567'})
            self.assertFalse(
                s.is_valid()
            )

        def test_save(self):
            """
            Make sure serializer stores data correctly,
            e.g. doesnt store raw password.
            """
            data = {'email': 'johndoe@email.com',
                    'password': 'Abc123456789'}
            serializer = RegisterSerializer(data=data)
            serializer.save()

            self.assertNotEqual(
                data['password'], serializer.instance.password
            )


class ShowCartsSerializerTest(TestCase):
    def setUp(self):
        self.serializer_class = ShowCartsSerializer

    def test_fields(self):
        self.assertEqual({'count', 'total_price', 'products'},
                         set(self.serializer_class().fields.keys()))

    def test_product_fields(self):
        self.assertEqual({'title', 'price', 'option', 'selected_item', 'id'},
                         set(self.serializer_class.CartProductSerializer().fields.keys()))
