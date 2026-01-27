from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from inventory.models import Inventory
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product, Color, Size


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_or_create_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_or_create_cart()

        try:
            product_id = int(request.data.get('product_id'))
            color_id = int(request.data.get('color_id'))
            size_id = int(request.data.get('size_id'))
            quantity = int(request.data.get('quantity', 1))
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
                {
                    'error': 'Not enough stock',
                    'available_stock': inventory.quantity
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item = CartItem.objects.filter(
            cart=cart,
            product_id=product_id,
            color_id=color_id,
            size_id=size_id
        ).first()

        if cart_item:
            if inventory.quantity < cart_item.quantity + quantity:
                return Response(
                    {
                        'error': 'Not enough stock for this quantity',
                        'available_stock': inventory.quantity
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity += quantity
            cart_item.save()
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        data = {
            'product_id': product_id,
            'color_id': color_id,
            'size_id': size_id,
            'quantity': quantity
        }

        serializer = CartItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    
    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
            cart_item.quantity = quantity
            cart_item.save()
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
            cart_item.delete()
            return Response(
                {'message': 'Item removed from cart'},
                status=status.HTTP_204_NO_CONTENT
            )
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def clear_cart(self, request):
        cart = self.get_or_create_cart()
        cart.cartitem_set.all().delete()
        return Response(
            {'message': 'Cart cleared'},
            status=status.HTTP_204_NO_CONTENT
        )