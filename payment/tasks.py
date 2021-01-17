from io import BytesIO
from celery import task
import weasyprint
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from orders.models import Order

@task
def payment_completed(order_id):

     '''
     send email notification
     '''
     order=Order.objects.get(id=order_id)

     #create invoice email
     subject=f'NaVic - EE Invoice no. { order.id }'
     message='Recent Purchase Invoice is Given Below.'
     email=EmailMessage(subject,message,'navicstoreofficial@gmail.com',[order.email])

     #pdf section
     html=render_to_string('orders/order/pdf.html',{'order':order})
     out=BytesIO()
     stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
     weasyprint.HTML(string=html).write_pdf(out,stylesheets=stylesheets)

     #attaching
     email.attach(f'order_{order.id}.pdf',out.getvalue(),'application/pdf')

     #send email
     email.send()
