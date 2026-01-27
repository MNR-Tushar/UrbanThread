from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser


class InventoryViewset(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'size', 'color']
    search_fields = ['product', 'size', 'color']
    ordering_fields = ['product', 'size', 'color', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve','check_availability']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        prouduct_id = request.query_params.get('product_id')
        color_id = request.query_params.get('color_id')
        size_id = request.query_params.get('size_id')
        
        if not all([prouduct_id, color_id, size_id]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory = Inventory.objects.get(
                product_id=prouduct_id, 
                color_id=color_id,
                size_id=size_id
            )
            serializer = self.get_serializer(inventory)
            return Response({
                'available': inventory.quantity > 0,
                'quantity': inventory.quantity,
                'inventory': serializer.data
            })
        except Inventory.DoesNotExist:
            return Response(
                {'available': False, 'quantity': 0},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def product_inventory(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory = Inventory.objects.filter(product_id=product_id)
        serializer = self.get_serializer(inventory, many=True)
        return Response(serializer.data)