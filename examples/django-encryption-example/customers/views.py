from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect

from django import forms

# Create your views here.
from customers.models import Customer


class CustomerForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    phone = forms.CharField(label='Phone', max_length=100)
    ssn = forms.CharField(label='SSN', max_length=100)
    dob = forms.DateField(label='DOB')
    state = forms.CharField(label='State', max_length=100)


def index(request, errors=None):
    # get all customers
    customers = list(Customer.objects.transform("mask", Customer.ssn).all())
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
    customer.ssn = request.POST['ssn']
    customer.dob = request.POST['dob']
    customer.state = request.POST['state']
    customer.save()
    # now redirect to the index page
    return redirect('index')
