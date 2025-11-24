# Frontend Implementation Plan

## Project Overview

Modern web frontend for the video transcription application using Next.js 14+, TypeScript, and shadcn/ui. Provides intuitive interface for video upload, processing status tracking, and transcription viewing.

## Technology Stack

### Core Framework
- **Next.js 14+**: React framework with App Router for modern routing and server components
- **TypeScript**: Type-safe development with full IDE support
- **React 18+**: Latest React features including concurrent rendering

### UI & Styling
- **shadcn/ui**: High-quality, accessible component library built on Radix UI
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Radix UI**: Headless UI primitives for accessibility
- **Lucide Icons**: Modern icon library for UI elements

### State Management
- **TanStack Query (React Query)**: Server state management with caching, polling, and optimistic updates
- **React Context**: Minimal client state for theme, notifications
- **Zustand** (optional): Lightweight state management if needed

### Form & Validation
- **React Hook Form**: Performant form handling with minimal re-renders
- **Zod**: TypeScript-first schema validation
- **Custom file upload**: Drag-and-drop with progress tracking

### API Communication
- **Axios**: HTTP client with interceptors for error handling
- **TanStack Query**: Automatic polling, caching, background refetching

## Project Structure

```
frontend/
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                # Root layout with providers
│   │   ├── page.tsx                  # Home page (upload + video list)
│   │   ├── globals.css               # Global styles and Tailwind
│   │   ├── videos/
│   │   │   └── [id]/
│   │   │       └── page.tsx          # Video detail page with transcription
│   │   └── error.tsx                 # Global error boundary
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── progress.tsx
│   │   │
│   │   ├── video-upload.tsx          # Drag-and-drop upload component
│   │   ├── video-list.tsx            # List of all videos with status
│   │   ├── video-card.tsx            # Individual video item in list
│   │   ├── transcription-viewer.tsx  # Transcription display with actions
│   │   ├── status-badge.tsx          # Status indicator (uploaded/processing/completed/failed)
│   │   ├── status-poller.tsx         # Real-time status polling component
│   │   ├── copy-button.tsx           # Copy to clipboard button
│   │   └── error-display.tsx         # Error message display
│   │
│   ├── lib/
│   │   ├── api.ts                    # Backend API client (Axios instance)
│   │   ├── utils.ts                  # Utility functions (cn, formatters)
│   │   ├── validators.ts             # Zod schemas for validation
│   │   ├── constants.ts              # App constants (file size limits, formats)
│   │   └── types.ts                  # TypeScript type definitions
│   │
│   ├── hooks/
│   │   ├── use-video-upload.ts       # Upload mutation with progress
│   │   ├── use-video-status.ts       # Status query with polling
│   │   ├── use-transcription.ts      # Transcription data query
│   │   ├── use-video-list.ts         # List all videos query
│   │   └── use-toast.ts              # Toast notification hook
│   │
│   └── providers/
│       ├── query-provider.tsx        # TanStack Query provider
│       └── toast-provider.tsx        # Toast notification provider
│
├── public/
│   └── favicon.ico
│
├── .env.local                         # Environment variables
├── .env.example                       # Example environment variables
├── components.json                    # shadcn/ui configuration
├── tailwind.config.ts                 # Tailwind configuration
├── tsconfig.json                      # TypeScript configuration
├── next.config.js                     # Next.js configuration
├── package.json                       # Dependencies
└── README.md                          # Setup and usage documentation
```

## Core Features

### 1. Video Upload Interface
- **Drag-and-drop zone** with visual feedback
- **File validation**: Format (mp4, avi, mov, mkv, webm), size (max 500MB)
- **Upload progress bar** with percentage and file size
- **Multiple file format support** with clear error messages
- **Immediate feedback** on upload success/failure

### 2. Real-Time Status Tracking
- **Automatic polling** for processing status using TanStack Query
- **Visual status indicators**:
  - `uploaded` → Gray badge, "Waiting to process"
  - `processing` → Blue badge with loading spinner, "Processing..."
  - `completed` → Green badge with checkmark, "Completed"
  - `failed` → Red badge with error icon, "Failed"
