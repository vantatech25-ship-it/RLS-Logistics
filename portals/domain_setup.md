# Custom Domain Setup Guide: RLS GNN Dashboard

To point your custom company domain (e.g., `dashboard.rlslogistics.co.za`) to this system, follow these steps.

## 1. Choose your Domain
Decide if you want a **subdomain** (recommended) or a **root domain**:
- **Subdomain**: `dashboard.yourcompany.co.za`
- **Root Domain**: `yourcompany.co.za`

## 2. DNS Configuration
Log in to your domain registrar (GoDaddy, Bluehost, Namecheap, etc.) and add the following records:

### For a Subdomain (e.g., dashboard)
| Type | Host | Value |
| :--- | :--- | :--- |
| **CNAME** | `dashboard` | `rls-system.onrender.com` |

### For a Root Domain
| Type | Host | Value |
| :--- | :--- | :--- |
| **ANAME / ALIAS** | `@` | `rls-system.onrender.com` |

> [!IMPORTANT]
> **TTL (Time to Live)**: We recommend setting the TTL to **3600** (1 hour).

## 3. Activate in Render Dashboard
1. Go to your **[Render Dashboard](https://dashboard.render.com)**.
2. Select your **RLS Web Service**.
3. Go to **Settings** > **Custom Domains**.
4. Click **"Add Custom Domain"** and enter your domain name.
5. Render will verify the DNS records and issue a **free SSL certificate** automatically.

## 4. Verification Check
Once active, your PWA will be fully functional on your custom branding. You can verify the status by visiting:
`https://your-custom-domain.com/.well-known/assetlinks.json` (Render handles this under the hood).

---
**Note**: DNS changes can take anywhere from 5 minutes to 24 hours to propagate globally.
