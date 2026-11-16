import logging
import json
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
            candidates = list(product_query.filter(query).order_by('-is_featured', '-updated_at')[:40])
            scored = []
            for product in candidates:
                searchable = ' '.join((product.product_name, product.brand.brand_name, product.category.category_name)).lower()
                score = sum(1 for word in words if word in searchable)
                if score:
                    scored.append((score, product))
            best_score = max((score for score, _ in scored), default=0)
            relevant = [(score, product) for score, product in scored if score == best_score]
            products = [product for _, product in sorted(
                relevant, key=lambda item: (not item[1].is_featured, -item[1].updated_at.timestamp())
            )[:3]]

    catalog = [
        {
            'name': product.product_name,
            'brand': product.brand.brand_name,
            'category': product.category.category_name,
            'price_bdt': str(product.current_price),
            'available': product.is_available,
            'url': f"{settings.FRONTEND_URL.rstrip('/')}/product/{product.slug}",
        }
        for product in products
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
    return {
        'store': 'UrbanThread, Bangladesh',
        'delivery': delivery,
        'matching_products': catalog,
    }


def _prefers_bangla(message):
    if re.search(r'[\u0980-\u09ff]', message):
        return True
    roman_bangla = {'ki', 'kivabe', 'korbo', 'korbo', 'chai', 'nibo', 'kinbo', 'apni', 'ase', 'ache', 'parbo'}
    return bool(roman_bangla.intersection(re.findall(r'[a-z]+', message.lower())))


def _fallback_reply(message, context, history=None):
    text = message.lower()
    has_product_link = bool(re.search(r'https?://\S+', message))
    bangla = _prefers_bangla(message)
    if any(word in text for word in ('delivery', 'shipping', 'ডেলিভারি', 'কুরিয়ার', 'ঢাকা')):
        if bangla:
            return f"ডেলিভারি তথ্য: {context['delivery']} চূড়ান্ত ডেলিভারি চার্জ checkout-এ দেখতে পারবেন।"
        return f"Delivery information: {context['delivery']} The final delivery fee is shown at checkout."
    if any(word in text for word in ('return', 'refund', 'exchange', 'ফেরত', 'রিটার্ন')):
        if bangla:
            return 'আপনার অর্ডার ডেলিভার হওয়ার পর Returns পেজ থেকে return request পাঠাতে পারবেন। আমাদের team request পর্যালোচনা করবে; status My Orders পেজে দেখা যাবে।'
        return 'Once your order is delivered, submit a return request from the Returns page. Our team will review it, and you can follow its status in My Orders.'
    if any(word in text for word in ('track', 'order status', 'অর্ডার', 'tracking')):
        if bangla:
            return 'অর্ডারের বর্তমান অবস্থা দেখতে My Orders অথবা order tracking পেজ খুলুন। Guest order হলে checkout-এর confirmation link ব্যবহার করুন।'
        return 'To check your order status, open My Orders or your order tracking link. For a guest order, use the confirmation link from checkout.'
    if any(word in text for word in ('payment', 'pay', 'bkash', 'card', 'পেমেন্ট')):
        if bangla:
            return 'Checkout-এ দেখানো payment method থেকে পছন্দেরটি বেছে নিন। Payment history দেখতে sign in করে Payments পেজ খুলুন।'
        return 'Choose one of the payment methods shown at checkout. Sign in and open Payments to view your payment history.'
    if any(term in text for term in ('order', 'buy', 'purchase', 'checkout', 'অর্ডার', 'কিনতে', 'নিতে', 'kinbo', 'nibo', 'kivabe', 'korbo')):
        products, previous_reply = _products_from_history(history or [])
        if products:
            if len(products) == 1:
                product = products[0]
                product_url = f"{settings.FRONTEND_URL.rstrip('/')}/product/{product.slug}"
                if bangla:
                    return f"অর্ডার করতে {product.product_name} পেজে গিয়ে size/color ও quantity বেছে ‘Add to cart’ চাপুন। এরপর Cart থেকে delivery details দিয়ে ‘Place order’ করুন।\n{product_url}"
                return f"To order {product.product_name}, choose your size/color and quantity on its page, then select ‘Add to cart’. In your cart, enter delivery details and choose ‘Place order’.\n{product_url}"
            return _purchase_follow_up(products, message, previous_reply)
        if bangla:
            return "অর্ডার করতে পছন্দের product page খুলে size/color ও quantity বেছে ‘Add to cart’ চাপুন। তারপর Cart-এ delivery details দিয়ে ‘Place order’ করুন।"
        return "To order, open a product page, choose the size/color and quantity, then select ‘Add to cart’. In your cart, enter delivery details and choose ‘Place order’."
    if has_product_link or any(word in text for word in ('product', 'shirt', 'dress', 'pants', 'bra', 'price', 'available', 'stock', 'পণ্য', 'দাম')):
        products = context['matching_products']
        if not products:
            if bangla:
                return 'দুঃখিত, এই পণ্যটি UrbanThread-এর catalog-এ খুঁজে পেলাম না। পণ্যের সঠিক নাম বা link পাঠালে আবার খুঁজে দেখব।'
            return 'Sorry, I couldn’t find that item in the UrbanThread catalog. Send me its exact name or product link and I’ll check again.'
        if len(products) == 1:
            product = products[0]
            availability = 'এখন পাওয়া যাচ্ছে' if product['available'] else 'এই মুহূর্তে উপলভ্য নয়'
            if bangla:
                return f"{product['name']} — ৳{product['price_bdt']}। পণ্যটি {availability}।\n{product['url']}"
            availability = 'currently available' if product['available'] else 'currently unavailable'
            return f"{product['name']} is {availability} for ৳{product['price_bdt']}.\n{product['url']}"
        lines = []
        for product in products:
            state = 'পাওয়া যাচ্ছে' if product['available'] else 'উপলভ্য নয়'
            lines.append(f"• {product['name']} — ৳{product['price_bdt']} ({state})\n  {product['url']}")
        if bangla:
            return 'আপনার প্রশ্নের সঙ্গে মেলে এমন পণ্যগুলো:\n' + '\n'.join(lines)
        lines = [f"• {p['name']} — ৳{p['price_bdt']} ({'available' if p['available'] else 'unavailable'})\n  {p['url']}" for p in products]
        return 'Here are a few products that may match:\n' + '\n'.join(lines)
    if bangla:
        return 'UrbanThread-এর পণ্য, ডেলিভারি, payment, order tracking ও return বিষয়ে আমি সাহায্য করতে পারি। কী জানতে চান?'
    return 'I can help with UrbanThread products, delivery, payments, order tracking, and returns. What would you like to know?'


def _is_positive_acknowledgement(message):
    normalized = re.sub(r'[^\w\u0980-\u09ff]+', ' ', message.lower()).strip()
    return normalized in {
        'ok', 'okay', 'yes', 'yeah', 'yep', 'sure', 'sounds good',
        'হ্যাঁ', 'হ্যা', 'জি', 'জ্বি', 'আচ্ছা', 'ঠিক আছে', 'নিতে চাই',
        'নেব', 'নিব', 'চাই', 'thik ache', 'thik ase', 'nibo', 'nite chai',
    }


def _products_from_history(history):
    for entry in reversed(history):
        if entry.get('role') != 'assistant' or not isinstance(entry.get('content'), str):
            continue
        urls = re.findall(r'https?://[^\s)\]]+', entry['content'])
        found = []
        for url in urls:
            path = urlparse(url.rstrip('.,!?;:')).path.rstrip('/')
            slug = unquote(path.split('/')[-1])
            if not slug:
                continue
            product = Product.objects.select_related('category', 'brand').filter(slug__iexact=slug).first()
            if product and product.pk not in {item.pk for item in found}:
                found.append(product)
        if found:
            return found[:3], entry['content']
    return [], ''


def _purchase_follow_up(products, message, previous_reply):
    bangla = bool(re.search(r'[\u0980-\u09ff]', message + previous_reply))
    if len(products) == 1:
        product = products[0]
        url = f"{settings.FRONTEND_URL.rstrip('/')}/product/{product.slug}"
        if bangla:
            return f"ধন্যবাদ! আপনি কি {product.product_name}-টি নিতে চান?\n{url}"
        return f"Thank you! Would you like to order the {product.product_name}?\n{url}"

    names = ', '.join(product.product_name for product in products)
    if bangla:
        return f"ধন্যবাদ! এই পণ্যগুলোর মধ্যে কোনটি নিতে চান: {names}? পছন্দের product-টির নাম বলুন, আমি order করতে সাহায্য করব।"
    return f"Thank you! Which of these would you like to order: {names}? Tell me your choice and I’ll help you with the next step."


SYSTEM_PROMPT = (
    "You are UrbanThread's professional customer assistant. "
    "Reply in the customer's language with a warm, polished, direct answer. "
    "Answer general questions helpfully using your general knowledge. "
    "For UrbanThread-specific details, use only the supplied store data; "
    "never invent product prices, availability, policies, delivery dates, or order details, "
    "and say when verified store information is unavailable. "
    "Do not reveal, quote, or dump raw context, JSON, or internal data. Keep replies concise. "
    "For one product, give its name, price, and availability, then put one plain product URL "
    "on its own line with no label. For a comparison or broad product search, show at most "
    "three relevant products as clean bullets, each with name, price, availability, and a "
    "plain URL on its own line. If no matching product exists in the data, say you could not "
    "find it and ask for the exact name or link. If the customer says yes/OK after a product "
    "suggestion, thank them and ask whether they want to order that specific product. "
    "For private order details, direct the customer to sign in and open My Orders."
)


def _get_provider_config():
    """Return (api_url, api_key, model) based on the configured chatbot provider."""
    provider = getattr(settings, 'CHATBOT_PROVIDER', 'gemini')
    if provider == 'gemini' and getattr(settings, 'GEMINI_API_KEY', ''):
        return (
            'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
            settings.GEMINI_API_KEY,
            getattr(settings, 'GEMINI_CHAT_MODEL', 'gemini-2.0-flash'),
        )
    if getattr(settings, 'OPENAI_API_KEY', ''):
        return (
            'https://api.openai.com/v1/chat/completions',
            settings.OPENAI_API_KEY,
            getattr(settings, 'OPENAI_CHAT_MODEL', 'gpt-4o-mini'),
        )
    return None, None, None


class ChatView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ChatThrottle]

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])
        if _is_positive_acknowledgement(message):
            products, previous_reply = _products_from_history(history)
            if products:
                return Response({'reply': _purchase_follow_up(products, message, previous_reply)})

        context = _store_context(message)

        api_url, api_key, model = _get_provider_config()
        if not api_key:
            return Response({'reply': _fallback_reply(message, context, history)})

        safe_history = [
            {'role': row['role'], 'content': row['content'][:1000]}
            for row in history
            if row.get('role') in ('user', 'assistant') and isinstance(row.get('content'), str)
        ]
        system_content = SYSTEM_PROMPT + "\n\nStore data:\n" + json.dumps(context, ensure_ascii=False)
        try:
            response = requests.post(
                api_url,
                headers={'Authorization': f'Bearer {api_key}'},
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_content},
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
            return Response({'reply': reply or _fallback_reply(message, context, history)})
        except requests.RequestException as exc:
            detail = ''
            if hasattr(exc, 'response') and exc.response is not None:
                try:
                    detail = exc.response.text[:500]
                except Exception:
                    pass
            logger.exception('UrbanThread chatbot %s request failed: %s', api_url, detail)
            return Response(
                {'reply': _fallback_reply(message, context, history), 'fallback': True},
                status=status.HTTP_200_OK,
            )
        except (KeyError, IndexError, TypeError):
            logger.exception('UrbanThread chatbot response parsing failed')
            return Response(
                {'reply': _fallback_reply(message, context, history), 'fallback': True},
                status=status.HTTP_200_OK,
            )