- **Smart polling**: Poll every 2s during processing, stop when completed/failed
- **Background refetching** with configurable intervals

### 3. Video List View
- **Card-based grid layout** responsive across devices
- **Status filtering** (optional): Show only completed, processing, or failed videos
- **Sorting options**: By upload date (newest first)
- **Quick actions**: View transcription, delete video (future)
- **Empty state** with helpful upload prompt

### 4. Transcription Viewer
- **Clean reading layout** with proper typography
- **Metadata display**: Model used, processing time, upload date
- **Copy to clipboard** button with success feedback
- **Download as text file** functionality
- **Responsive text area** for long transcriptions
- **Back navigation** to video list

### 5. Error Handling & UX
- **Toast notifications** for all actions (upload, errors)
- **Loading states** with skeleton screens
- **Error boundaries** for graceful degradation
- **Network error handling** with retry options
- **User-friendly error messages** (no raw API errors)

## API Integration

### Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/videos/upload` | POST | Upload video file, returns `video_id` |
| `/api/videos/{id}/status` | GET | Poll processing status |
| `/api/videos/{id}/transcription` | GET | Retrieve completed transcription |
| `/api/videos` | GET | List all uploaded videos |

### API Client Configuration

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Unknown error';
    console.error(`[API Error] ${error.config?.url}:`, message);
    return Promise.reject(new Error(message));
  }
);

export default api;
```

### Custom Hooks Implementation

#### useVideoUpload Hook
```typescript
// hooks/use-video-upload.ts
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { AxiosProgressEvent } from 'axios';

interface UploadResponse {
  id: string;
  filename: string;
  status: string;
  status_url: string;
}

export function useVideoUpload() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post<UploadResponse>(
        '/api/videos/upload',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            // Update progress state
          },
        }
      );

      return data;
    },
  });
}
```

#### useVideoStatus Hook (with polling)
```typescript
// hooks/use-video-status.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface VideoStatus {
  id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
}

export function useVideoStatus(videoId: string | null) {
  return useQuery({
    queryKey: ['video-status', videoId],
    queryFn: async () => {
      const { data } = await api.get<VideoStatus>(
        `/api/videos/${videoId}/status`
      );
      return data;
    },
    enabled: !!videoId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if processing, stop if completed/failed
      if (data?.status === 'processing' || data?.status === 'uploaded') {
        return 2000;
      }
      return false;
    },
    refetchOnWindowFocus: true,
  });
}
```

#### useTranscription Hook
```typescript
// hooks/use-transcription.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface Transcription {
  video_id: string;
  transcript_text: string;
  model_used: string;
  processing_time: string;
  created_at: string;
}

export function useTranscription(videoId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['transcription', videoId],
    queryFn: async () => {
      const { data } = await api.get<Transcription>(
        `/api/videos/${videoId}/transcription`
      );
      return data;
    },
    enabled: !!videoId && enabled,
    retry: false, // Don't retry if transcription isn't ready
  });
}
```

## Component Design

### VideoUpload Component
```typescript
// components/video-upload.tsx
'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileVideo, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useVideoUpload } from '@/hooks/use-video-upload';
import { useToast } from '@/hooks/use-toast';
import { ALLOWED_VIDEO_FORMATS, MAX_FILE_SIZE_MB } from '@/lib/constants';

export function VideoUpload({ onUploadSuccess }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { mutate: uploadVideo, isPending } = useVideoUpload();
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ALLOWED_VIDEO_FORMATS.map(fmt => `.${fmt}`),
    },
    maxSize: MAX_FILE_SIZE_MB * 1024 * 1024,
    multiple: false,
  });

  const handleUpload = () => {
    if (!selectedFile) return;

    uploadVideo(selectedFile, {
      onSuccess: (data) => {
        toast({
          title: 'Upload successful',
          description: `${selectedFile.name} is being processed`,
        });
        onUploadSuccess(data.id);
        setSelectedFile(null);
      },
      onError: (error) => {
        toast({
          title: 'Upload failed',
          description: error.message,
          variant: 'destructive',
        });
      },
    });
  };

  return (
    <Card className="p-6">
      {/* Drag-and-drop zone, file info, upload button */}
    </Card>
  );
}
```

### StatusBadge Component
```typescript
// components/status-badge.tsx
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';

