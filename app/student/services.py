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
