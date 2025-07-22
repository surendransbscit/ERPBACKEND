from rest_framework import serializers
from .models import ProjectCreate, TaskCreation, subtask, EmployeeAttendance, PerformanceInvoice, PerformanceInvoiceDetails, ErpEmployeeAttendanceDetails, ErpEmployeeAttendance
from employees.models import Employee

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCreate
        fields = '__all__'


class TaskCreationSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    class Meta:
        model = TaskCreation
        fields = '__all__'
    def get_status_display(self, obj):
        return obj.get_status_display()


class SubTaskSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    class Meta:
        model = subtask
        fields = '__all__'
    def get_status_display(self, obj):
        return obj.get_status_display()


class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendance
        fields = '__all__'

class PerformanceInvoiceDetailsSerializer(serializers.ModelSerializer):
    id_module = serializers.IntegerField()
    payment_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    class Meta:
        model = PerformanceInvoiceDetails
        fields = '__all__'

class PerformanceInvoiceSerializer(serializers.ModelSerializer):
    id_module = PerformanceInvoiceDetailsSerializer(many=True, write_only=True, required=False)
    class Meta:
        model =PerformanceInvoice
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class ErpEmployeeAttendanceDetailsSerializer(serializers.ModelSerializer):
    id_employee_detail = EmployeeSerializer(source='id_employee', read_only=True)

    class Meta:
        model = ErpEmployeeAttendanceDetails
        fields = '__all__'
        extra_kwargs = {'id_erp_employee_attendance': {'read_only': True}}

class ErpEmployeeAttendanceSerializer(serializers.ModelSerializer):
    attendance_details = ErpEmployeeAttendanceDetailsSerializer(many=True)

    class Meta:
        model = ErpEmployeeAttendance
        fields = '__all__'

    def create(self, validated_data):
        details_data = validated_data.pop('attendance_details', [])
        attendance = ErpEmployeeAttendance.objects.create(**validated_data)
        for detail in details_data:
            ErpEmployeeAttendanceDetails.objects.create(
                id_erp_employee_attendance=attendance,
                **detail
            )
        return attendance
    
    def update(self, instance, validated_data):
        details_data = validated_data.pop('attendance_details', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.attendance_details.all().delete()
        for detail in details_data:
            ErpEmployeeAttendanceDetails.objects.create(
                id_erp_employee_attendance=instance,
                **detail
            )

        return instance