type Status = 'uploaded' | 'processing' | 'completed' | 'failed';

export function StatusBadge({ status }: { status: Status }) {
  const config = {
    uploaded: {
      label: 'Queued',
      icon: Clock,
      variant: 'secondary' as const,
    },
    processing: {
      label: 'Processing',
      icon: Loader2,
      variant: 'default' as const,
      className: 'animate-spin',
    },
    completed: {
      label: 'Completed',
      icon: CheckCircle2,
      variant: 'success' as const,
    },
    failed: {
      label: 'Failed',
      icon: XCircle,
      variant: 'destructive' as const,
    },
  };

  const { label, icon: Icon, variant, className } = config[status];

  return (
    <Badge variant={variant}>
      <Icon className={cn('mr-1 h-3 w-3', className)} />
      {label}
    </Badge>
  );
}
```

### TranscriptionViewer Component
```typescript
// components/transcription-viewer.tsx
'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, Download } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Props {
  transcription: {
    transcript_text: string;
    model_used: string;
    processing_time: string;
    created_at: string;
  };
  filename: string;
}

export function TranscriptionViewer({ transcription, filename }: Props) {
  const { toast } = useToast();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(transcription.transcript_text);
    toast({ title: 'Copied to clipboard' });
  };

  const handleDownload = () => {
    const blob = new Blob([transcription.transcript_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^/.]+$/, '')}_transcript.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Transcription</h2>
          <p className="text-sm text-muted-foreground">
            Model: {transcription.model_used} •
            Processing time: {transcription.processing_time}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="mr-2 h-4 w-4" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </Button>
        </div>
      </div>
      <div className="prose prose-sm max-w-none rounded-lg bg-muted p-4">
        <p className="whitespace-pre-wrap">{transcription.transcript_text}</p>
      </div>
    </Card>
  );
}
```

## Implementation Steps

### Phase 1: Project Setup ⏱️ ~30 minutes

1. **Initialize Next.js project**:
   ```bash
   cd frontend
   npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
   ```

2. **Install dependencies**:
   ```bash
   npm install @tanstack/react-query axios zod react-hook-form @hookform/resolvers
   npm install lucide-react clsx tailwind-merge
   npm install react-dropzone
   ```

3. **Install shadcn/ui**:
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card badge input label textarea skeleton toast dialog progress
   ```

