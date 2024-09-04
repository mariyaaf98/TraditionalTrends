from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import WishlistItem
from product_management.models import Product_Variant,Products
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Please log in to add items to your wishlist.'}, status=401)
    
    variant_id = request.POST.get('variant_id')
    if not variant_id:
        return JsonResponse({'status': 'error', 'message': 'No variant selected'}, status=400)
    
    try:
        product = get_object_or_404(Products, id=product_id)
        variant = get_object_or_404(Product_Variant, id=variant_id, product=product)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            variant=variant
        )
        
        if created:
            message = f"{product.product_name} - {variant.colour_name} added to your wishlist."
        else:
            message = f"{product.product_name} - {variant.colour_name} is already in your wishlist."
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': message})
        else:
            # For non-AJAX requests, redirect back to the referring page or to the product detail page
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id]))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        else:
            # Handle the error for non-AJAX requests
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id]))
    
@login_required
def remove_from_wishlist(request, wishlist_item_id):
    if request.method == 'POST':
        wishlist_item = get_object_or_404(WishlistItem, id=wishlist_item_id, user=request.user)
        product_name = wishlist_item.variant.product.product_name
        variant_color = wishlist_item.variant.colour_name
        
        wishlist_item.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': f'{product_name} - {variant_color} removed from your wishlist.'})
        
        messages.success(request, f'{product_name} - {variant_color} removed from your wishlist.')
        return redirect('wishlist:view-wishlist')
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)



@login_required
def view_wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('variant', 'variant__product')
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'user_side/view_wishlist.html', context)


