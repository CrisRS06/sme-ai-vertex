# Firebase Hosting Deployment Guide

Complete guide to deploy the SME AI frontend to Firebase Hosting.

## Prerequisites

- [x] Node.js installed
- [x] Firebase CLI installed
- [x] Google Cloud project (sustained-truck-408014)

## Step-by-Step Deployment

### 1. Install Firebase CLI (if not installed)

```bash
npm install -g firebase-tools
```

Verify installation:
```bash
firebase --version
```

### 2. Login to Firebase

```bash
firebase login
```

This will open your browser for authentication.

### 3. Initialize Firebase Project

In the frontend directory:

```bash
cd frontend
firebase init hosting
```

**Configuration options:**
- **Existing project**: Select `sustained-truck-408014`
- **Public directory**: `out`
- **Configure as single-page app**: No
- **GitHub integration**: Optional (recommended for CI/CD)

### 4. Build the Application

```bash
# Build static export
npm run build
```

This creates the `out/` directory with static files.

### 5. Test Locally (Optional)

```bash
firebase serve
```

Open http://localhost:5000 to preview.

### 6. Deploy to Firebase

```bash
firebase deploy
```

**Output example:**
```
✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/sustained-truck-408014/overview
Hosting URL: https://sustained-truck-408014.web.app
```

### 7. Update Production API URL

After backend is deployed to Cloud Run, update `.env.local`:

```bash
# Example Cloud Run URL
NEXT_PUBLIC_API_URL=https://sme-ai-vertex-xyz123-uc.a.run.app
```

Then rebuild and redeploy:
```bash
npm run build
firebase deploy
```

---

## Automated Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Build
echo "📦 Building application..."
npm run build

# Deploy
echo "🔥 Deploying to Firebase..."
firebase deploy --only hosting

echo "✅ Deployment complete!"
echo "🌐 Visit: https://sustained-truck-408014.web.app"
```

Make executable:
```bash
chmod +x deploy.sh
```

Run:
```bash
./deploy.sh
```

---

## Firebase Configuration Files

### `firebase.json`
Already created. Configures hosting settings.

### `.firebaserc` (auto-created)
Links project ID:
```json
{
  "projects": {
    "default": "sustained-truck-408014"
  }
}
```

---

## Custom Domain (Optional)

### 1. Add Custom Domain in Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/project/sustained-truck-408014/hosting)
2. Click "Add custom domain"
3. Enter your domain (e.g., `sme-ai.yourcompany.com`)
4. Follow DNS verification steps

### 2. Update DNS Records

Add these records to your DNS provider:

```
Type: A
Name: @
Value: (Firebase IP addresses provided)

Type: CNAME
Name: www
Value: sustained-truck-408014.web.app
```

### 3. Wait for SSL Certificate

Firebase automatically provisions SSL certificate (can take up to 24 hours).

---

## Environment Variables

For different environments:

**Development** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**Production** (`.env.production`):
```bash
NEXT_PUBLIC_API_URL=https://your-cloudrun-url.run.app
```

Build with production env:
```bash
npm run build
```

---

## Rollback

If deployment has issues:

```bash
# List deployments
firebase hosting:releases:list

# Rollback to previous
firebase hosting:rollback
```

---

## CI/CD with GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Firebase

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install Dependencies
        run: npm install
        working-directory: ./frontend

      - name: Build
        run: npm run build
        working-directory: ./frontend

      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          channelId: live
          projectId: sustained-truck-408014
          entryPoint: ./frontend
```

---

## Monitoring

### 1. View Analytics

Firebase Console → Analytics

### 2. Performance Monitoring

Add to `app/layout.tsx`:
```typescript
import { getPerformance } from 'firebase/performance';
```

### 3. Check Bandwidth Usage

Firebase Console → Hosting → Usage

---

## Cost Estimates

Firebase Hosting **Free Tier**:
- 10 GB storage
- 360 MB/day bandwidth
- Custom domain & SSL included

**Typical usage:**
- Static site: ~50 MB
- Monthly bandwidth (100 users): ~5 GB
- **Cost: FREE** (well within limits)

---

## Troubleshooting

### Build Fails

```bash
# Clear cache
rm -rf .next out node_modules
npm install
npm run build
```

### Deployment Fails

```bash
# Re-authenticate
firebase logout
firebase login

# Try again
firebase deploy
```

### 404 Errors

Check `firebase.json` rewrites configuration.

### Slow Performance

1. Check `next.config.ts` has `output: 'export'`
2. Verify images are optimized
3. Enable CDN caching

---

## Checklist

Before deploying:
- [ ] Backend is deployed and accessible
- [ ] `.env.local` has correct API URL
- [ ] `npm run build` completes successfully
- [ ] Test locally with `firebase serve`
- [ ] Commit changes to git
- [ ] Run `firebase deploy`
- [ ] Test production site
- [ ] Verify all pages work
- [ ] Check API calls succeed

---

## Support

Issues with deployment:
1. Check [Firebase Status](https://status.firebase.google.com/)
2. Review [Firebase Docs](https://firebase.google.com/docs/hosting)
3. Check build logs: `npm run build`
4. Verify API URL in browser console

---

**Your site will be live at:**
`https://sustained-truck-408014.web.app`

**Custom domain (when configured):**
`https://your-custom-domain.com`
