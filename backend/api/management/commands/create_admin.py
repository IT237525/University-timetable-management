from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create or update the default admin user"

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='Admin@123')
        parser.add_argument('--email', default='admin@example.com')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']
        email = options['email']
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        user.email = email
        user.role = 'admin'
        user.is_superuser = True
        user.is_staff = True
        user.set_password(password)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"Updated admin user: {username}"))

