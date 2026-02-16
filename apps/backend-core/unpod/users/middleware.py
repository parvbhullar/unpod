from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from unpod.users.models import BlackListToken


class BlackListTokenCheckerMiddleware(MiddlewareMixin):

    def process_request(self, request):
        token = request.headers.get("Authorization")
        if token:
            if BlackListToken.objects.filter(token=token).exists():
                return JsonResponse({"message": "Unauthorized Access", 'error': "Expired Auth Token"}, status=401)
        return None
