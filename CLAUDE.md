# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vitrina is Lithuania's open data catalogue (data.gov.lt), built with Django 4.2. The project follows TDD, DDD (Documentation Driven Development), and GitHub Flow principles. The main development branch is `devel` (not `main`).

## Django-CMS 4.x Upgrade

The project has been upgraded from django-cms 3.10.1 to 4.1.9 (branch: `feature/django-cms-4-rebase`). Key changes:

### Updated Dependencies
- `django-cms`: 3.10.1 → 4.1.9
- `djangocms-blog`: 1.2.3 → 2.0.6
- `django-filer`: 3.2.3 → 3.4.1
- `djangocms-text-ckeditor`: 5.0.1 → 5.1.7 (deprecated as of March 2025)

### CMS 4.x API Changes
- **PageContent API**: Navigation now uses `PageContent.objects.filter(in_navigation=True)` instead of `Page.objects.public()` (updated in `vitrina/templatetags/navigation_tags.py`)
- **No Draft/Publish**: CMS 4.x has no draft workflow by default; all changes are immediately live
- **Settings**: Requires `CMS_CONFIRM_VERSION4 = True` in settings

### Known Issue: djangocms-blog Migration Compatibility

**Problem**: The djangocms-blog migration `0014_auto_20160215_1331` uses `Page.objects.drafts()` which was removed in CMS 4.x, causing:
```
AttributeError: 'PageManager' object has no attribute 'drafts'
```

**Solution**: Compatibility patch in `tests/conftest.py`:
```python
@pytest.fixture(scope="session", autouse=True)
def patch_cms_page_manager_for_blog_migration():
    """
    Patch CMS Page manager to add drafts() method for djangocms-blog migration compatibility.

    djangocms-blog migration 0014_auto_20160215_1331 uses Page.objects.drafts() which was
    removed in django-CMS 4.x. This patch adds the method back as an alias to all() since
    in CMS 4.x, all pages are considered "live" by default (no draft/publish distinction).
    """
    from cms.models import Page

    if not hasattr(Page.objects, 'drafts'):
        Page.objects.drafts = lambda: Page.objects.all()

    yield

    if hasattr(Page.objects, 'drafts') and callable(Page.objects.drafts):
        try:
            delattr(Page.objects.__class__, 'drafts')
        except (AttributeError, TypeError):
            pass
```

This patch is only needed for fresh database migrations. Production migrations should fake this specific migration:
```bash
python manage.py migrate djangocms_blog 0014_auto_20160215_1331 --fake
```

### Future Considerations
- **djangocms-text-ckeditor**: Deprecated as of Q1 2025. Plan migration to `djangocms-text` within 6 months
- **Versioning**: Consider installing `djangocms-versioning` if draft workflow is needed

## Environment Setup

Copy environment variables:
```bash
cp .env.example .env
```

Start services with Docker:
```bash
docker-compose up -d
```

Install dependencies and setup database:
```bash
poetry install
poetry run python manage.py migrate vitrina_classifiers
poetry run python manage.py migrate sites
poetry run python manage.py migrate
poetry run python manage.py rebuild_index --noinput
poetry run python manage.py createinitialrevisions
```

Build static assets:
```bash
poetry run python manage.py collectstatic
cd webpack
npm install
npm run build
```

## Common Commands

### Development server
```bash
poetry run python manage.py runserver
```

### Run tests
```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/path/to/test_file.py

# Specific test function
poetry run pytest tests/path/to/test_file.py::test_function_name

# With coverage
poetry run pytest --cov=vitrina
```

### Linting and formatting
```bash
# Run ruff linter
poetry run ruff check vitrina/

# Format code with ruff
poetry run ruff format vitrina/

# Run flake8
poetry run flake8

# Lint templates
poetry run djlint vitrina/
```

### Translations
```bash
# Create/update translation files (replace en with desired language)
poetry run python manage.py makemessages -av1

# Compile translation files
poetry run python manage.py compilemessages
```

### Database
```bash
# Create migrations
poetry run python manage.py makemigrations

# Apply migrations
poetry run python manage.py migrate

# Access database via adminer at http://localhost:9000/
# Credentials: System: PostgreSQL, Server: postgres, Username: adp, Password: secret, Database: adp-dev
```

### Search index
```bash
# Rebuild Elasticsearch index
poetry run python manage.py rebuild_index --noinput

# Update index
poetry run python manage.py update_index
```

### Celery (background tasks)
```bash
# Worker runs via docker-compose service 'celery'
# To run manually:
celery -A vitrina worker -l info
```

## Project Architecture

### Core Django Apps Structure

