import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'
import { AuthProvider } from '@/lib/auth-context'
import { Toaster } from '@/components/ui/toaster'
import { SidebarWrapper } from '@/components/sidebar-wrapper'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Notetaker - Video Transcription Notes',
  description: 'Organize and manage your video transcription notes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <QueryProvider>
            <div className="flex min-h-screen">
              <SidebarWrapper />
              <main className="flex-1 w-full">
                {children}
              </main>
            </div>
            <Toaster />
          </QueryProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
