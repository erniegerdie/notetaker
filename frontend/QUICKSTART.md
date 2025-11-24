# Frontend Quick Start Guide

## Setup (1 minute)

```bash
cd frontend
npm install
```

## Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment Configuration

The app is pre-configured to connect to the backend at `http://localhost:8000`.

To change this, edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://your-backend-url:port
```

## What's Included

✅ **Drag & Drop Upload** - Upload videos with progress tracking
✅ **Real-time Status** - Automatic polling for processing updates
✅ **Video List** - View all uploaded videos with status badges
✅ **Transcription Viewer** - Read, copy, and download transcriptions
✅ **Responsive Design** - Works on mobile, tablet, and desktop
✅ **Error Handling** - User-friendly error messages
✅ **Loading States** - Skeleton screens and spinners

## Common Tasks

### Start Fresh
```bash
rm -rf node_modules .next
npm install
npm run dev
```

### Build for Production
```bash
npm run build
npm start
```

### Run Linter
```bash
npm run lint
```

## Need Help?

- Check [README.md](README.md) for full documentation
- Verify backend is running at `http://localhost:8000/docs`
- Check browser console for errors
- Ensure `.env.local` has correct `NEXT_PUBLIC_API_URL`

## Next Steps

1. Start backend: `cd ../backend && docker-compose up`
2. Upload a video through the UI
3. Watch the status change from Queued → Processing → Completed
4. View and download the transcription

Enjoy! 🎉