4. **Configure environment variables**:
   ```bash
   # .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. **Set up project structure**:
   ```bash
   mkdir -p components/ui hooks lib providers
   touch lib/{api,utils,validators,constants,types}.ts
   ```

### Phase 2: API Client & Types ⏱️ ~30 minutes

1. **Create API client** (`lib/api.ts`):
   - Configure Axios instance with base URL
   - Add request/response interceptors
   - Error handling with user-friendly messages

2. **Define TypeScript types** (`lib/types.ts`):
   - Video, VideoStatus, Transcription interfaces
   - API response types
   - Form data types

3. **Create validation schemas** (`lib/validators.ts`):
   - Zod schemas for file upload validation
   - File size and format validators
   - Error message definitions

4. **Add constants** (`lib/constants.ts`):
   - Allowed video formats array
   - Max file size constant
   - Polling interval configuration
   - Status display configurations

### Phase 3: Custom Hooks ⏱️ ~45 minutes

1. **Implement useVideoUpload**:
   - Mutation for file upload with FormData
   - Upload progress tracking
   - Success/error callbacks
   - File validation before upload

2. **Implement useVideoStatus**:
   - Query with automatic polling
   - Conditional refetch based on status
   - Stop polling when completed/failed
   - Background refetching support

3. **Implement useTranscription**:
   - Query for transcription data
   - Conditional enabling (only when status is completed)
   - Error handling for premature requests

4. **Implement useVideoList**:
   - Query for all videos
   - Sorting by upload date
   - Periodic background refresh

### Phase 4: Core Components ⏱️ ~1.5 hours

1. **VideoUpload Component**:
   - Drag-and-drop zone using react-dropzone
   - File validation and preview
   - Upload progress bar
   - Success/error feedback
   - Clear/cancel functionality

2. **StatusBadge Component**:
   - Status-specific icons and colors
   - Loading animation for processing
   - Consistent styling across app

3. **VideoCard Component**:
   - Display video metadata
   - Status indicator
   - Click to view transcription
   - Hover effects and interactions

4. **VideoList Component**:
   - Grid layout with responsive columns
   - Loading skeletons
   - Empty state with upload prompt
   - Error state handling

5. **TranscriptionViewer Component**:
   - Display transcription text
   - Metadata display (model, time)
   - Copy to clipboard button
   - Download as text file
   - Responsive layout

6. **StatusPoller Component**:
   - Real-time status updates
   - Visual processing indicator
   - Automatic redirect when completed
   - Error display for failures

### Phase 5: Pages & Routing ⏱️ ~45 minutes

1. **Root Layout** (`app/layout.tsx`):
   - TanStack Query provider setup
   - Toast notification provider
   - Global styles and fonts
   - Metadata configuration

2. **Home Page** (`app/page.tsx`):
   - VideoUpload component
   - VideoList component
   - Page header and description
   - Responsive two-column layout

3. **Video Detail Page** (`app/videos/[id]/page.tsx`):
   - Fetch video status
   - StatusPoller for real-time updates
   - TranscriptionViewer when completed
   - Loading states
   - Error handling
   - Back navigation

4. **Error Page** (`app/error.tsx`):
   - Global error boundary
   - User-friendly error message
   - Reset/retry functionality

### Phase 6: Providers & Configuration ⏱️ ~30 minutes

1. **Query Provider** (`providers/query-provider.tsx`):
   - TanStack Query setup
   - Default query options
   - Devtools configuration (dev only)
   - Error handling defaults

2. **Toast Provider** (`providers/toast-provider.tsx`):
   - shadcn toast setup
   - Global toast configuration
   - Toast positioning and styling

3. **Tailwind Configuration**:
   - Custom theme colors
   - Typography plugin
   - Animation configurations
   - Responsive breakpoints

4. **Next.js Configuration**:
   - API proxy for CORS (if needed)
   - Image optimization
   - Build optimizations

### Phase 7: Polish & UX Improvements ⏱️ ~45 minutes

1. **Loading States**:
   - Skeleton screens for video list
   - Loading spinners for actions
   - Progress indicators for uploads
   - Shimmer effects

2. **Animations**:
   - Fade-in for page transitions
   - Smooth status badge changes
   - Upload progress animation
   - Toast slide-in effects

3. **Responsive Design**:
   - Mobile-first approach
   - Tablet breakpoint optimizations
   - Desktop multi-column layout
   - Touch-friendly interactions

4. **Accessibility**:
   - ARIA labels for interactive elements
   - Keyboard navigation support
   - Focus management
   - Screen reader announcements

5. **Error Handling**:
   - Network error retry
   - Timeout handling
   - User-friendly error messages
   - Toast notifications for all actions

### Phase 8: Testing & Documentation ⏱️ ~30 minutes

1. **Manual Testing Checklist**:
   - Upload various video formats
   - Test file size limits
   - Verify status polling
   - Check transcription display
   - Test copy/download functionality
   - Mobile responsiveness
   - Error scenarios

2. **Create README.md**:
   - Quick start instructions
   - Environment setup
   - Development workflow
   - Build and deployment
   - Troubleshooting guide

3. **Component Documentation**:
   - Props interfaces
   - Usage examples
   - Styling customization

## Environment Variables

Create `.env.local`:
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=false
```

