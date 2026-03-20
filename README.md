# Medical Store Management System

## LIVE DEMO (Vercel)
**LIVE LINK: https://medicines-store-db-yxfm.vercel.app/dashboard**

**Demo Login**
- Username: `admin`
- Password: `admin123`

Note: Agar aapka exact Vercel URL alag hai, is line ko update kar dena. Isko intentionally top par rakha gaya hai taki koi bhi directly open kar sake.

## Project Overview
Ye project ek **Medical Store Management + POS + Dashboard Analytics** system hai.
Goal simple tha: manual billing aur stock handling ki problem ko digital aur fast banana.

Is app me aap:
- medicines manage kar sakte ho
- sales/invoice generate kar sakte ho
- customer and supplier records maintain kar sakte ho
- low stock and expiry alerts dekh sakte ho
- dashboard pe revenue/profit analytics monitor kar sakte ho

## Why This Project
Local medical stores me common problems hoti hain:
- stock mismatch
- expiry loss
- proper sales tracking nahi
- fast billing system missing

Is project ka purpose tha in sab problems ko single system me solve karna.

## Main Features
- Secure login/logout (session based)
- Inventory CRUD (add/update/delete medicines)
- Supplier management
- Customer management
- POS billing flow with invoice
- Auto stock deduction on sale
- Dashboard KPIs (sales, medicines, low stock, net profit)
- Top products and monthly analytics charts
- Expiry and low-stock alerts
- Global search support
- Multi-store style store context (`store_id` based filtering)

## Tech Stack
- Backend: Flask
- Database: PostgreSQL (Neon compatible)
- DB Access: psycopg2 (raw SQL)
- Frontend: Jinja2 templates + JavaScript + CSS
- Charts: Chart.js
- Deployment: Vercel (`backend/wsgi.py`)

## Folder Structure (Cleaned)
```text
medical_store_project_Backend/
  backend/
    app/
      routes/
      services/
      middleware/
      database.py
      __init__.py
    database/
      sql/
        neon_setup.sql
        reset_admin.sql
        schema_cloud.sql
      scripts/
        check_schema_saas.py
        debug_saas_data.py
        debug_settings.py
        migrate_settings_saas.py
    scripts/
      check_schema_temp.py
      debug_dashboard.py
      test_endpoints.py
    run.py
    wsgi.py
    gunicorn_config.py
  database/
    scripts/
      ...migration and maintenance scripts...
  frontend/
    templates/
      layout.html
      dashboard.html
      inventory.html
      sales.html
      customers.html
      suppliers.html
      settings.html
      store_frontend.html
      invoice.html
      expiry_analytics.html
      login.html
    static/
      style.css
      store.css
      store.js
      logo.png
  DEPLOY_INSTRUCTIONS.md
  vercel.json
  requirements.txt
```

## How It Works (Simple Flow)
1. User login karta hai.
2. Session me `user_id`, `role`, `store_id` set hota hai.
3. User dashboard/inventory/sales modules access karta hai.
4. Sale create hone par invoice banta hai + stock reduce hota hai.
5. Dashboard APIs real-time metrics return karte hain.

## Local Setup
### 1. Clone
```bash
git clone <your-repo-url>
cd medical_store_project_Backend
```

### 2. Create Virtual Env
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 4. Environment Variable
Create `.env` file in root:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>
SECRET_KEY=your_secret_key
```

### 5. Run App
```bash
cd backend
python run.py
```

Open: `http://127.0.0.1:5000`

## Deployment (Vercel)
`vercel.json` already configured hai to route all traffic to Flask app:
- Entry: `backend/wsgi.py`

Required env vars on Vercel:
- `DATABASE_URL`
- `SECRET_KEY`

Detailed steps: check `DEPLOY_INSTRUCTIONS.md`

## Important API Endpoints
- `/login`
- `/dashboard`
- `/api/dashboard/stats`
- `/api/dashboard/alerts`
- `/api/dashboard/expiry`
- `/api/dashboard/top-products`
- `/api/dashboard/analytics/monthly`
- `/sales`
- `/create_sale`
- `/invoice/<invoice_id>`

## Git Remote Setup (Both Repos)
Current setup idea:
- `origin` -> first GitHub repo
- `second` -> second GitHub repo

Push to both:
```bash
git push origin main
git push second main
```

## Troubleshooting
- `DATABASE_URL missing`: `.env` ya Vercel env vars check karo
- `403 on push`: correct GitHub account auth check karo
- `not a git repository`: correct project folder me terminal kholo
- `500 on deploy`: Vercel logs + DB schema + env vars verify karo

## Author
Developed by Deep Tiwari
