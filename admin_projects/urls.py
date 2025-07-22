from django.urls import path
from .views import (
    ProjectCreateListView, ProjectRetrieveUpdateDestroyView,
    TaskCreateListView, TaskRetrieveUpdateDestroyView,
    SubTaskCreateListView, SubTaskRetrieveUpdateDestroyView,
    AttendanceCreateListView, AttendanceRetrieveUpdateDestroyView,PerformanceInvoiceCreateAPI,PerformanceInvoiceListAPI,PerformanceUpdateDestroyView,
    ErpEmployeeAttendanceCreateListView, ErpEmployeeAttendanceRetrieveUpdateDestroyView,EmployeeWithAttendanceListView
)

urlpatterns = [
    # Project URLs
    path('projects/', ProjectCreateListView.as_view()),
    path('projects/<int:pk>/', ProjectRetrieveUpdateDestroyView.as_view()),

    # Task URLs
    path('tasks/', TaskCreateListView.as_view()),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroyView.as_view()),

    # Subtask URLs
    path('subtasks/', SubTaskCreateListView.as_view()),
    path('subtasks/<int:pk>/', SubTaskRetrieveUpdateDestroyView.as_view()),

    # Employee Attendance URLs
    path('attendance/', AttendanceCreateListView.as_view()),
    path('attendance/<int:pk>/', AttendanceRetrieveUpdateDestroyView.as_view()),

    # Performance Invoice URLs
    path('performance_invoices/', PerformanceInvoiceCreateAPI.as_view()),
    path('performance_invoices_list/', PerformanceInvoiceListAPI.as_view()),
    path('performance_invoices_list/<int:pk>', PerformanceUpdateDestroyView.as_view()),

    # Erp Employee Attendance URLs
    path('erpemployeeattendance/', ErpEmployeeAttendanceCreateListView.as_view() ),
    path('erpemployeeattendance/<int:pk>/', ErpEmployeeAttendanceRetrieveUpdateDestroyView.as_view()),
    path('employeesdetails/', EmployeeWithAttendanceListView.as_view()),
]
