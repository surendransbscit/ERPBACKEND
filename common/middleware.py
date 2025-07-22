from datetime import datetime

from django.http import Http404, HttpResponseRedirect
from knox.models import AuthToken
from django.http import JsonResponse

from rest_framework import response, status

from re import sub


class AccountExpiry:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header_token = request.META.get('HTTP_AUTHORIZATION', None)
        print(header_token)
        if header_token is not None:
            try:
                token = sub('Token ', '',
                            request.META.get('HTTP_AUTHORIZATION', None))
                # print(token)
                # print(token[:8], "from middleware")
                token_obj = AuthToken.objects.get(token_key=token[:8])
                request.user = token_obj.user
            except AuthToken.DoesNotExist:
                pass
        # #This is now the correct user

        current_user = request.user

        # print(request.META['HTTP_USER_AGENT'],"from MiddleWare")
        # print(request.device,"from MiddleWare")

        # user_group=request.user.groups.filter("name")
        # print(current_user, "from middleware")
        # print (user_group, " group from middleware")

        response = self.get_response(request)
        # expiry_path = reverse('accounts:account-expired')

        if current_user.is_anonymous is False:

            # if current_user.admin is False and current_user.staff is False:
            # if request.path not in [expiry_path]:
            expiry_date = current_user.account_expiry
            # print("Account Expiry Date is", expiry_date)
            todays_date = datetime.today().date()
            # print(todays_date)
            if current_user.is_adminuser:
                if todays_date > expiry_date:
                    return JsonResponse({"Error": "Your Account has expired"},
                                        status=403)

        return response