import django_filters
from .models import BridgeProviderConfig

class TrunkFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status')
    direction = django_filters.CharFilter(field_name='direction')
    trunk_type = django_filters.CharFilter(field_name='trunk_type')
    provider_credential = django_filters.NumberFilter(field_name='provider_credential__id')
    bridge = django_filters.CharFilter(field_name='bridge__slug')
    provider = django_filters.NumberFilter(field_name='provider_credential__provider__id')
    numbers = django_filters.CharFilter(method='filter_numbers')

    class Meta:
        model = BridgeProviderConfig
        fields = ['status', 'direction', 'trunk_type', 'provider_credential', 'bridge', 'provider', 'numbers']

    def filter_numbers(self, queryset, name, value):
        return queryset.filter(numbers__icontains=value)
