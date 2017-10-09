from django.test import TestCase

from leagues.models import League, Payout

class PayoutTestCase(TestCase):

    def test_calculate_winner(self):
        league = League.objects.create(
            name='Test League'
        )
        payout = Payout.objects.create(
                league=league,
                name='Test Payout',
                amount=10,
                position=1,
                start_date='2017-08-01',
                end_date='2017-08-31',
                paid_out=False
        )

        with self.assertRaises(NotImplementedError):
            payout.calculate_winner()
