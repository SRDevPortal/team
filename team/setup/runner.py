from .custom_fields import apply_custom_fields
from .doctypes import ensure_team_doctypes
from .utils import ensure_module_def


def setup_all():
	ensure_module_def()
	ensure_team_doctypes()
	apply_custom_fields()
