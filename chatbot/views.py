import logging
import re
from urllib.parse import unquote, urlparse

import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from products.models import DeliveryZone, Product, StoreSettings

logger = logging.getLogger(__name__)


class ChatThrottle(AnonRateThrottle):
    scope = 'chatbot'


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, allow_blank=False, trim_whitespace=True)
    history = serializers.ListField(
        child=serializers.DictField(), required=False, max_length=10
    )


def _store_context(message):
    product_query = Product.objects.select_related('category', 'brand')
    url_match = re.search(r'https?://[^\s]+', message)
    slug = ''
    if url_match:
        path = urlparse(url_match.group(0).rstrip('.,!?)]}')).path.rstrip('/')
        slug = unquote(path.split('/')[-1]).lower()

    products = []
    if slug:
        exact = product_query.filter(slug__iexact=slug).first()
        if exact:
            products = [exact]

    if not products:
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'product', 'item',
            'price', 'available', 'availability', 'stock', 'please', 'what',
            'is', 'are', 'it', 'ai', 'asa', 'ache', 'ase', 'assa', 'er',
            'app', 'vercel', 'urbanthreadshop',
        }
        search_text = slug.replace('-', ' ') if slug else message.lower()
        words = [
            word for word in re.findall(r'[a-z0-9]+', search_text)
            if len(word) > 1 and word not in stop_words
        ]
        # URL paths contain the exact product slug, so use its words even if
        # the rest of the customer's message is in Bangla.
        if slug:
            words.extend(word for word in slug.split('-') if len(word) > 1)
        words = list(dict.fromkeys(words))[:10]
        if words:
            query = Q()
            for word in words:
                query |= (
                    Q(product_name__icontains=word)
                    | Q(slug__icontains=word)
                    | Q(description__icontains=word)
                    | Q(category__category_name__icontains=word)
                    | Q(brand__brand_name__icontains=word)
                )
            products = list(product_query.filter(query).order_by('-is_featured', '-updated_at')[:8])

    catalog = [
        f"{p.product_name} (brand: {p.brand.brand_name}, category: {p.category.category_name}) — ৳{p.current_price}; {'available' if p.is_available else 'unavailable'}; product URL: {settings.FRONTEND_URL.rstrip('/')}/product/{p.slug}"
        for p in products
    ]
    store = StoreSettings.objects.first()
    zones = list(DeliveryZone.objects.filter(is_active=True).values_list('name', 'delivery_fee')[:20])
    if store:
        delivery = (
            f"Dhaka ৳{store.dhaka_delivery_fee}; outside Dhaka ৳{store.outside_delivery_fee}; "
            f"free shipping for orders over ৳{store.free_shipping_threshold}."
        )
    else:
        delivery = 'Delivery fee and free shipping threshold are shown at checkout.'
    if zones:
        delivery += ' Specific delivery zones: ' + ', '.join(f'{name} ৳{fee}' for name, fee in zones) + '.'
    return f"Store: UrbanThread, Bangladesh. Delivery: {delivery}\nMatching catalog items: " + ('; '.join(catalog) if catalog else 'No matching products found.')


def _fallback_reply(message, context):
    text = message.lower()
    has_product_link = bool(re.search(r'https?://\S+', message))
    if any(word in text for word in ('delivery', 'shipping', 'ডেলিভারি', 'কুরিয়ার', 'ঢাকা')):
        return f"Delivery information: {context.split('Delivery: ', 1)[1].split(chr(10), 1)[0]} You can see the final fee at checkout."
    if any(word in text for word in ('return', 'refund', 'exchange', 'ফেরত', 'রিটার্ন')):
        return 'Delivered order হলে Returns page থেকে return request submit করুন। Store team request review করবে; refund approval/status সম্পর্কে order page-এ update দেখুন।'
    if any(word in text for word in ('track', 'order status', 'অর্ডার', 'tracking')):
        return 'আপনার order status দেখতে My Orders বা order tracking page খুলুন। Guest order হলে checkout-এর confirmation link ব্যবহার করুন।'
    if any(word in text for word in ('payment', 'pay', 'bkash', 'card', 'পেমেন্ট')):
        return 'Checkout-এ উপলভ্য payment method বেছে নিন। Payment history দেখতে sign in করে Payments page খুলুন।'
    if has_product_link or any(word in text for word in ('product', 'shirt', 'dress', 'pants', 'bra', 'price', 'available', 'stock', 'পণ্য', 'দাম')):
        matches = context.split('Matching catalog items: ', 1)[1]
        if matches == 'No matching products found.':
            return 'এই product-টি UrbanThread catalog-এ খুঁজে পাচ্ছি না। Product name বা link-টি আবার মিলিয়ে পাঠাবেন? You can also browse all products on the store page.'
        return 'Catalog-এ যা পেয়েছি: ' + matches
    return 'আমি UrbanThread-এর product, price, delivery, payment, order tracking এবং return বিষয়ে সাহায্য করতে পারি। নির্দিষ্ট প্রশ্নটি আরেকটু বিস্তারিত লিখুন।'


class ChatView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ChatThrottle]

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']
        context = _store_context(message)

        if not settings.OPENAI_API_KEY:
            return Response({'reply': _fallback_reply(message, context)})

        history = serializer.validated_data.get('history', [])
        safe_history = [
            {'role': row['role'], 'content': row['content'][:1000]}
            for row in history
            if row.get('role') in ('user', 'assistant') and isinstance(row.get('content'), str)
        ]
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {settings.OPENAI_API_KEY}'},
                json={
                    'model': settings.OPENAI_CHAT_MODEL,
                    'messages': [
                        {'role': 'system', 'content': 'You are UrbanThread customer support. Reply clearly in the customer\'s language (Bangla or English). Answer only using the store facts and catalog context below. Never invent stock, policies, delivery dates, or order details. For private order help, direct the customer to sign in and use My Orders. Keep answers concise.\n\n' + context},
                        *safe_history,
                        {'role': 'user', 'content': message},
                    ],
                    'temperature': 0.3,
                    'max_tokens': 300,
                },
                timeout=20,
            )
            response.raise_for_status()
            reply = response.json()['choices'][0]['message']['content'].strip()
            return Response({'reply': reply or _fallback_reply(message, context)})
        except (requests.RequestException, KeyError, IndexError, TypeError):
            logger.exception('UrbanThread chatbot provider request failed')
            return Response(
                {'reply': _fallback_reply(message, context), 'fallback': True},
                status=status.HTTP_200_OK,
            )
