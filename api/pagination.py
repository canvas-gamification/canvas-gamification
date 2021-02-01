from rest_framework import pagination


class BasePagination(pagination.PageNumberPagination):
    page_size = 100
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 1000
