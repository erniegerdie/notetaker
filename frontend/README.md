# Video Transcription Frontend

Modern Next.js 14 frontend application for video transcription with shadcn/ui components and real-time status polling.

## Features

- 🎬 **Drag-and-drop video upload** with file validation
- 📊 **Real-time status polling** for processing updates
- 📝 **Transcription viewer** with copy and download functionality
- 🎨 **Modern UI** with shadcn/ui and Tailwind CSS
- ⚡ **Fast performance** with Next.js App Router
- 📱 **Responsive design** for all devices
- 🔄 **Automatic caching** with TanStack Query

## Tech Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI + Tailwind)
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Form Validation**: Zod
- **File Upload**: react-dropzone
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (or configure `NEXT_PUBLIC_API_URL`)

### Installation

1. Install dependencies:

```bash
npm install
```

2. Configure environment variables:

```bash
# Copy example env file
cp .env.example .env.local

# Edit .env.local and set your backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:

```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Home page (upload + list)
│   ├── videos/[id]/         # Video detail page
│   ├── globals.css          # Global styles
│   ├── error.tsx            # Error boundary
│   └── not-found.tsx        # 404 page
│
├── components/              # React components
│   ├── ui/                  # shadcn/ui components
│   ├── video-upload.tsx     # Upload component
│   ├── video-list.tsx       # List component
│   ├── video-card.tsx       # Card component
│   ├── status-badge.tsx     # Status indicator
│   └── transcription-viewer.tsx  # Transcription display
│
├── hooks/                   # Custom React hooks
│   ├── use-video-upload.ts
│   ├── use-video-status.ts
│   ├── use-transcription.ts
│   ├── use-video-list.ts
│   └── use-toast.ts
│
├── lib/                     # Utilities and configuration
│   ├── api.ts               # Axios client
│   ├── types.ts             # TypeScript types
│   ├── constants.ts         # App constants
│   ├── validators.ts        # Zod schemas
│   └── utils.ts             # Helper functions
│
└── providers/               # Context providers
    └── query-provider.tsx   # TanStack Query setup
```

## Available Scripts

```bash
# Development
npm run dev          # Start dev server (localhost:3000)

# Production
npm run build        # Build for production
npm start            # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint errors
```

## Key Features Explained

### Video Upload

- Drag-and-drop interface with visual feedback
- File validation (format, size)
- Upload progress tracking
- Automatic navigation to video detail page

### Status Polling

- Automatic polling every 2 seconds during processing
- Smart polling that stops when completed/failed
- Background refetching when tab is active
- Visual status indicators (Queued, Processing, Completed, Failed)

### Transcription Viewer

- Clean, readable layout for long transcriptions
- One-click copy to clipboard
- Download as text file
- Processing metadata display (model, time, date)

## Environment Variables

Create a `.env.local` file:

```bash
# Backend API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=false
```

## Supported Video Formats

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WebM (.webm)

**Maximum file size**: 500MB

## API Integration

The frontend communicates with the backend API:

- `POST /api/videos/upload` - Upload video
- `GET /api/videos/{id}/status` - Get processing status
- `GET /api/videos/{id}/transcription` - Get transcription
- `GET /api/videos` - List all videos

## Troubleshooting

### Backend Connection Issues

If you see connection errors:

1. Verify backend is running: `curl http://localhost:8000/docs`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for CORS errors

### Upload Failures

If uploads fail:

1. Check file size (max 500MB)
2. Verify file format is supported
3. Check backend logs for errors
4. Ensure sufficient disk space

### Status Not Updating

If status remains stuck:

1. Check browser console for polling errors
2. Verify backend is processing videos
3. Check network tab in DevTools
4. Try refreshing the page

## Development

### Adding New Components

```bash
# Example: Add a new shadcn/ui component
npx shadcn-ui@latest add dialog
```

### Customizing Theme

Edit `tailwind.config.ts` and `app/globals.css` to customize colors, fonts, and other theme variables.

### API Changes

If backend API changes:

1. Update types in `lib/types.ts`
2. Update API calls in `hooks/`
3. Update components as needed

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables
4. Deploy

### Docker

```bash
# Build
docker build -t notetaker-frontend .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  notetaker-frontend
```

### Other Platforms

The app can be deployed to any platform supporting Next.js:

- Netlify
- AWS Amplify
- Railway
- Fly.io

## Performance Optimization

- **Code Splitting**: Automatic with Next.js
- **Image Optimization**: Next.js Image component ready
- **Query Caching**: Intelligent caching with TanStack Query
- **Lazy Loading**: Components loaded as needed
- **Background Refetching**: Always fresh data

## Contributing

1. Follow existing code style
2. Use TypeScript for type safety
3. Test all changes locally
4. Update documentation as needed

## License

MIT
