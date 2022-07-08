from django.contrib.auth.models import User
user = User.objects.create_user(username='supmit@gmail.com', email='supmit@gmail.com', password='password')


