from django.shortcuts import render,redirect,get_object_or_404
import razorpay
from django.conf import settings
from orders.models import Order
from .tasks import payment_completed

# Create your views here.

#instantiate razorpay payment gateway
client =razorpay.Client(auth=("rzp_test_y5Sw2cGztVnW9u","6YKNBmwSmtnUyRz1tc6a0pou"))


def payment_process(request):
    context={}
    order_id=request.session.get('order_id')
    order=get_object_or_404(Order,id=order_id)
    total_cost=order.get_total_cost()
    if(total_cost<400):
        total_cost=total_cost+30   # adding delivery charges 
    total_cost=int(total_cost*100)

    order_currency='INR'
    order_receipt='order_receipt'+str(order)
    #CREATING ORDER
    response=client.order.create(dict(amount=total_cost,currency=order_currency,receipt=order_receipt))
    order_no=response['id']
    order_status=response['status']

    if order_status=='created':
        context['order_number']=order
        context['price']=total_cost
        context['order_nos']=order_no
        return render(request,'payment/process.html',context)

    return render(request,'payment/canceled.html')


def payment_status(request):
    order_id=request.session.get('order_id')
    order=get_object_or_404(Order,id=order_id)
    response = request.POST
    params_dict = {'razorpay_payment_id':response['razorpay_payment_id'],
                    'razorpay_order_id':response['razorpay_order_id'],
                    'razorpay_signature':response['razorpay_signature']

                  }

    try:
        status=client.utility.verify_payment_signature(params_dict)
        order.paid=True
        order.razorpay_id=response['razorpay_payment_id']
        payment_completed.delay(order.id)
        order.save()
        return render(request,'payment/done.html',{'status':'Payment Successful'})
    except:
        order.paid=False
        order.save()
        return render(request,'payment/canceled.html',{'status':'Payment Unsuccessful'})
