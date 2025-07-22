from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import ProtectedError
from .models import ClientMaster, ModuleMaster, ProductMaster
from .serializers import (
    ClientMasterSerializer,
    ModuleMasterSerializer,
    ProductMasterSerializer,
)
from django.core.paginator import Paginator
from utilities.pagination_mixin import PaginationMixin
from .constants import ADMIN_MASTER_ACTION_LIST, ADMIN_MASTER_COLUMN_LIST, ADMIN_MODULE_MASTER_COLUMN_LIST, ADMIN_MODULE_MASTER_ACTION_LIST,ADMIN_PRODUCT_MASTER_COLUMN_LIST,ADMIN_PRODUCT_MASTER_ACTION_LIST
from utilities.constants import FILTERS
from utilities.utils import base64_to_file
from django.utils.timezone import now
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee, isSuperuser, IsSuperuserOrEmployee
from rest_framework import generics, permissions, status

pagination = PaginationMixin()


# CLIENT MASTER

class ClientMasterListCreateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ClientMaster.objects.all()
    serializer_class = ClientMasterSerializer

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = ClientMaster.objects.all()
            serializer = ClientMasterSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()

        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_MASTER_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)

        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("client_id")),
                "sno": index + 1,
            })

            img = data.get("client_img")
            # if img:
            #     data['image_text'] = img
            # else:
            first_name = data.get('first_name', '').strip()
            data['image_text'] = f"{first_name[0].upper()}" if first_name else "Letter:?"

            enhanced_data.append(data)

        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_MASTER_COLUMN_LIST,
            "actions": ADMIN_MASTER_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        return pagination.paginated_response(enhanced_data, context)

    def post(self, request):
        order_image = request.data.get("order_images", [])
        if order_image:
            try:
                base64_string = order_image.split(",")[1]
                file_content = base64_to_file(
                    base64_string, filename_prefix="client_img", file_extension="jpg"
                )
                request.data["client_img"] = file_content
            except Exception as e:
                return Response(
                    {"error": f"Image processing failed: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientMasterRetrieveUpdateDestroyView(generics.GenericAPIView):
    queryset = ClientMaster.objects.all()
    serializer_class = ClientMasterSerializer
    lookup_field = "client_id"

    def get(self, request, pk):
        try:
            client = self.get_queryset().get(client_id=pk)
            serializer = self.get_serializer(client)
            return Response(serializer.data)
        except ClientMaster.DoesNotExist:
            return Response(
                {"detail": "Client not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            client = self.get_queryset().get(client_id=pk)
        except ClientMaster.DoesNotExist:
            return Response(
                {"detail": "Client not found"}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.copy()
        order_image = request.data.get("order_images")

        if order_image:
            try:
                base64_string = None

                # Case 1: Single base64 string (correct in your case)
                if isinstance(order_image, str) and order_image.startswith("data:image"):
                    base64_string = order_image

                # Case 2: List of dicts with 'base64' key
                elif isinstance(order_image, list) and isinstance(order_image[0], dict):
                    base64_string = order_image[0].get("base64")

                # Case 3: List of base64 strings
                elif isinstance(order_image, list) and isinstance(order_image[0], str) and order_image[0].startswith("data:image"):
                    base64_string = order_image[0]

                # Case 4: Image URL – skip processing
                elif isinstance(order_image, str) and order_image.startswith("http"):
                    base64_string = None  # don't touch

                else:
                    raise ValueError("Unsupported image format.")

                if base64_string:
                    file_content = base64_to_file(
                        base64_string, filename_prefix="client_img", file_extension="jpg"
                    )
                    data["client_img"] = file_content

            except Exception as e:
                return Response(
                    {"error": f"Image processing failed: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(client, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            client = self.get_queryset().get(client_id=pk)
            client.delete()
            return Response(
                {"detail": "Client deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except ProtectedError:
            return Response(
                {
                    "detail": "Cannot delete client as it is referenced by other records."
                },
                status=status.HTTP_423_LOCKED,
            )
        except ClientMaster.DoesNotExist:
            return Response(
                {"detail": "Client not found"}, status=status.HTTP_404_NOT_FOUND
            )


# MODULE MASTER

class ModuleMasterListCreateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ModuleMaster.objects.all().order_by("-id_module")
    serializer_class = ModuleMasterSerializer

    def get(self, request):
        if 'active' in request.query_params:
            queryset = ModuleMaster.objects.all()
            serializer = ModuleMasterSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_MODULE_MASTER_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("id_module")),
                "sno": index + 1,
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_MODULE_MASTER_COLUMN_LIST,
            "actions": ADMIN_MODULE_MASTER_ACTION_LIST,
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


class ModuleMasterRetrieveUpdateDestroyView(generics.GenericAPIView):
    queryset = ModuleMaster.objects.all()
    serializer_class = ModuleMasterSerializer
    lookup_field = "id_module"

    def get(self, request, pk):
        try:
            module = self.get_queryset().get(id_module=pk)
            serializer = self.get_serializer(module)
            return Response(serializer.data)
        except ModuleMaster.DoesNotExist:
            return Response(
                {"detail": "Module not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            module = self.get_queryset().get(id_module=pk)
        except ModuleMaster.DoesNotExist:
            return Response(
                {"detail": "Module not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(module, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            module = self.get_queryset().get(id_module=pk)
            module.delete()
            return Response(
                {"detail": "Module deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except ProtectedError:
            return Response(
                {
                    "detail": "Cannot delete module as it is referenced by other records."
                },
                status=status.HTTP_423_LOCKED,
            )
        except ModuleMaster.DoesNotExist:
            return Response(
                {"detail": "Module not found"}, status=status.HTTP_404_NOT_FOUND
            )


# PRODUCT MASTER


class ProductMasterListCreateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ProductMaster.objects.all().order_by("-id_product")
    serializer_class = ProductMasterSerializer

    def get(self, request):
        if 'active' in request.query_params:
            queryset = ProductMaster.objects.all()
            serializer = ProductMasterSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ADMIN_PRODUCT_MASTER_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("id_product")),
                "sno": index + 1,
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        context = {
            "columns": ADMIN_PRODUCT_MASTER_COLUMN_LIST,
            "actions": ADMIN_PRODUCT_MASTER_ACTION_LIST,
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


class ProductMasterRetrieveUpdateDestroyView(generics.GenericAPIView):
    queryset = ProductMaster.objects.all()
    serializer_class = ProductMasterSerializer
    lookup_field = "id_product"

    def get(self, request, pk):
        try:
            product = self.get_queryset().get(id_product=pk)
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except ProductMaster.DoesNotExist:
            return Response(
                {"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            product = self.get_queryset().get(id_product=pk)
        except ProductMaster.DoesNotExist:
            return Response(
                {"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            product = self.get_queryset().get(id_product=pk)
            product.delete()
            return Response(
                {"detail": "Product deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except ProtectedError:
            return Response(
                {
                    "detail": "Cannot delete product as it is referenced by other records."
                },
                status=status.HTTP_423_LOCKED,
            )
        except ProductMaster.DoesNotExist:
            return Response(
                {"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )
