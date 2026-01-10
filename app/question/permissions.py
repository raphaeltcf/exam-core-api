from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Permissão padrão do DRF: permite leitura para todos,
    escrita apenas para usuários autenticados.
    """
    pass
