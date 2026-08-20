# Add these imports at the top
from app.core.database import Base
from app.models import species, protected_area, ranger, incident, patrol, report, observation, alert, poacher, equipment

# Find the target_metadata line and set it:
target_metadata = Base.metadata

# Also add this to support our models:
from app.core.database import engine