# Remove individual imports and use lazy imports instead
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .provider_model import ProviderProfile
    from .provider_registration import ProviderRegistration
    from .admin_action import AdminAction