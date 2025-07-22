from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import ProtectedError
from .models import ProjectCreate, TaskCreation, subtask, EmployeeAttendance, PerformanceInvoice, PerformanceInvoiceDetails, ErpEmployeeAttendance, ErpEmployeeAttendanceDetails
from .serializers import ErpEmployeeAttendanceDetailsSerializer, ErpEmployeeAttendanceSerializer, ProjectCreateSerializer, TaskCreationSerializer, SubTaskSerializer, EmployeeAttendanceSerializer, PerformanceInvoiceSerializer, PerformanceInvoiceDetailsSerializer
from employees.models import Employee,EmployeeFamilyDetails, EmployeeSettings
from employees.serializers import EmployeeSerializer
from common.permissions import IsAdminUser, IsCustomerUser, IsCustomer,IsEmployee, isSuperuser,IsSuperuserOrEmployee
from django.core.paginator import Paginator
from utilities.pagination_mixin import PaginationMixin
from .constants import ADMIN_PROJECT_ACTION_LIST,ADMIN_PROJECT_COLUMN_LIST,ADMIN_TASK_COLUMN_LIST,ADMIN_TASK_ACTION_LIST,SUB_TASK_COLUMN_LIST,SUB_TASK_ACTION_LIST, ADMIN_PERFORMANCE_COLUMN_LIST, ADMIN_PERFORMANCE_ACTION_LIST,ADMIN_ERP_ATTENDANCE_COLUMNS,ADMIN_ERP_ATTENDANCE_ACTION_LIST
from utilities.constants import FILTERS
from utilities.utils import base64_to_file
from django.utils.timezone import now
from rest_framework import generics, permissions, status
pagination = PaginationMixin()
from admin_masters.models import ClientMaster, ProductMaster,ModuleMaster
from datetime import datetime, timedelta, date, time
from django.utils.crypto import get_random_string
from django.utils import timezone
import re
# PROJECT CREATION

