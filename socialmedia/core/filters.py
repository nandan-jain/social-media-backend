from django.db.models import Q
from rest_framework import filters

class SearchFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get('search', None)
        if search:
            # Exact match for email and contains for name
            return queryset.filter(
                Q(email__iexact=search) | Q(name__icontains=search)
            )
        return queryset
