'''
this acts as security guard for API endpoints. By default, if a user is logged in, they can access any view. 
Without this, a Freelancer could technically hit the /api/hire/ endpoint and hire themselves, 
or a Client could "submit" work to skip paying.
it checks the roles in CustomUser model and if role not matched, 403 forbidden.
'''

from rest_framework import permissions

class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'

class IsFreelancer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'freelancer'
