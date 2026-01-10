from student.models import Student


class StudentService:

    @staticmethod
    def create_student(email: str, username: str, name: str, password: str, **extra_fields) -> Student:
        return Student.objects.create_user(
            email=email,
            username=username,
            name=name,
            password=password,
            **extra_fields
        )

    @staticmethod
    def update_student(student: Student, **kwargs) -> Student:
        if 'password' in kwargs:
            password = kwargs.pop('password')
            student.set_password(password)

        for field, value in kwargs.items():
            if hasattr(student, field):
                setattr(student, field, value)

        student.save()
        return student
    
    @staticmethod
    def get_or_create_student_by_email(email: str) -> tuple[Student, bool]:
        email = email.lower().strip()
        student, created = Student.objects.get_or_create(email=email,
            defaults={
                'username': email.split('@')[0] if '@' in email else email,
                'name': email.split('@')[0] if '@' in email else email,
                'is_active': True,
            }
        )
        return student, created
    
