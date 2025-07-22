from django.db import models
from  utilities.model_utils import CommonFields
from admin_masters.models import ClientMaster, ProductMaster, ModuleMaster
from employees.models import Employee

class ProjectCreate(CommonFields):
    id_project = models.AutoField(primary_key=True)
    client_id = models.ForeignKey(ClientMaster, on_delete=models.PROTECT, null=True)
    id_product = models.ForeignKey(ProductMaster, on_delete=models.PROTECT, null=True)
    project_name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField()
    approx_end_date = models.DateField(blank=True, null=True)
    final_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    closed_date = models.DateField(blank=True, null=True)
    team_members = models.ManyToManyField(Employee, blank=True)

    def __str__(self):
        return f"{self.project_name} ({self.id_project})"

    class Meta:
        db_table = 'project_master'

class TaskCreation(CommonFields):
    task_id = models.AutoField(primary_key=True)
    id_project = models.ForeignKey(ProjectCreate, on_delete=models.PROTECT, null=True)
    id_module = models.ForeignKey(ModuleMaster, on_delete=models.PROTECT, null=True)
    task_name = models.CharField(max_length=255)
    start_date = models.DateField()
    approx_due_date = models.DateField(blank=True, null=True)
    closed_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    referencelink = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(choices=((1,"Pending"),(2,"Assigned"),(3,"Work in progress"),(4,"Completed"),(5,"Delivered"),(6,"Cancelled"),(7,"Hold")), default=1)
    assigned_to = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True)
    assigned_by = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, related_name='task_creations_assigned')
    assigned_date = models.DateField(auto_now_add=True)

    def __self__(self):
        return f"{self.task_name} ({self.task_id})"
    
    class Meta:
        db_table = 'task'

class subtask(CommonFields):
    id_sub_task = models.AutoField(primary_key=True)
    id_task = models.ForeignKey(TaskCreation, on_delete=models.PROTECT, null=True)
    task_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    referencelink = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(choices=((1,"Pending"),(2,"Assigned"),(3,"Work in progress"),(4,"Completed"),(5,"Delivered"),(6,"Cancelled"),(7,"Hold")), default=1)
    assigned_to = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True)
    assigned_by = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, related_name='subtasks_assigned')
    assigned_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_name}({self.id_sub_task})"
    
    class Meta:
        db_table = 'sub_task'


class EmployeeAttendance(CommonFields):
    checkin_id = models.AutoField(primary_key=True)
    id_employee = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True)
    checkin_date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__ (self):
        return f"{self.id_employee} ({self.checkin_id})"
    
    class Meta:
        db_table = 'employee_attendance'


class PerformanceInvoice(CommonFields):
    invoice_id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255)
    client_id = models.ForeignKey(ClientMaster, on_delete=models.PROTECT, null=True)
    id_product = models.ForeignKey(ProductMaster, on_delete=models.PROTECT, null=True)
    date = models.DateField()
    
    def __str__(self):
        return f"{self.ref_no} ({self.invoice_id})"
    
    class Meta:
        db_table = 'admin_client_invoice'

class PerformanceInvoiceDetails(CommonFields):
    invoicedetails_id = models.AutoField(primary_key=True)
    invoice_id = models.ForeignKey(PerformanceInvoice, on_delete=models.PROTECT, null=True)
    id_module = models.ForeignKey(ModuleMaster, on_delete=models.PROTECT, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"{self.invoice_id} ({self.invoicedetails_id})"
    
    class Meta:
        db_table = 'admin_client_invoice_details'


class ErpEmployeeAttendance(CommonFields):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    class Meta:
        db_table = 'erp_employee_attendance'

    def __str__(self):
        return f"Attendance on {self.date}"


class ErpEmployeeAttendanceDetails(CommonFields):
    id = models.AutoField(primary_key=True)
    id_erp_employee_attendance = models.ForeignKey(ErpEmployeeAttendance,on_delete=models.CASCADE, related_name='attendance_details')
    id_employee = models.ForeignKey(Employee,on_delete=models.CASCADE,related_name='employee_attendance')
    STATUS_CHOICES = (
        (1, "Present"),
        (2, "Absent"),
    )
    status = models.IntegerField(choices=STATUS_CHOICES)

    class Meta:
        db_table = 'erp_employee_attendance_details'
    def __str__(self):
        return f"{self.id_employee} - {self.get_status_display()} ({self.id_erp_employee_attendance.date})"



        
