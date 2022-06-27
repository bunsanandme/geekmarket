from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from account.models import User
from cart.models import Order, ProductsInOrder
from catalog.models import Product

import smtplib


def add_to_cart(request):
    global total_price
    path = request.GET.get('next')

    if request.method == 'POST':
        product_id = request.GET.get('product_id')

        if 'cart' not in request.session:
            request.session['cart'] = {}

        cart = request.session.get('cart')

        if product_id in cart:
            cart[product_id]['quantity'] += 1

        else:
            cart[product_id] = {
                'quantity': 1
            }

    request.session.modified = True
    return redirect(path)

products = {}

def view_cart(request):
    path = request.GET.get('next')

    context = {
        'next': path,
    }

    cart = request.session.get('cart', None)

    if cart:
        total_price = 0
        
        product_list = Product.objects.filter(pk__in=cart.keys()).values('id', 'title', 'description', 'price')

        for product in product_list:
            products[str(product['id'])] = product

        for key in cart.keys():
            cart[key]['product'] = products[key]
            total_price += product['price'] * cart[key]['quantity']

        context['cart'] = cart
        context['total_price'] = total_price
    return render(request, 'cart.html', context)


@login_required(login_url='login')
def view_order(request):
    if request.method == 'POST':
        user_id = request.user.pk
        customer = User.objects.get(pk=user_id)
        email = request.user.email
        cart = request.session['cart']


        if len(cart) > 0:
            order = Order.objects.create(customer=customer)

            for key, value in cart.items():
                product = Product.objects.get(pk=key)
                quantity = value['quantity']
                ProductsInOrder.objects.create(order=order, product=product, quantity=quantity)

            request.session['cart'] = {}
            request.session.modified = True
            email_text = "Спасибо, что выбрали наш магазин!\n\nВаш заказ включает: \n"
            for item in cart:
                product = Product.objects.get(pk=item)
                email_text += product.title
                email_text += ": "+ str(cart[item]['quantity']) + "шт \n"
            email_text += "\nС вами скоро свяжется наш менеджер по этому адресу электронной почты\n Хорошего дня :)"
            user = 'geekmarket2022@gmail.com'
            password = 'Geekmarket@1'
            subject = "Ваш заказ на Geekmarket"

            smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
            smtpObj.starttls()
            smtpObj.login(user, password)

            smtpObj.sendmail('geekmarket2022@gmail.com', email, email_text.encode('utf-8'))
            messages.success(request, 'Заказ принят')

    return redirect('cart:cart')
