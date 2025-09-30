# Anteiku Sports Café POS

A lightweight, web-based Point of Sale (POS) system built with Python and Flask, designed for a small café to efficiently manage sales, inventory, and users.

## Screenshots

*(It's highly recommended to add a few screenshots of your application here. You can upload them to your GitHub repository and link them.)*

| Dashboard | Billing Page |
| :---: | :---: |
| 

[Image of Dashboard]
 |  |
| *The main analytics dashboard.* | *The interactive multi-item billing system.* |

## Features

* **Secure Authentication**: Role-based access control with 'Admin' and 'User' roles.
* **Inventory Management**: Full CRUD (Create, Read, Update, Delete) functionality for products with automatic stock tracking.
* **Multi-Item Billing**: A dynamic cart system for processing transactions with multiple items.
* **Interactive Dashboard**: A comprehensive dashboard featuring:
    * Daily sales metrics (Revenue, Items Sold, Invoices).
    * Charts for 7-day sales trends, top products by revenue, and sales by category.
    * Informational widgets for low stock alerts, recent transactions, and most valuable customers.
* **Sales Reporting**: An advanced, filterable report page for analyzing sales data by date range, customer, or cashier.
* **Printable Receipts**: Professional, branded, and print-friendly receipts for every transaction.
* **Responsive Design**: The layout is optimized for use on tablet devices in landscape mode.

## Technology Stack

* **Backend**: Python 3, Flask
* **Frontend**: HTML, CSS, Vanilla JavaScript, Jinja2
* **Database**: SQLite
* **Key Libraries**:
    * Werkzeug (for password hashing)
    * Chart.js (for data visualization)
    * Toastify.js (for notifications)
    * Gunicorn (for production deployment)

## Setup and Installation

Follow these steps to get the application running locally.

### Prerequisites
* Python 3.x
* `pip`

### 1. Clone the Repository
```bash
git clone [Your-GitHub-Repository-URL]
cd [Your-Repository-Folder-Name]
```

### 2. Create and Activate a Virtual Environment
* **On macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
* **On Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

### 3. Install Dependencies
Install all the required packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 4. Set Up the Database
Run the reset script to create the `POS.db` file and populate it with a default admin user and sample products.
```bash
python reset_db.py
```

### 5. Configure Environment Variables
Create a file named `.env` in the root of the project folder and add your secret key.
```
SECRET_KEY='your_own_super_secret_and_random_key'
```

### 6. Run the Application
Start the Flask development server.
```bash
flask run
```
The application will be available at `http://127.0.0.1:5000`.

## Usage

* **Admin Login**:
    * Username: `admin`
    * Password: `admin123`
* After logging in, you can add new users, manage inventory, and view all reports.