from django.contrib.auth.models import Group, Permission

def create_groups_permissions(sender, **kwargs):
    try:
        # Create groups
        readers_group, _ = Group.objects.get_or_create(name="Readers")
        authors_group, _ = Group.objects.get_or_create(name="Authors")
        editors_group, _ = Group.objects.get_or_create(name="Editors")

        # Create permissions
        readers_permissions = [
            Permission.objects.get(codename="view_post"),
        ]

        authors_permissions = [
            Permission.objects.get(codename="add_post"),
            Permission.objects.get(codename="change_post"),
            Permission.objects.get(codename="delete_post"),
        ]

        editors_permissions = [
            Permission.objects.get_or_create(codename="can_publish", content_type_id=7, name="Can Publish Post")[0],
            Permission.objects.get(codename="add_post"),
            Permission.objects.get(codename="change_post"),
            Permission.objects.get(codename="delete_post"),
        ]

        # Assigning the permissions to the groups
        readers_group.permissions.set(readers_permissions)
        authors_group.permissions.set(authors_permissions)
        editors_group.permissions.set(editors_permissions)

        print("Groups and permissions created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