class ProjectCreateListView(generics.GenericAPIView):
    queryset = ProjectCreate.objects.all().order_by('-id_project')
    serializer_class = ProjectCreateSerializer

    def get(self, request):
        if 'active' in request.query_params:
            queryset = ProjectCreate.objects.all()
            serializer = ProjectCreateSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_PROJECT_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("id_project")),
                "sno": index + 1,
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_PROJECT_COLUMN_LIST,
            "actions": ADMIN_PROJECT_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        return pagination.paginated_response(enhanced_data, context)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectRetrieveUpdateDestroyView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ProjectCreate.objects.all()
    serializer_class = ProjectCreateSerializer
    lookup_field = "id_project"

    def get(self, request, pk):
        try:
            project = self.get_queryset().get(id_project=pk)

            serializer = self.get_serializer(project)
            return Response(serializer.data)
        except ProjectCreate.DoesNotExist:
            return Response(
                {"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        project = self.get_queryset().get(id_project=pk)
        serializer = self.get_serializer(project, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = self.get_queryset().get(id_project=pk)
        try:
            project.delete()
            return Response({"message": "Project deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"message": "Cannot delete this project because it is referenced by other records."},
                status=status.HTTP_423_LOCKED
            )


# TASK CREATION
class TaskCreateListView(generics.GenericAPIView):
    queryset = TaskCreation.objects.all().order_by('-task_id')
    serializer_class = TaskCreationSerializer

    def get(self, request):
        if 'active' in request.query_params:
            queryset = TaskCreation.objects.all()
            serializer = TaskCreationSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_TASK_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("task_id")),
                "sno": index + 1,
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_TASK_COLUMN_LIST,
            "actions": ADMIN_TASK_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        return pagination.paginated_response(enhanced_data, context)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = TaskCreation.objects.all()
    serializer_class = TaskCreationSerializer
    lookup_field = 'task_id'

    def get(self, request,pk):
        try:
            task = self.get_queryset().get(task_id=pk)
            serializer = self.get_serializer(task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TaskCreation.DoesNotExist:
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        task = self.get_queryset().get(task_id=pk)
        serializer = self.get_serializer(task, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = self.get_queryset().get(task_id=pk)
        try:
            task.delete()
            return Response({"message": "Task deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"message": "Cannot delete this task because it is referenced by other records."},
                status=status.HTTP_423_LOCKED
            )




# SUBTASK CREATION

class SubTaskCreateListView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = subtask.objects.all().order_by('-id_sub_task')
    serializer_class = SubTaskSerializer
    
    def get(self, request):
        if 'active' in request.query_params:
            queryset = subtask.objects.all()
            serializer = SubTaskSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, SUB_TASK_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            
            tas = TaskCreation.objects.get(task_id = data['id_task'])
            data.update({
                "pk_id": data.get("id", data.get("id_sub_task")),
                "sno": index + 1,
                "id_task":tas.task_name,
            })
            enhanced_data.append(data)

        filters_copy = FILTERS.copy()
        context = {
            "columns": SUB_TASK_COLUMN_LIST,
            "actions": SUB_TASK_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        return pagination.paginated_response(enhanced_data, context)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SubTaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = subtask.objects.all()
    serializer_class = SubTaskSerializer
    lookup_field = 'id_sub_task'

    def get(self, request, pk):
        try:
            sub_task = self.get_queryset().get(id_sub_task=pk)
            serializer = self.get_serializer(sub_task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except subtask.DoesNotExist:
            return Response({"message": "Subtask not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        sub_task = self.get_queryset().get(id_sub_task=pk)
        serializer = self.get_serializer(sub_task, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        sub_task = self.get_queryset().get(id_sub_task=pk)
        try:
            sub_task.delete()
            return Response({"message": "Subtask deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"message": "Cannot delete this subtask because it is referenced by other records."},
                status=status.HTTP_423_LOCKED
            )


# EMPLOYEE ATTENDANCE

class AttendanceCreateListView(generics.GenericAPIView):
    queryset = EmployeeAttendance.objects.all().order_by('-checkin_id')
    serializer_class = EmployeeAttendanceSerializer

    def get(self, request):
        attendance = self.get_queryset()
        serializer = self.get_serializer(attendance, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AttendanceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = EmployeeAttendance.objects.all()
    serializer_class = EmployeeAttendanceSerializer
    lookup_field = 'checkin_id'

    def get(self, request, *args, **kwargs):
        try:
            attendance = self.get_object()
            serializer = self.get_serializer(attendance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployeeAttendance.DoesNotExist:
            return Response({"message": "Attendance record not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, *args, **kwargs):
        attendance = self.get_object()
        serializer = self.get_serializer(attendance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        attendance = self.get_object()
        try:
            attendance.delete()
            return Response({"message": "Attendance record deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"message": "Cannot delete this attendance record because it is referenced by other records."},
                status=status.HTTP_423_LOCKED
            )


# PERFORMANCE INVOICE

class PerformanceInvoiceCreateAPI(generics.GenericAPIView):
    serializer_class = PerformanceInvoiceSerializer
    permission_classes = [IsSuperuserOrEmployee]

    def get(self, request, *args, **kwargs):
        pk = request.data.get('id_product')
        client = request.data.get('client_id')
        try:
            product = ProductMaster.objects.get(pk=pk)
            client = ClientMaster.objects.get(pk=client)
        except ProductMaster.DoesNotExist:
            return Response({"message": "Product or Client not found."}, status=status.HTTP_404_NOT_FOUND)
        modules = product.module.all()
        details = []
        for module in modules:
            details.append({
                "id_module": module.id_module,
                "module_name": module.module_name,
                "payment_amount": float(module.approx_cost or 0)
            })
        return Response( details ,status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        client_id = request.data.get("client_id")
        id_product = request.data.get("id_product")
        modules = request.data.get("modules", [])

        if not all([client_id, id_product, modules]):
            return Response({"message": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = ClientMaster.objects.get(pk=client_id)
            product = ProductMaster.objects.get(pk=id_product)
        except (ClientMaster.DoesNotExist, ProductMaster.DoesNotExist):
            return Response({"message": "Invalid client or product."}, status=status.HTTP_404_NOT_FOUND)

        # Generate ref_no (e.g., "INV-0001")
        last_invoice = PerformanceInvoice.objects.order_by('-invoice_id').first()
        next_invoice_number = 1 if not last_invoice else last_invoice.invoice_id + 1
        ref_no = f"INV-{str(next_invoice_number).zfill(4)}"
        today = timezone.now().date()

        # Create the invoice
        invoice = PerformanceInvoice.objects.create(
            ref_no=ref_no,
            client_id=client,
            id_product=product,
            date=today
        )

        # Save each module detail
        for item in modules:
            module_id = item.get("id_module")
            payment_amount = item.get("payment_amount", 0)

            try:
                module = ModuleMaster.objects.get(pk=module_id)
                PerformanceInvoiceDetails.objects.create(
                    invoice_id=invoice,
                    id_module=module,
                    payment_amount=payment_amount
                )
            except ModuleMaster.DoesNotExist:
                continue

        # Return the final saved data
        response_data = {
            "ref_no": ref_no,
            "invoice_id": invoice.invoice_id,
            "date": today.strftime("%Y-%m-%d"),
            "client_id": client_id,
            "id_product": id_product,
            "modules": modules,
        }
        return Response(response_data, status=status.HTTP_200_OK)
        
class PerformanceInvoiceListAPI(generics.GenericAPIView):
    queryset = PerformanceInvoice.objects.all().order_by('-invoice_id')
    serializer_class = PerformanceInvoiceSerializer

    def get(self, request):
        if 'active' in request.query_params:
            queryset = PerformanceInvoice.objects.all()
            serializer = PerformanceInvoiceSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_PERFORMANCE_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True) 
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("invoice_id")),
                "sno": index + 1,
                "ref_no": data.get("ref_no"),
                "date": data.get("date", now().strftime("%Y-%m-%d")),
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_PERFORMANCE_COLUMN_LIST,
            "actions": ADMIN_PERFORMANCE_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        return pagination.paginated_response(enhanced_data, context)
    


class PerformanceUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformanceInvoice.objects.all()
    serializer_class = PerformanceInvoiceSerializer
    lookup_field = 'invoice_id'

    def get(self, request, pk):
        try:
            instance = self.get_queryset().get(invoice_id=pk)
            serializer = self.get_serializer(instance)
            
            # Manually include related PerformanceInvoiceDetails
            details = PerformanceInvoiceDetails.objects.filter(invoice_id=instance)
            details_data = [
                {
                    "invoicedetails_id": d.invoicedetails_id,
                    "invoice_id": d.invoice_id_id,
                    "id_module": d.id_module_id,
                    "payment_amount": d.payment_amount
                }
                for d in details
            ]

            response_data = serializer.data
            response_data["invoice_details"] = details_data

            return Response(response_data, status=status.HTTP_200_OK)
        except PerformanceInvoice.DoesNotExist:
            return Response({"message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            instance = self.get_queryset().get(invoice_id=pk)
        except PerformanceInvoice.DoesNotExist:
            return Response({"message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        details_data = request.data.pop("id_module", []) or request.data.pop("invoice_details", [])

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            PerformanceInvoiceDetails.objects.filter(invoice_id=instance).delete()
            for detail in details_data:
                PerformanceInvoiceDetails.objects.create(
                    invoice_id=instance,
                    id_module_id=detail["id_module"],
                    payment_amount=detail.get("payment_amount")
                )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            instance = self.get_queryset().get(invoice_id=pk)
            PerformanceInvoiceDetails.objects.filter(invoice_id=instance).delete()
            instance.delete()
            return Response({"success": "Invoice and related details deleted."}, status=status.HTTP_204_NO_CONTENT)
        except PerformanceInvoice.DoesNotExist:
            return Response({"message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        

# ERP EMPLOYEE ATTENDANCE

# class ErpEmployeeAttendanceCreateListView(generics.GenericAPIView):
#     queryset = ErpEmployeeAttendance.objects.all().order_by("-id")
#     serializer_class = ErpEmployeeAttendanceSerializer

#     def get(self, request):
#         from_date = request.data.get('fromDate')
#         to_date = request.data.get('toDate')
#         queryset = self.get_queryset().prefetch_related('attendance_details')
#         if from_date and to_date:
#             date_filter = queryset.filter(date__gte=from_date, date__lte=to_date)

#         if 'active' in request.query_params:
#             serializer = ErpEmployeeAttendanceSerializer(queryset, many=True)
#             return Response(serializer.data)

#         paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_ERP_ATTENDANCE_COLUMNS)
#         serializer = self.get_serializer(page, many=True)
#         enhanced_data = []
#         sno_counter = 1

#         for data in serializer.data:
#             attendance_details = data.get("attendance_details", [])
#             for detail in attendance_details:
#                 emp = detail.get("id_employee_detail", {})
#                 status_code = detail.get("status")
#                 status_name = "Present" if status_code == 1 else "Absent" if status_code == 2 else "Unknown"
#                 formatted_date = datetime.strptime(data.get("date"), "%Y-%m-%d").strftime("%d-%m-%Y")
#                 enhanced_data.append({
#                     "sno": sno_counter,
#                     "id": data.get("id"),
#                     "pk_id": detail.get("id"),
#                     "firstname": emp.get("firstname", ""),
#                     "mobile": emp.get("mobile", ""),
#                     "date": formatted_date,
#                     "status": status_name,
#                 })
#                 sno_counter += 1

#         filters_copy = FILTERS.copy()
#         filters_copy['isDateFilterReq'] = True
#         context = {
#             "columns": ADMIN_ERP_ATTENDANCE_COLUMNS,
#             "actions": ADMIN_ERP_ATTENDANCE_ACTION_LIST,
#             "page_count": paginator.count,
#             "total_pages": paginator.num_pages,
#             "current_page": page.number,
#             "is_filter_req": True,
#             "filters": filters_copy,
#         }
#         return pagination.paginated_response(enhanced_data, context)

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ErpEmployeeAttendanceCreateListView(generics.GenericAPIView):
    queryset = ErpEmployeeAttendance.objects.all().order_by("-id")
    serializer_class = ErpEmployeeAttendanceSerializer

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        print("date",from_date, to_date)
        if isinstance(request.data.get("attendance_details"), list):
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().prefetch_related("attendance_details", "attendance_details__id_employee")
        if from_date and to_date:
            queryset = queryset.filter(date__gte=from_date, date__lte=to_date)
        if 'active' in request.query_params:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        flat_data = []
        sno_counter = 1

        for attendance in queryset:
            date_formatted = attendance.date.strftime("%d-%m-%Y")
            for detail in attendance.attendance_details.all():
                emp = detail.id_employee
                flat_data.append({
                    "sno": sno_counter,
                    "id": attendance.id,
                    "pk_id": detail.id,
                    "firstname": emp.firstname,
                    "mobile": emp.mobile,
                    "date": date_formatted,
                    "status": dict(detail.STATUS_CHOICES).get(detail.status, "Unknown"),
                })
                sno_counter += 1

        paginator, page = pagination.paginate_queryset(flat_data, request, None, ADMIN_ERP_ATTENDANCE_COLUMNS)

        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True

        context = {
            "columns": ADMIN_ERP_ATTENDANCE_COLUMNS,
            "actions": ADMIN_ERP_ATTENDANCE_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": True,
            "filters": filters_copy,
        }

        return pagination.paginated_response(list(page), context)


class ErpEmployeeAttendanceRetrieveUpdateDestroyView(generics.GenericAPIView):
    queryset = ErpEmployeeAttendance.objects.all()
    serializer_class = ErpEmployeeAttendanceSerializer
    lookup_field = "id"

    def get(self, request, pk):
        try:
            detail = ErpEmployeeAttendanceDetails.objects.get(id=pk)

            # Toggle status (1 = Present, 2 = Absent)
            detail.status = 2 if detail.status == 1 else 1
            detail.updated_by = request.user
            detail.updated_on = datetime.now(tz=timezone.utc)
            detail.save()

            return Response({
                "message": "Attendance detail status updated successfully.",
                "id": detail.id,
                "new_status": detail.status,
                "status_display": detail.get_status_display()
            }, status=status.HTTP_202_ACCEPTED)

        except ErpEmployeeAttendanceDetails.DoesNotExist:
            return Response({"message": "Attendance detail not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            attendance = self.get_queryset().get(id=pk)
        except ErpEmployeeAttendance.DoesNotExist:
            return Response({"detail": "Attendance not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(attendance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            attendance = self.get_queryset().get(id=pk)
            attendance.delete()
            return Response({"message": "Attendance deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ErpEmployeeAttendance.DoesNotExist:
            return Response({"detail": "Attendance not found"}, status=status.HTTP_404_NOT_FOUND)
        
class EmployeeWithAttendanceListView(generics.GenericAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Employee.objects.prefetch_related('employee_attendance')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


