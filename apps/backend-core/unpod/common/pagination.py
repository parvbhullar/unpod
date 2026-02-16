import logging
import traceback
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage

logger = logging.getLogger(__name__)


class UnpodCustomPagination:
    page_size = 10
    page = 1
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100
    data = []
    error = {}

    def __init__(self, request, queryset, serilaizer, kwargs={}):
        self.page_size = (
            int(request.GET.get(self.page_size_query_param, "0")) or self.page_size
        )
        self.page = int(request.GET.get(self.page_query_param, "0")) or self.page
        self.serilaizer = serilaizer
        self.data = queryset
        self.kwargs = kwargs

    def get_paginated_response(self, return_dict=False):
        if self.error:
            return Response(self.error, status=400)

        paginate = Paginator(self.data, self.page_size)
        try:
            page = paginate.page(self.page)
            page_data = {
                "count": page.paginator.count,
                "data": self.serilaizer(
                    page.object_list, many=True, **self.kwargs
                ).data,
            }
            if return_dict:
                return page_data
            return Response(page_data)
        except EmptyPage:
            # Requested page is out of range - return empty data with correct count
            page_data = {"count": paginate.count, "data": []}
            if return_dict:
                return page_data
            return Response(page_data)
        except Exception as ex:
            # Log the actual error for debugging
            logger.error(f"UnpodCustomPagination error: {str(ex)}", exc_info=True)
            traceback.print_exc()
            # Re-raise to show the actual error instead of silently returning empty data
            raise


def getPaginator(queryset, request):
    page_size = int(request.GET.get("page_size", "0")) or 10
    page = int(request.GET.get("page", "0")) or 1
    paginator = Paginator(queryset, page_size)
    return paginator, page, page_size


def getPagination(query_params: dict, default_limit: int = 50):
    limit = int(query_params.get("page_size", str(default_limit)))
    page = int(query_params.get("page", "1"))
    skip = (page - 1) * limit

    return skip, limit
