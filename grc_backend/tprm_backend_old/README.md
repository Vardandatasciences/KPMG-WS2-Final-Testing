# Vendor Guard Hub - Django Backend

A comprehensive Django-based backend for SLA management and vendor performance monitoring.

## Features

- **SLA Management**: Complete lifecycle management of Service Level Agreements
- **Review Workflows**: Configurable multi-level review processes
- **Performance Monitoring**: Real-time performance tracking and analytics
- **Compliance Tracking**: Automated compliance monitoring and reporting
- **Vendor Management**: Comprehensive vendor relationship management
- **Analytics Dashboard**: Advanced analytics and reporting capabilities

## Technology Stack

- **Django 4.2.7**: Web framework
- **Django REST Framework**: API framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Background task processing
- **JWT Authentication**: Secure API authentication
- **Swagger/OpenAPI**: API documentation

## Project Structure

```
backend/
├── vendor_guard_hub/          # Main Django project
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── celery.py            # Celery configuration
│   └── wsgi.py              # WSGI configuration
├── users/                    # User management app
├── core/                     # Core functionality
├── slas/                     # SLA management
├── performance/              # Performance monitoring
├── compliance/               # Compliance tracking
├── analytics/                # Analytics and reporting
├── vendors/                  # Vendor management
├── requirements.txt          # Python dependencies
└── manage.py                # Django management script
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js (for frontend)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vendor-guard-hub/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   Create a `.env` file in the backend directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=vendor_guard_hub
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=localhost
   DB_PORT=5432
   REDIS_URL=redis://localhost:6379
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis server**
   ```bash
   redis-server
   ```

8. **Start Celery worker**
   ```bash
   celery -A vendor_guard_hub worker -l info
   ```

9. **Start Celery beat (for scheduled tasks)**
   ```bash
   celery -A vendor_guard_hub beat -l info
   ```

10. **Run development server**
    ```bash
    python manage.py runserver
    ```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/token/refresh/` - Refresh JWT token

### SLA Management
- `GET /api/slas/` - List SLAs
- `POST /api/slas/` - Create SLA
- `GET /api/slas/{id}/` - Get SLA details
- `PUT /api/slas/{id}/` - Update SLA
- `DELETE /api/slas/{id}/` - Delete SLA
- `POST /api/slas/{id}/submit/` - Submit for review
- `POST /api/slas/{id}/review/` - Review SLA

### Performance & Monitoring
- `GET /api/performance/` - List performance data
- `POST /api/performance/` - Create performance entry
- `POST /api/performance/bulk/` - Bulk performance upload
- `GET /api/performance/trends/` - Trend analysis


### Compliance
- `GET /api/compliance/frameworks/` - Get compliance frameworks
- `POST /api/compliance/audits/` - Create compliance audit
- `GET /api/compliance/questionnaires/` - Get audit questionnaires
- `POST /api/compliance/evidence/` - Upload audit evidence

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Key Models

### SLA Management
- **Vendor**: Vendor information and contact details
- **Contract**: Contract details and terms
- **SLA**: Service Level Agreement definitions
- **SLAMetric**: Individual SLA metrics and targets
- **SLACompliance**: Compliance tracking records
- **SLAViolation**: Violation records and penalties


### Performance Monitoring
- **PerformanceMetric**: Performance data points
- **PerformanceReport**: Performance reports

## Background Tasks

The application uses Celery for background task processing:

- **SLA Compliance Checks**: Daily automated compliance verification
- **Performance Reports**: Hourly performance report generation
- **Data Cleanup**: Weekly cleanup of old data
- **Review Reminders**: Hourly review reminder notifications
- **Dashboard Updates**: 30-minute dashboard data updates

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | True |
| `DB_NAME` | Database name | vendor_guard_hub |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `EMAIL_BACKEND` | Email backend | console |

### System Configuration

The application uses Django Constance for dynamic configuration:

- `SLA_REVIEW_TIMEOUT_HOURS`: SLA review timeout (default: 24)
- `PERFORMANCE_DATA_RETENTION_DAYS`: Data retention period (default: 365)
- `MAX_FILE_UPLOAD_SIZE_MB`: Maximum file upload size (default: 10)

## Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Install pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
isort .
```

### Database Migrations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

## Deployment

### Production Settings

For production deployment, update the following in `settings.py`:

1. Set `DEBUG = False`
2. Configure proper database settings
3. Set up proper email backend
4. Configure static file serving
5. Set up proper logging
6. Configure HTTPS

### Docker Deployment

A Docker setup is available for containerized deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation

## Changelog

### Version 1.0.0
- Initial release
- Core SLA management functionality
- Review workflows
- Performance monitoring
- Compliance tracking
- Analytics dashboard
