# Standard Library Imports
import os

# Django Imports
from django.shortcuts import render, redirect, HttpResponse
from django.http import FileResponse, HttpResponseForbidden,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage

# Models and Settings
from django.conf import settings

# Image Processing
import cv2
import base64

# Utility Imports
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

#Codes

from . import Backend

def generate_uidb64_token(user):
    '''
    Type   : Helper 
    Args   : Model of a User
    Job    : Encryt User Model into Base64, Create a Token
    Return : Base64 Encryption & Token
    '''
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk)) 
    token_generator = PasswordResetTokenGenerator() 
    token = token_generator.make_token(user)

    return uidb64, token

#Static Pages 

def Login(request):

    return render(request, "login.html")

class Logout(LogoutView):
    print("Logout")
    next_page = reverse_lazy('login')

def ResetPassword(request):

    return render(request,"forget.html")

# Request Handelers

def Login_Submit(request):
    if request.method == 'POST':
        employeeID = request.POST.get('emp-id')
        Password = request.POST.get('pass')
        User_details = authenticate(request, username=employeeID, password=Password)
        if User_details is not None:
            # User is there in the db
            login(request, User_details)
            request.session['id'] = employeeID
            return redirect('automl')
        else:
            # Authentication failed, Returning the error.
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def Form_Submit(request):
    '''
    Type    : HTTP POST Request
    ARGS    : Money and File details
    Purpose : Store the Details to the User DB.
    Return  : Success - Return to Success Page | False - return Error in Server Log.
    '''
    if request.method == 'POST':
        #Form submission
        # Yet to work
        house_price = request.POST.get('house-price')
        house_file = request.FILES.get('house-file')

        fees_price = request.POST.get("fees-price")
        fees_file = request.FILES.get('fees-file')

        travelling_price = request.POST.get("travel-price")
        travelling_file = request.FILES.get("travel-file")

        bus_fees = request.POST.get('bus-price')
        bus_file = request.FILES.get('bus-file')
        
        # Save form data to the database
        emp_id = request.session['id'] 
        info = User.objects.filter(username=emp_id).first()
        email = info.email
        name = info.first_name + " " + info.last_name
        document = Documents.objects.create(
            house_rent=house_price,
            house_file=house_file,
            fees=fees_price,
            fees_file=fees_file,
            travelling=travelling_price,
            travelling_file=travelling_file,
            bus=bus_fees,
            bus_file=bus_file,
            email=email,  
            emp_id=emp_id,  
            name=name 
        )

        # Return a response
        return render(request,'success.html')
    else:
        return HttpResponse("UnAuthorised Response")
    
#Main Routes
#  Home
def Home(request):
    # Handle the case when user or user Info not found
    return render(request,"pages/home.html")


#  Forget Password
def Reset_Password_Link(request, uidb64, token):
    '''
    Type    : HTTP GET & POST Request
    ARGS    : Base64 String, Token
    Purpose : Decrupt and Validate the token.
    Return  : Success - Return to Change Password Page | False - Return HTTPResponse stating Invalid Token.
    '''
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # Checking if the user exists and the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new-password')
            confirm_password = request.POST.get('confirm-password')
            if new_password == confirm_password:
                try:
                    validate_password(new_password)
                except ValidationError as error:
                    return render(request, 'PasswordReset.html', {'error': error})
                else:
                    # Setting the new password for the user
                    user.set_password(new_password)
                    user.save()
                    print("Password Changed Successfull")
                    logout(request)
                    return render(request,"login.html",{'success':'Password Changed Successfully'})
            else:
                # If passwords don't match
                return render(request, 'PasswordReset.html', {'error': 'Passwords do not match'})

        else:
            # If it's a GET request
            return render(request, 'PasswordReset.html')

    else:
        # If user or token is invalid
        return HttpResponse("Token Invalid")

#Forget Password 
def Forget_Password(request, template_name='Forget.html'):
    if request.method == 'POST':
        userid = request.POST.get("emp-id")
        print(userid)
        if User.objects.filter(username=userid).exists():
            # User exists, proceed with password reset
            user = User.objects.get(username=userid)
            email = user.email
            print(email)
            # Generate password reset token and send email
            uidb64,token = generate_uidb64_token(user)
            reset_url = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token}))
            send_mail(
                'Password Reset',
                f'Click the following link to reset your password: {reset_url}',
                'course.bytecamp@gmail.com',
                [email],
                fail_silently=False,
            )
            return render(request,"Forget.html",{'success':"Email Sent Successfully. Follow the instruction to reset Password."}) # Redirect to password reset done page
        else:
            return render(request,"Forget.html",{'error':"No User Found"})
    return render(request, template_name)

@login_required
def AutoML(request):
    return render(request,"pages/fileupload.html")

@login_required
def Dataset(request):
    import tempfile
    import joblib
    if request.method == 'POST':
        print(request.POST)
        label_name = request.POST.get('label')
        uploaded_file = request.FILES.get('filessss')  # Ensure the key matches the form input name attribute
        print(uploaded_file)
        
        if uploaded_file:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False,suffix=".csv")
            temp_file.write(uploaded_file.read())
            temp_file.close()

            # Get the temporary file path
            temp_file_path = temp_file.name
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            print(f"File Name: {file_name}")
            print(f"File Size: {file_size}")
            print(f"Label Name: {label_name}")
            print(f"Temp File Path: {temp_file_path}")
            
            # Call the AutoML tool with the temp file path and label
            best_model, accuracy, rmse,fileurl = Backend.automl_tool(temp_file_path, label_name, bins=5)

            # Clean up the temporary file
            data = {
        "best": best_model,
        "acc": accuracy,
        "rmse": rmse,
        "loc": fileurl
    }
            print(fileurl)

        return JsonResponse(data)
            
    else:
        return render(request,"pages/Final.html",{"best": 'Hi', "acc": '5454', 'rmse': '85487sjh',"loc":"shbhsbhgb.com"})
    
    return HttpResponse("Only POST requests are allowed.")
   