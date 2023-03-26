from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect

from django import forms

# Create your views here.
from customers.models import Customer

from django_encryption.fields import transform


class CustomerForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    phone = forms.CharField(label='Phone', max_length=100)
    address = forms.CharField(label='Address', max_length=100)
    ssn = forms.CharField(label='SSN', max_length=100)
    dob = forms.DateField(label='DOB')


def index(request, errors=None):
    # get all customers
    with transform("mask", Customer.ssn):
        customers = list(Customer.objects.all())
    # render the index template and pass in the customers
    return render(request, 'index.html', dict(customers=customers, add_customer_form=CustomerForm(), errors=errors))


@require_POST
def add_customer(request):
    # create a new customer object and save it
    form = CustomerForm(request.POST)
    if not form.is_valid():
        return redirect('index', errors=form.errors)
    customer = Customer()
    customer.name = request.POST['name']
    customer.email = request.POST['email']
    customer.phone = request.POST['phone']
    customer.address = request.POST['address']
    customer.ssn = request.POST['ssn']
    customer.dob = request.POST['dob']
    customer.save()
    # now redirect to the index page
    return redirect('index')