Create `.env.example`:
```bash
# Backend API URL (update for production)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Key Design Decisions

### Why Next.js 14+ App Router?
- **Server Components**: Improved performance with RSC
- **Modern routing**: File-based routing with layouts
- **Built-in optimization**: Image, font, script optimization
- **TypeScript first**: Excellent TypeScript support
- **Production ready**: Battle-tested framework

### Why shadcn/ui?
- **Copy-paste components**: Own the code, no black box
- **Radix UI foundation**: Accessible, production-ready primitives
- **Tailwind integration**: Consistent styling system
- **Customizable**: Easy to modify for brand requirements
- **Modern design**: Beautiful default styling

### Why TanStack Query?
- **Automatic caching**: Reduces unnecessary API calls
- **Background refetching**: Always fresh data
- **Polling support**: Perfect for status tracking
- **Optimistic updates**: Better UX with instant feedback
- **DevTools**: Excellent debugging experience

### Status Polling Strategy
- **Poll interval**: 2 seconds during processing
- **Smart polling**: Stop when completed/failed
- **Background refetch**: 30 seconds when tab is active
- **Pause when hidden**: Save resources when tab inactive
- **Retry logic**: Automatic retry on network errors

## Responsive Design Breakpoints

```css
/* Tailwind breakpoints */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet portrait */
lg: 1024px  /* Tablet landscape / Small desktop */
xl: 1280px  /* Desktop */
2xl: 1536px /* Large desktop */
```

**Layout Strategy**:
- **Mobile**: Single column, full-width cards
- **Tablet**: Two-column grid for video list
- **Desktop**: Three-column grid, sidebar layout option

## Performance Optimizations

1. **Code Splitting**: Automatic with Next.js App Router
2. **Image Optimization**: Next.js Image component (if thumbnails added)
3. **React Query Caching**: Reduce API calls with intelligent caching
4. **Lazy Loading**: Load transcription viewer only when needed
5. **Debounced Search**: If search feature added
6. **Virtualization**: If video list grows large (use `@tanstack/react-virtual`)

## Future Enhancements (Out of Scope for MVP)

- Video thumbnail generation and display
- Search and filter videos by filename or content
- Export transcription in multiple formats (SRT, VTT, JSON)
- Edit transcription inline
- Share transcription via link
- Dark mode toggle
- User authentication and authorization
- Batch upload multiple videos
- Video playback with synchronized transcription
- Transcription editing with timestamps
- Mobile app (React Native)

## Testing Strategy (Future)

- **Unit Tests**: Vitest for components and utilities
- **Integration Tests**: Testing Library for user interactions
- **E2E Tests**: Playwright for critical user flows
- **API Mocking**: MSW for development and testing
- **Visual Regression**: Chromatic for UI consistency

## Deployment Considerations

### Vercel (Recommended)
- Native Next.js support
- Automatic preview deployments
- Edge functions for API routes
- Zero-configuration deployment

### Docker
- Create Dockerfile for containerization
- docker-compose.yml with frontend + backend
- Nginx for production serving

### Environment Variables
- Development: `.env.local`
- Production: Set in hosting platform (Vercel, AWS, etc.)
- **Never commit**: `.env` files to version control

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| Setup | 30 min | Initialize project, install dependencies |
| API & Types | 30 min | API client, TypeScript types, validation |
| Hooks | 45 min | Custom React hooks for API integration |
| Components | 1.5 hrs | Core UI components |
| Pages | 45 min | Routes and page layouts |
| Providers | 30 min | Context providers and configuration |
| Polish | 45 min | UX improvements, animations, accessibility |
| Testing | 30 min | Manual testing and documentation |
| **Total** | **~5 hours** | Complete MVP implementation |

## Success Criteria

✅ User can upload video files via drag-and-drop
✅ Upload progress is visible with percentage
✅ Status updates automatically via polling
✅ Transcription displays when processing completes
✅ Copy to clipboard works reliably
✅ Download transcription as text file
✅ Responsive design works on mobile, tablet, desktop
✅ Error handling with user-friendly messages
✅ Loading states for all async operations
✅ Professional UI with shadcn/ui components

## Getting Started

After implementation, developers can start with:

```bash
cd frontend
npm install
npm run dev
```

Then visit `http://localhost:3000` to see the application.

Ensure backend is running on `http://localhost:8000` or update `NEXT_PUBLIC_API_URL` accordingly.
