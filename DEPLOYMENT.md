# Kings Cut Addis — Production deployment guide

## 1. Message to send Techno Bros (copy-paste)

Subject: VPS / Cloud server for Python FastAPI + PostgreSQL + Telegram bot + React apps

Hello,

I need a Linux server for a small business app with this stack:

- Python FastAPI API (uvicorn, long-running)
- Telegram bot (long-running Python process)
- PostgreSQL database on the same server (or managed Postgres if you offer it)
- Two React (Vite) static frontends behind Nginx
- HTTPS (Let’s Encrypt) on a domain you provide / I already have free

Please confirm:

1. OS available: Ubuntu 22.04 or 24.04 LTS preferred, with full SSH (root or sudo) access?
2. Can I run custom systemd services (uvicorn + Telegram bot), not only cPanel/Passenger apps?
3. Can I install PostgreSQL, Python 3.11+, Node.js 20, Nginx, Certbot myself?
4. Outbound HTTPS allowed to api.telegram.org? Any firewall restrictions?
5. Public IPv4 dedicated to my server? Ports 22, 80, 443 open (22 restricted to my IP if possible)?
6. For Cloud plans: you list “no backup” — can you add weekly snapshots, or disk space for my own DB dumps?
7. Recommended plan for: Nginx + Postgres + FastAPI + bot + static sites. I believe I need at least 2 GB RAM. Is Cloud SMALL (2 GB) suitable, or should I take VPS / upgrade RAM?
8. Free domain: can you point DNS A records (api / admin / app subdomains) to my server IP and help with SSL if needed?
9. Setup time after payment, and how I receive SSH credentials?

Thank you.

---

## 2. Target production layout

Use your free domain, e.g. `kingscutaddis.com`:

| Host | Purpose |
|------|---------|
| `api.kingscutaddis.com` | FastAPI + `/uploads` |
| `admin.kingscutaddis.com` | Staff dashboard (built React) |
| `app.kingscutaddis.com` | Telegram Mini App (built React, **must be HTTPS**) |

Same server also runs:

- PostgreSQL
- systemd: `kingscut-api`
- systemd: `kingscut-bot`

---

## 3. What to prepare on your PC before server day

1. Strong passwords written down (DB, admin user, SSH).
2. Telegram bot token from BotFather.
3. Decide final Mini App URL: `https://app.YOURDOMAIN.com`
4. Build frontends locally (optional if you build on the server):

```bash
cd admin-dashboard
npm ci
npm run build

cd ../mini-app
# set API URL for production build
# Windows PowerShell:
$env:VITE_API_BASE_URL="https://api.YOURDOMAIN.com"
npm ci
npm run build
```

5. Production `.env` values (never commit this file):

```env
DATABASE_URL=postgresql://kingscut:STRONG_DB_PASSWORD@127.0.0.1:5432/KingsCutAddis
SECRET_KEY=long-random-string-at-least-48-chars
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=14

TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_MINI_APP_URL=https://app.YOURDOMAIN.com

ADMIN_EMAIL=you@example.com
ADMIN_PASSWORD=ChangeThisImmediately!
ADMIN_FIRST_NAME=Owner
ADMIN_LAST_NAME=Admin
ADMIN_PHONE=0911000000

UPLOAD_DIR=/var/www/kingscut/uploads
```

Also set CORS in `app/config.py` or via env once you support it — production origins must include:

- `https://admin.YOURDOMAIN.com`
- `https://app.YOURDOMAIN.com`

---

## 4. Server setup (Ubuntu, SSH only — no GUI)

Connect:

```bash
ssh root@YOUR_SERVER_IP
```

### 4.1 System packages

