from alembic import context

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models
from app.core.database import Base
from app.models import (
    species, incident, ranger, patrol, report, 
    protected_area, alert, equipment, observation, 
    poacher
)

target_metadata = Base.metadata
# Also add this to support our models:
from app.core.database import engine