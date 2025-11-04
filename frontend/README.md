# SME AI Frontend

Modern Next.js frontend for the SME AI Injection Molding Feasibility Analysis System.

## Features

- ✅ **Dashboard** - Overview of all analyses and system stats
- ✅ **Drawing Analysis** - Upload and analyze technical drawings
- ✅ **Knowledge Base** - Manage manuals and specifications
- ✅ **Results Viewer** - Browse and download analysis reports
- ✅ **Modern UI** - Tailwind CSS with dark mode support
- ✅ **TypeScript** - Full type safety
- ✅ **Responsive** - Mobile-friendly design

## Tech Stack

- **Next.js 16** - React framework with SSR
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Firebase Hosting** - Fast CDN deployment

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Dashboard (home)
│   ├── analyze/           # Drawing analysis page
│   ├── knowledge-base/    # Manual management
│   └── results/           # Results viewer
├── components/            # Reusable UI components
├── lib/                   # Utilities and API client
│   └── api.ts            # Backend API integration
├── public/               # Static assets
└── ...config files
```

## API Integration

All API calls go through `lib/api.ts`:

```typescript
import { analysisAPI, knowledgeBaseAPI } from '@/lib/api';

// Upload drawing
const result = await analysisAPI.uploadDrawing(file, 'Project Name', 'flash');

// Upload manual
await knowledgeBaseAPI.uploadDocument(file, 'manual');
```

## Deployment to Firebase

### 1. Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### 2. Initialize Firebase

```bash
firebase init hosting
```

Select:
- **Public directory**: `out`
- **Single-page app**: No
- **GitHub integration**: Optional

### 3. Build & Deploy

```bash
# Build static export
npm run build

# Deploy to Firebase
firebase deploy
```

Your site will be live at: `https://your-project.web.app`

### 4. Update Production API URL

In production, update `.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://your-cloudrun-url.run.app
```

Then rebuild and redeploy.

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build production static export
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8080` |

## Pages

### Dashboard (`/`)
- System overview with stats
- Quick access to main features
- Feature highlights

### Analyze Drawing (`/analyze`)
- Upload PDF drawings
- Select quality mode (Flash/Pro)
- Track analysis progress
- View results when complete

### Knowledge Base (`/knowledge-base`)
- Upload manuals, specifications
- List all documents
- Delete documents
- Automatic RAG indexing

### Results (`/results`)
- List all analyses
- View status and exceptions
- Download reports
- Track history

## Customization

### Colors

Edit `tailwind.config.ts`:
```typescript
colors: {
  primary: { 500: '#your-color' }
}
```

### Logo

Replace logo in `app/page.tsx`:
```typescript
<div className="w-10 h-10 ...">
  <span>Your Logo</span>
</div>
```

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next out
npm run build
```

### API Connection Errors

1. Check backend is running: `curl http://localhost:8080/health`
2. Verify `.env.local` has correct API URL
3. Check CORS is enabled in backend

## Production Checklist

- [ ] Update `NEXT_PUBLIC_API_URL` to production backend
- [ ] Build static export: `npm run build`
- [ ] Test built site: check `out/` directory
- [ ] Deploy to Firebase: `firebase deploy`
- [ ] Verify SSL certificate (auto with Firebase)
- [ ] Test all features in production
- [ ] Monitor performance

## Support

For issues or questions:
1. Check backend logs
2. Check browser console for errors
3. Verify API endpoints in Swagger: `http://localhost:8080/docs`

---

**Built with ❤️ for SME AI**