The project uses a modular Django app structure under the `vitrina/` directory:

- **datasets/** - Core dataset models, views, and management. Contains the main `Dataset` model (83KB models.py) which is central to the application
- **orgs/** - Organization and representative management
- **users/** - User authentication, profiles, email confirmation
- **structure/** - Data structure modeling (Models, Properties, Metadata) for dataset schemas
- **requests/** - Data access requests and request management
- **comments/** - Commenting system for datasets and other resources
- **api/** - REST API endpoints (DRF + drf-yasg for Swagger)
- **uapi/** - Unified API integration with Spinta
- **catalogs/** - Data catalog management and harvesting
- **cms/** - Django CMS integration for content pages
- **classifiers/** - Taxonomy/classification system (Categories, Frequencies, Concepts)
- **messages/** - Internal messaging system
- **tasks/** - Task management
- **projects/** - Project tracking
- **plans/** - Planning functionality
- **resources/** - Resource management
- **statistics/** - Analytics and statistics
- **likes/** - Like/favorite functionality
- **viisp/** - VIISP authentication integration (Lithuanian e-government gateway)
- **smart_contracts/** - Smart contract integration
- **translate/** - Translation services

### Key External Integrations

- **Spinta** - Open data framework integration via `vitrina/uapi/` app. Spinta executable path configured via `SPINTA_EXECUTABLE` env var
- **VIISP** - Lithuanian government authentication service integrated via `vitrina/viisp/`
- **OAuth** - OAuth server integration for API authentication
- **Elasticsearch** - Search backend (version 7.8.1) managed via django-haystack

### Technology Stack

- **Backend**: Django 4.2, Python 3.11+, Poetry for dependency management
- **Database**: PostgreSQL 14
- **Cache/Queue**: Redis (for caching and Celery broker)
- **Search**: Elasticsearch 7.8.1 with django-haystack
- **Task Queue**: Celery 5.5+ for async tasks
- **Frontend**: Webpack build system, Bulma CSS framework, jQuery
- **Authentication**: django-allauth, custom VIISP integration, OAuth
- **CMS**: django-cms 4.1+ (upgraded from 3.10)
- **API**: Django REST Framework, drf-yasg (Swagger/OpenAPI)
- **Versioning**: django-reversion for model history tracking

### Data Model Patterns

- **Translatable Models**: Uses django-parler for multilingual content (e.g., `DatasetGroup`, `Resource`)
- **Tree Structures**: Uses treebeard MP_Node for hierarchical data (e.g., `Resource` model)
- **Generic Relations**: ContentType framework for polymorphic relationships
- **UUID Primary Keys**: Custom `UUIDBaseModel` base class
- **Versioning**: django-reversion integration for tracking changes

### URL Routing

Main URL patterns defined in `vitrina/urls.py` include all apps with prefix-less routing (most apps use `path("", include("vitrina.{app}.urls"))`). Key endpoints:
- `/admin/` - Django admin
- `/coordinator-admin/` - Custom coordinator admin interface
- `/accounts/` - VIISP authentication
- `/_version/` - Version information endpoint

### Settings Organization

Settings in `vitrina/settings.py` use django-environ for configuration. Key environment variables in `.env`:
- `DATABASE_URL` - PostgreSQL connection
- `SEARCH_URL` - Elasticsearch connection
- `REDIS_URL` - Redis connection
- `CELERY_BROKER_URL` - Celery broker
- `VIISP_*` - VIISP authentication configuration
- `OAUTH_*` - OAuth server configuration
- `SPINTA_*` - Spinta integration paths

### Testing

- Uses pytest with pytest-django and pytest-cov
- WebTest for integration testing via django-webtest
- Factory Boy for test data generation
- Main conftest at `tests/conftest.py` with app-specific conftests
- Haystack tests marked with `@pytest.mark.haystack` decorator

### Static Assets

- Source: `webpack/` directory with webpack build configuration
- Built assets collected to `static/` via `collectstatic`
- Uses Bulma CSS framework, Font Awesome icons
- SCSS compilation via django-sass-processor and libsass

### Docker Services

Defined in `docker-compose.yml`:
- `vitrina` - Main Django application (port 8000)
- `postgres` - PostgreSQL database (port 5432)
- `elasticsearch` - Search engine (port 9200)
- `redis` - Cache and message broker (port 6379)
- `adminer` - Database admin UI (port 9000)
- `celery` - Background task worker

## Code Style

- Line length: 120 characters (configured in ruff)
- Ruff checks for print statements (T201) - avoid using print in production code
- Exclude migrations from linting
- Quote style: double quotes
- Indent: 4 spaces
- Follow Django coding conventions
