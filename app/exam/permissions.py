from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    pass
