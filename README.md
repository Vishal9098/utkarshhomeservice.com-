# Utkarsh Cleaning Home Services - Django Website

## Setup Instructions

### Requirements
- Python 3.10+
- pip

### Installation Steps

```bash
# 1. Extract the zip and enter directory
cd utkarsh_cleaning_website

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install django pillow

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create admin user (or use existing)
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

### Access
- **Website**: http://127.0.0.1:8000/
- **Admin Dashboard**: http://127.0.0.1:8000/dashboard/
- **Django Admin**: http://127.0.0.1:8000/admin/

### Default Credentials (if using sample data)
- Admin Username: `vishal`
- Admin Password: `admin123`

### Features
- Full eCommerce with Cart, Checkout, Orders
- Admin Dashboard with Charts
- Service Categories & Products
- Blog, Gallery, Contact
- Coupon System
- User Registration & Profile
- Mobile Responsive
