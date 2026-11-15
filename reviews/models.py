from django.db import models
from accounts.models import *
from products.models import *


class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    review_text = models.TextField()
    is_approved = models.BooleanField(default=False)
    verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewHelpfulVote(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='review_helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['review', 'user'], name='unique_helpful_vote_per_review_user')]
