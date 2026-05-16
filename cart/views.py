from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from inventory.models import Inventory
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product, Color, Size


# ─── Cache Key Helpers ────────────────────────────────────────────────────────

def _cart_key(user_id) -> str:
    return f"cart:{user_id}"


CART_CACHE_TTL = 60 * 5  # 5 minutes


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_or_create_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def _invalidate_cart_cache(self):
        cache.delete(_cart_key(self.request.user.id))

    # ─── My Cart ──────────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cache_key = _cart_key(request.user.id)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        cache.set(cache_key, serializer.data, timeout=CART_CACHE_TTL)
        return Response(serializer.data)

    # ─── Add Item ─────────────────────────────────────────────────────────────

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        try:
            product_id = int(request.data.get('product_id'))
            color_id   = int(request.data.get('color_id'))
            size_id    = int(request.data.get('size_id'))
            quantity   = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid product/color/size/quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )

        inventory = Inventory.objects.filter(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id
        ).first()

        if not inventory:
            return Response(
                {'error': 'This product variant is not available in inventory'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if inventory.quantity < quantity:
            return Response(
                {'error': 'Not enough stock', 'available_stock': inventory.quantity},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_or_create_cart()

        cart_item = CartItem.objects.filter(
            cart=cart,
            product_id=product_id,
            color_id=color_id,
            size_id=size_id
        ).first()

        if cart_item:
            if inventory.quantity < cart_item.quantity + quantity:
                return Response(
                    {'error': 'Not enough stock for this quantity', 'available_stock': inventory.quantity},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity += quantity
            cart_item.save()
            self._invalidate_cart_cache()
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        data = {
            'product_id': product_id,
            'color_id':   color_id,
            'size_id':    size_id,
            'quantity':   quantity,
        }
        serializer = CartItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)

        self._invalidate_cart_cache()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ─── Update Item ──────────────────────────────────────────────────────────

    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        item_id  = request.data.get('item_id')
        quantity = request.data.get('quantity')

        if not quantity or int(quantity) < 1:
            return Response(
                {'error': 'Quantity must be at least 1'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            inventory = Inventory.objects.get(
                product=cart_item.product,
                color=cart_item.color,
                size=cart_item.size
            )
        except Inventory.DoesNotExist:
            return Response(
                {'error': 'Product variant no longer available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if inventory.quantity < int(quantity):
            return Response(
                {'error': 'Not enough stock', 'available_stock': inventory.quantity},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = int(quantity)
        cart_item.save()

        self._invalidate_cart_cache()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    # ─── Remove Item ──────────────────────────────────────────────────────────

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        item_id = request.data.get('item_id')

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            self._invalidate_cart_cache()
            return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

    # ─── Clear Cart ───────────────────────────────────────────────────────────

    @action(detail=False, methods=['delete'])
    def clear_cart(self, request):
        cart = self.get_or_create_cart()
        cart.items.all().delete()  
        self._invalidate_cart_cache()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_204_NO_CONTENT)