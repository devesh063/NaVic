from decimal import Decimal
from django.conf import settings
from navic_part1.models import Product
from coupons.models import Coupon


class Cart(object):


    def __init__(self,request):

        """
        Intitialize the Cart
        """
        self.session=request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            #save an empty cart in the sessions
            cart=self.session[settings.CART_SESSION_ID]={}
        self.cart = cart

        #store current applied coupon
        self.coupon_id = self.session.get('coupon_id')

    def add(self,product,quantity=1,override_quantity=False):
        """
        Add a Product to the cart or update its quantity
        """
        product_id=str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity':0,'price':str(product.price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity']=quantity
        self.save()

    def save(self):
        #mark the session as modified to make sure it gets saved
        self.session.modified=True


    def remove(self,product):
       '''
       Remove a prodcut from the cart
       '''
       product_id=str(product.id)
       if product_id in self.cart:
           del self.cart[product_id]
           self.save()

    def  __iter__(self):
       '''
       Iterate over the items in the cart and get the Products
       '''
       product_ids=self.cart.keys()
       #get the product objects and add them to the Cart
       products=Product.objects.filter(id__in=product_ids)

       cart = self.cart.copy()
       for product in products:
           cart[str(product.id)]['product']=product

       for item in cart.values():
           item['price']=Decimal(item['price'])
           item['total_price']=item['price'] * item['quantity']
           yield item

    def __len__(self):
        """
        count all items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())
    def get_total_price(self):
        end_sum=sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
        return end_sum

    def clear(self):
        #remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()

    @property
    def coupon(self):
        if self.coupon_id:
            try:
               return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
               pass
        return None
    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        final_sum=self.get_total_price() - self.get_discount()
        if(final_sum<400):
            delivery_charge=30
            final_sum=final_sum+delivery_charge
        return final_sum

    def get_total_price_before_delivery(self):
        return self.get_total_price() - self.get_discount()
