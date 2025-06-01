from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20

    def get_paginated_response(self, data):
        return super().get_paginated_response(data)