```bash
apt update && apt upgrade -y
apt install -y nginx postgresql postgresql-contrib python3 python3-venv python3-pip \
  certbot python3-certbot-nginx git curl ufw

# Node 20 (for building frontends on server, optional)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

### 4.2 Firewall

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

### 4.3 App user and folders

```bash
adduser --disabled-password --gecos "" kingscut
mkdir -p /var/www/kingscut/{app,admin,mini-app,uploads/promotions}
chown -R kingscut:kingscut /var/www/kingscut
```

Upload code (from your PC), e.g. with scp/rsync, into `/var/www/kingscut/app` (repo root contents),  
and put builds into:

- `/var/www/kingscut/admin` ← `admin-dashboard/dist/*`
- `/var/www/kingscut/mini-app` ← `mini-app/dist/*`

### 4.4 PostgreSQL

```bash
sudo -u postgres psql <<'SQL'
CREATE USER kingscut WITH PASSWORD 'STRONG_DB_PASSWORD';
CREATE DATABASE "KingsCutAddis" OWNER kingscut;
GRANT ALL PRIVILEGES ON DATABASE "KingsCutAddis" TO kingscut;
SQL
```

Then as `kingscut` user:

```bash
su - kingscut
cd /var/www/kingscut/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# ensure aiosmtplib is installed if you use staff invite emails:
# pip install aiosmtplib

cp .env.example .env
nano .env   # paste production values

# Point Alembic at DATABASE_URL (prefer editing alembic to use settings;
# for first deploy you can also set sqlalchemy.url temporarily)
alembic upgrade head
# If you use baseline schema.sql for a fresh DB, apply that first, then alembic.

python scripts/seed_admin.py
python scripts/seed_services.py   # optional
python scripts/seed_loyalty_rules.py  # optional
```

### 4.5 systemd — API

Create `/etc/systemd/system/kingscut-api.service`:

```ini
[Unit]
Description=Kings Cut FastAPI
After=network.target postgresql.service

[Service]
User=kingscut
Group=kingscut
WorkingDirectory=/var/www/kingscut/app
EnvironmentFile=/var/www/kingscut/app/.env
ExecStart=/var/www/kingscut/app/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.6 systemd — Bot

Create `/etc/systemd/system/kingscut-bot.service`:

```ini
[Unit]
Description=Kings Cut Telegram Bot
After=network.target kingscut-api.service

[Service]
User=kingscut
Group=kingscut
WorkingDirectory=/var/www/kingscut/app
EnvironmentFile=/var/www/kingscut/app/.env
ExecStart=/var/www/kingscut/app/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
systemctl daemon-reload
systemctl enable --now kingscut-api kingscut-bot
systemctl status kingscut-api kingscut-bot
```

### 4.7 Nginx (HTTP first, then SSL)

`/etc/nginx/sites-available/kingscut`:

```nginx
# API
server {
    listen 80;
    server_name api.YOURDOMAIN.com;

    client_max_body_size 55M;

    location /uploads/ {
        alias /var/www/kingscut/uploads/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Admin dashboard
server {
    listen 80;
    server_name admin.YOURDOMAIN.com;
    root /var/www/kingscut/admin;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Mini App
server {
    listen 80;
    server_name app.YOURDOMAIN.com;
    root /var/www/kingscut/mini-app;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/kingscut /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

Point DNS A records for `api`, `admin`, `app` to the server IP. Wait until they resolve, then:

```bash
certbot --nginx -d api.YOURDOMAIN.com -d admin.YOURDOMAIN.com -d app.YOURDOMAIN.com
```

### 4.8 BotFather

1. Set Mini App / menu button URL to `https://app.YOURDOMAIN.com`
2. `systemctl restart kingscut-bot`

### 4.9 Smoke test

- `https://api.YOURDOMAIN.com/health` → `{"status":"ok"}`
- Open `https://admin.YOURDOMAIN.com` → login
- Open Mini App from Telegram (not a plain browser link)
- Log a visit, check QR check-in, promotion media if used

---

## 5. After go-live checklist

- [ ] Changed default admin password
- [ ] `COOKIE_SECURE=true`
- [ ] CORS only allows your real HTTPS fronts
- [ ] Strong `SECRET_KEY`
- [ ] `/docs` disabled or blocked in production (optional Nginx rule)
- [ ] Weekly Postgres backup cron, e.g.:

```bash
# as root crontab
0 2 * * 0 pg_dump -U kingscut KingsCutAddis | gzip > /var/backups/kingscut-$(date +\%F).sql.gz
```

- [ ] `journalctl -u kingscut-api -f` and `journalctl -u kingscut-bot -f` look clean

---

## 6. Useful commands

```bash
systemctl restart kingscut-api
systemctl restart kingscut-bot
systemctl status kingscut-api kingscut-bot nginx postgresql
journalctl -u kingscut-api -n 100 --no-pager
journalctl -u kingscut-bot -n 100 --no-pager
```

---

## 7. Plan reminder (Techno Bros sheet)

| Plan | Note for this app |
|------|-------------------|
| Cloud ENTRY 1 GB | Risky — Postgres + API + bot will struggle |
| **Cloud SMALL 2 GB** | Best cloud option on the sheet; ask about backups |
| VPS 1 GB + cPanel | Easier UI, still light on RAM; confirm systemd Python apps OK |
| Dedicated | Unnecessary for now |

Start with **2 GB RAM + Ubuntu + SSH**, then scale up if the shop grows.
