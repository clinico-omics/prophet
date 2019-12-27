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
  def get_paginated_response(self, data):
    return Response(
      OrderedDict([
        ('next', self.get_next_link()),
        ('previous', self.get_previous_link()),
        ('results', data)]))
