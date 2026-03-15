# Deployment Instructions for Vercel

Your project is now configured for deployment to Vercel. Because this is a **database-driven application**, deployment requires two main parts:
1.  **Hosting the Application Code** (Vercel)
2.  **Hosting the Database** (Cloud PostgreSQL) - *Vercel does not host databases directly.*

## Prerequisites
- A GitHub account.
- A Vercel account (free).
- A Cloud Database account (recommend **Neon.tech** or **Supabase** - free tiers available).

---

## Step 1: Prepare the Database (Crucial!)
Since your local database (`localhost`) cannot be accessed by Vercel, you need a cloud database.

1.  **Create a Cloud Database**:
    - Sign up at [Neon.tech](https://neon.tech/) or [Supabase](https://supabase.com/).
    - Create a new project/database.
    - Copy the **Connection String** (it looks like `postgres://user:pass@host/db...`).

2.  **Migrate Your Schema**:
    You need to copy your local database structure to the cloud.
    - Open a terminal in your project root.
    - Run this command to export your local schema (if you have PostgreSQL tools installed):
      ```bash
      pg_dump -s -h localhost -U postgres medical_store_db > schema.sql
      ```
    - Use a tool like **pgAdmin** or `psql` to connect to your **NEW Cloud Database** using the connection string.
    - Run the SQL from `schema.sql` to create the tables in the cloud.

---

## Step 2: Push to GitHub
1.  Create a new repository on GitHub.
2.  Push your code:
    ```bash
    git init
    git add .
    git commit -m "Ready for deploy"
    git branch -M main
    git remote add origin <your-github-repo-url>
    git push -u origin main
    ```

---

## Step 3: Deploy to Vercel
1.  Go to [Vercel Dashboard](https://vercel.com/dashboard).
2.  Click **"Add New..."** -> **"Project"**.
3.  Import your GitHub repository.
4.  **Configure Project**:
    - **Framework Preset**: Select "Other" (or leave default).
    - **Root Directory**: `./` (default).
    - **Environment Variables**:
      - Click to add a new variable.
      - **Name**: `DATABASE_URL`
      - **Value**: Paste your Cloud Database Connection String (from Step 1).
      - Add another variable:
        - **Name**: `SECRET_KEY`
        - **Value**: Any random long string (e.g., `s3cr3t_k3y_12345`).

5.  Click **Deploy**.

---

## Verification
- Once deployed, Vercel will give you a URL (e.g., `medical-store.vercel.app`).
- Visit the URL.
- Log in with your admin credentials (you may need to manually insert an admin user into your cloud database if you didn't export data).

## Troubleshooting
- **500 Error**: Check Vercel **Logs** tab. It usually means `DATABASE_URL` is wrong or the database tables don't exist.
- **Static Files 404**: Ensures your `vercel.json` is in the root (I have created it for you).

## SaaS & Responsiveness Check
- **Responsiveness**: Your CSS includes `@media (max-width: 768px)` blocks, ensuring tablets and phones render the dashboard correctly (sidebar toggles, grids stack).
- **SaaS Readiness**: Your backend code (`store_id` checks) supports multi-tenancy properly. Ensure every table has `store_id` if you plan to host multiple pharmacies on one DB.
