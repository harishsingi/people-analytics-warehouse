"""People analytics warehouse: synthetic HR data, SCD2 dims, attrition metrics."""

from .config import WarehouseConfig, load_config
from .models import EmployeeRecord, SCD2Row

__version__ = "0.2.0"
__all__ = ["WarehouseConfig", "load_config", "EmployeeRecord", "SCD2Row",
           "__version__"]
