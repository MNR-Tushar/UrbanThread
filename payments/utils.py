import hashlib
import requests
from decimal import Decimal
from django.conf import settings
from typing import Dict, Optional


class SSLCommerzPayment:
    """
    SSL Commerce Payment Gateway Integration
    
    """
    
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_password = settings.SSLCOMMERZ_STORE_PASSWORD
        self.is_sandbox = settings.SSLCOMMERZ_IS_SANDBOX
        
        if self.is_sandbox:
            self.base_url = "https://sandbox.sslcommerz.com"
        else:
            self.base_url = "https://securepay.sslcommerz.com"
    
    def create_session(self, payment_data: Dict) -> Dict:
        """
        Create a payment session with SSL Commerce
        
        Args:
            payment_data: Dictionary containing payment information
            
        Returns:
            Dictionary with session response
        """
        url = f"{self.base_url}/gwprocess/v4/api.php"
        
        # Prepare the data
        data = {
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'total_amount': str(payment_data['total_amount']),
            'currency': payment_data.get('currency', 'BDT'),
            'tran_id': payment_data['tran_id'],
            'success_url': payment_data['success_url'],
            'fail_url': payment_data['fail_url'],
            'cancel_url': payment_data['cancel_url'],
            'ipn_url': payment_data.get('ipn_url', ''),
            
            # Customer Information
            'cus_name': payment_data['cus_name'],
            'cus_email': payment_data['cus_email'],
            'cus_phone': payment_data['cus_phone'],
            'cus_add1': payment_data.get('cus_add1', 'N/A'),
            'cus_city': payment_data.get('cus_city', 'Dhaka'),
            'cus_country': payment_data.get('cus_country', 'Bangladesh'),
            'cus_postcode': payment_data.get('cus_postcode', '1000'),
            
            # Shipment Information
            'shipping_method': payment_data.get('shipping_method', 'NO'),
            'ship_name': payment_data.get('ship_name', payment_data['cus_name']),
            'ship_add1': payment_data.get('ship_add1', payment_data.get('cus_add1', 'N/A')),
            'ship_city': payment_data.get('ship_city', payment_data.get('cus_city', 'Dhaka')),
            'ship_country': payment_data.get('ship_country', 'Bangladesh'),
            'ship_postcode': payment_data.get('ship_postcode', '1000'),
            
            # Product Information
            'product_name': payment_data.get('product_name', 'Order Payment'),
            'product_category': payment_data.get('product_category', 'general'),
            'product_profile': payment_data.get('product_profile', 'general'),
            
            # Optional Parameters
            'value_a': payment_data.get('value_a', ''),  # Can store order_id
            'value_b': payment_data.get('value_b', ''),
            'value_c': payment_data.get('value_c', ''),
            'value_d': payment_data.get('value_d', ''),
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def validate_payment(self, val_id: str, tran_id: str) -> Dict:
        """
        Validate a payment transaction
        
        Args:
            val_id: Validation ID from SSL Commerce
            tran_id: Transaction ID
            
        Returns:
            Dictionary with validation response
        """
        url = f"{self.base_url}/validator/api/validationserverAPI.php"
        
        params = {
            'val_id': val_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def refund_payment(self, bank_tran_id: str, refund_amount: Decimal, refund_remarks: str = '') -> Dict:
        """
        Initiate a refund for a transaction
        
        Args:
            bank_tran_id: Bank transaction ID
            refund_amount: Amount to refund
            refund_remarks: Reason for refund
            
        Returns:
            Dictionary with refund response
        """
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        
        data = {
            'refund_amount': str(refund_amount),
            'refund_remarks': refund_remarks,
            'bank_tran_id': bank_tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def transaction_query_by_tran_id(self, tran_id: str) -> Dict:
        """
        Query transaction status by transaction ID
        
        Args:
            tran_id: Transaction ID
            
        Returns:
            Dictionary with transaction details
        """
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        
        params = {
            'tran_id': tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def transaction_query_by_session_id(self, session_id: str) -> Dict:
        """
        Query transaction status by session ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with transaction details
        """
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        
        params = {
            'sessionkey': session_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def verify_hash(post_data: Dict) -> bool:
        """
        Verify the hash from IPN response
        
        Args:
            post_data: POST data from IPN
            
        Returns:
            Boolean indicating if hash is valid
        """
        if 'verify_sign' not in post_data or 'verify_key' not in post_data:
            return False
        
        verify_sign = post_data['verify_sign']
        verify_key = post_data['verify_key']
        
        # Create MD5 hash
        verify_sign_key = hashlib.md5(verify_key.encode()).hexdigest()
        
        return verify_sign == verify_sign_key