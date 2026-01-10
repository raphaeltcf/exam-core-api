from rest_framework import serializers

from student.models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'email', 'username', 'name', 
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login',
            'is_staff', 'is_superuser'
        ]


class StudentCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="Senha do estudante (mínimo 8 caracteres)."
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirmação da senha."
    )

    class Meta:
        model = Student
        fields = [
            'id', 'email', 'username', 'name', 
            'password', 'password_confirmation', 'is_active'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'username': {'required': False}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirmation'):
            raise serializers.ValidationError({
                'password_confirmation': 'As senhas não coincidem.'
            })
        return attrs

    def validate_email(self, value):
        if Student.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email já está em uso.')
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        
        student = Student.objects.create_user(
            password=password,
            **validated_data
        )
        return student


class StudentUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        min_length=8,
        allow_blank=True,
        help_text="Nova senha (deixe em branco para não alterar)."
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        allow_blank=True,
        help_text="Confirmação da nova senha."
    )

    class Meta:
        model = Student
        fields = [
            'id', 'email', 'username', 'name', 
            'password', 'password_confirmation', 'is_active'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'username': {'required': False}
        }

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')
        
        if password or password_confirmation:
            if password != password_confirmation:
                raise serializers.ValidationError({
                    'password_confirmation': 'As senhas não coincidem.'
                })
        
        return attrs

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        
        if Student.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email já está em uso.')
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirmation', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
