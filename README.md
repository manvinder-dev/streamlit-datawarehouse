# LeadTrack CRM

A lightweight, multi-user Sales CRM built entirely in Python with Streamlit. It features secure per-user authentication, complete data isolation, and full CRUD management for Contacts, Deals, and Activities.

## Features

- **Multi-tenant Architecture:** Data is isolated per user at the SQL level.
- **Secure Authentication:** Custom login and registration system using `bcrypt` hashing.
- **Dashboard:** At-a-glance KPIs, active deals, pipeline value, and recent activities.
- **Contacts Management:** Track leads, prospects, and customers.
- **Deals Pipeline:** Manage sales stages from prospect to closed-won.
- **Activity Tracking:** Log calls, emails, and meetings with automatic overdue detection.

## Quick Start (Local Development)

```bash
# Clone the repository (replace with your repo URL)
git clone https://github.com/YOUR_USERNAME/leadtrack.git
cd leadtrack

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```
*(A local SQLite database will be created automatically on the first run).*

## Deployment

LeadTrack is built to deploy instantly on **Streamlit Community Cloud** with a **Supabase PostgreSQL** database.

1. Create a free PostgreSQL database on [Supabase](https://supabase.com).
2. Go to [Streamlit Community Cloud](https://share.streamlit.io) and deploy this repository.
3. In your Streamlit app's **Advanced Settings -> Secrets**, add:
   ```toml
   [database]
   postgres_url = "postgresql://postgres:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres"

   [auth]
   cookie_key = "a-random-32-character-secret-key"
   ```
4. Click **Deploy**. The database tables and initial seed data will be created automatically on the first boot.
