from rest_framework.permissions import DjangoModelPermissions, BasePermission
from rest_framework import permissions


class ProjectDjangoModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


# class CustomDjangoModelPermissions(DjangoModelPermissions):
#     def __init__(self):
#         self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        if request.user.groups.filter(id=1).exists():
            return True
        return False


# from rest_framework.permissions import BasePermission

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        # Ensure the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        # Ensure user has the correct attribute
        return getattr(request.user, "is_adminuser", False)  # Avoid AttributeError

class IsAdminUser(BasePermission):

    def has_permission(self, request, view):

        return bool(request.user and request.user.is_adminuser)
    
class IsSuperuserOrEmployee(BasePermission):
    def has_permission(self, request, view):
        return isSuperuser().has_permission(request, view) or IsEmployee().has_permission(request, view)
    
class IsEmployeeOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return IsEmployee().has_permission(request, view) or IsCustomer().has_permission(request, view)


class IsCustomerUser(BasePermission):

    def has_permission(self, request, view):

        return bool(request.user and request.user.is_customer)


#         if (request.user):
#             return True
#         return False


class isSuperuser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


# Set Permission for Admin
class isAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_adminuser)


# Set Permission for Customer
class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_customer)
    

class AllowAnyOrIsEmployee(BasePermission):
    def has_permission(self, request, view):
        return permissions.AllowAny().has_permission(request, view) or IsEmployee().has_permission(request, view)