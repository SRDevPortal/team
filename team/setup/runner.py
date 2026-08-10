from .custom_fields import apply_custom_fields
from .role_permissions import apply_role_permission_rules


def setup_all():
	apply_custom_fields()
	apply_role_permission_rules()
