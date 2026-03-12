from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from .models import ComparisonSearch, ComparisonResult
from .scoring import parse_delivery_days, calculate_product_rating


class ScoringTestCase(TestCase):
    """Test scoring utility functions"""
    
    def test_parse_delivery_days_single(self):
        """Test parsing single day values"""
        self.assertEqual(parse_delivery_days("3 days"), 3)
        self.assertEqual(parse_delivery_days("5 business days"), 5)
        self.assertEqual(parse_delivery_days("7"), 7)
    
    def test_parse_delivery_days_range(self):
        """Test parsing day ranges (returns average)"""
        self.assertEqual(parse_delivery_days("3-5 days"), 4)
        self.assertEqual(parse_delivery_days("5-7 days"), 6)
    
    def test_parse_delivery_days_weeks(self):
        """Test parsing weeks"""
        self.assertEqual(parse_delivery_days("1 week"), 7)
        self.assertEqual(parse_delivery_days("2 weeks"), 14)
    
    def test_parse_delivery_days_default(self):
        """Test default value when parsing fails"""
        self.assertEqual(parse_delivery_days(None), 7)
        self.assertEqual(parse_delivery_days(""), 7)
        self.assertEqual(parse_delivery_days("unknown"), 7)
    
    def test_calculate_product_rating(self):
        """Test product rating calculation"""
        result = calculate_product_rating(
            price=950.0,
            min_price=900.0,
            delivery_days=3,
            store_stars=4.5
        )
        
        self.assertIn('final_score', result)
        self.assertIn('price_score', result)
        self.assertIn('delivery_score', result)
        self.assertIn('trust_score', result)
        
        # Check score ranges
        self.assertGreaterEqual(result['final_score'], 0)
        self.assertLessEqual(result['final_score'], 10)


class ComparisonModelsTestCase(TestCase):
    """Test comparison models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.search = ComparisonSearch.objects.create(
            user=self.user,
            query='iPhone 15',
            location='outside beirut',
            min_price=Decimal('950.00'),
            sites_checked=7,
            sites_succeeded=6
        )
    
    def test_comparison_search_creation(self):
        """Test ComparisonSearch model creation"""
        self.assertEqual(self.search.query, 'iPhone 15')
        self.assertEqual(self.search.user, self.user)
        self.assertEqual(self.search.sites_checked, 7)
    
    def test_comparison_result_creation(self):
        """Test ComparisonResult model creation"""
        result = ComparisonResult.objects.create(
            search=self.search,
            source='mobileleb',
            product_title='Apple iPhone 15 128GB',
            product_url='https://example.com/product',
            item_price=Decimal('950.00'),
            total_price=Decimal('954.00'),
            currency='USD',
            delivery_days=3,
            store_rating=Decimal('4.3'),
            score=Decimal('9.2'),
            price_score=Decimal('10.0'),
            delivery_score=Decimal('8.6'),
            trust_score=Decimal('8.6')
        )
        
        self.assertEqual(result.search, self.search)
        self.assertEqual(result.source, 'mobileleb')
        self.assertEqual(result.score, Decimal('9.2'))
    
    def test_comparison_search_ordering(self):
        """Test that searches are ordered by creation date (newest first)"""
        search2 = ComparisonSearch.objects.create(
            user=self.user,
            query='Samsung Galaxy',
            sites_checked=7,
            sites_succeeded=5
        )
        
        all_searches = list(ComparisonSearch.objects.all())
        self.assertEqual(all_searches[0], search2)  # Newest first
        self.assertEqual(all_searches[1], self.search)
