from typing import Any
from blog.models import Category  # Make sure the model name is capitalized as per convention
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This command inserts category data"

    def handle(self, *args: Any, **options: Any):
        #Delete existing data
        Category.objects.all().delete()


        categories = ['sports', 'Technology', 'Science', 'Arts', 'Food']


    
     

        for category_name in categories:
            Category.objects.create(name = category_name)

        self.stdout.write(self.style.SUCCESS("Completed inserting Data!"))
