from collections import OrderedDict
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination


class FasterDjangoPaginator(Paginator):
    @cached_property
    def count(self):
        # only select 'pmid' for counting, much cheaper
        return self.object_list.values('pmid').count()


class FasterPageNumberPagination(PageNumberPagination):
  django_paginator_class = FasterDjangoPaginator
