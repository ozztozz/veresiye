from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Apartment, Transaction


class ApartmentModelTest(TestCase):
    def setUp(self):
        self.apartment = Apartment.objects.create(number='A01')

    def test_apartment_str(self):
        self.assertEqual(str(self.apartment), 'A01')

    def test_total_balance_no_transactions(self):
        self.assertEqual(self.apartment.total_balance(), 0)

    def test_total_debt_and_payment(self):
        user = User.objects.create_user(username='testuser', password='pass')
        Transaction.objects.create(
            apartment=self.apartment,
            amount=100,
            is_debt=True,
            created_by_name=user,
            updated_by_name=user,
        )
        Transaction.objects.create(
            apartment=self.apartment,
            amount=40,
            is_debt=False,
            created_by_name=user,
            updated_by_name=user,
        )
        self.assertEqual(self.apartment.total_debt(), 100)
        self.assertEqual(self.apartment.total_payment(), 40)
        self.assertEqual(self.apartment.total_balance(), 60)


class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

    def test_home_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_payment_waiting_view(self):
        response = self.client.get('/payment_waiting/')
        self.assertEqual(response.status_code, 200)

    def test_last_transactions_view(self):
        response = self.client.get('/last_transactions/')
        self.assertEqual(response.status_code, 200)

    def test_reports_view(self):
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)

    def test_apartment_detail_view_creates_apartment(self):
        response = self.client.get('/apartment/A99/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Apartment.objects.filter(number='A99').exists())
