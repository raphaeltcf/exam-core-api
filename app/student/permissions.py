from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão personalizada para permitir apenas ao dono do objeto editá-lo.
    Outros usuários têm permissão apenas de leitura.
    """

    def has_object_permission(self, request, view, obj):
        # Permissões de leitura são permitidas para qualquer requisição
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permissões de escrita são permitidas apenas ao dono do objeto
        return obj == request.user


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Permissão padrão do DRF: permite leitura para todos,
    escrita apenas para usuários autenticados.
    """
    pass
