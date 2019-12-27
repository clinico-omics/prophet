from collections import OrderedDict
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.utils.functional import cached_property
from rest_framework.pagination import LimitOffsetPagination


class FasterPageNumberPagination(LimitOffsetPagination):
  def get_count(self):
    # only select 'pmid' for counting, much cheaper
    return 10000

  def paginate_queryset(self, queryset, request, view=None):
    self.count = self.get_count()
    self.limit = self.get_limit(request)
    if self.limit is None:
        return None

    self.offset = self.get_offset(request)
    self.request = request
    if self.count > self.limit and self.template is not None:
        self.display_page_controls = True

    if self.count == 0 or self.offset > self.count:
        return []
    return list(queryset[self.offset:self.offset + self.limit])

  def get_paginated_response(self, data):
    return Response({
      'next': self.get_next_link(),
      'previous': self.get_previous_link(),
      'results': data
    })
