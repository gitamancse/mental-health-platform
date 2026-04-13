from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db.models import Base 

# This is the Alembic Config object
config = context.config

# Import models after setting up the metadata
def import_models():
    # Import user models
    from app.modules.users.models.user_model import User, AdminProfile, ProviderProfile, ClientProfile

    # Import provider models
    from app.modules.provider.models.provider_registration import ProviderRegistration
    from app.modules.provider.models.admin_action import AdminAction

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Set the SQLAlchemy URL
from app.core.config import settings
config.set_main_option('sqlalchemy.url', settings.SQLALCHEMY_DATABASE_URI)

# Target metadata
target_metadata = Base.metadata

# Import models after target_metadata is set
import_models()

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    import_models()  # Import models again for offline mode
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    import_models()  # Import models again for online mode
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
