# AI Enhancements & Navigation Implementation Plan

## 🎯 Overview
Add sentiment timeline analysis, theme detection, actionable insights, sticky TOC, and collapsible sections to the video detail page.

## 📦 Implementation Phases

### **Phase 1: Backend - AI Analysis Enhancement**

**1.1 Extend Note Generation Schema**
- Add sentiment analysis to `GeneratedNote` schema ([backend/app/schemas.py:100](backend/app/schemas.py#L100))
  - `sentiment_timeline`: Array of `{timestamp_seconds, sentiment, intensity, description}`
  - `themes`: Array of `{theme, frequency, key_moments}`
  - `actionable_insights`: Array of strings for clinical/professional recommendations
- Update `NotesData` model with new fields

**1.2 Update Note Generation Service**
- Enhance LLM prompt in [backend/app/services/note_generation_service.py:36](backend/app/services/note_generation_service.py#L36)
  - Add sentiment analysis instructions: "Analyze emotional tone throughout transcript, marking intensity shifts"
  - Add theme extraction: "Identify recurring themes (perfectionism, attachment, etc.) with frequency counts"
  - Add actionable insights: "Generate 3-5 clinical/professional recommendations for follow-up"
- Update return type to include new fields

**1.3 Database Migration**
- The `notes` JSONB column ([backend/app/models.py:86](backend/app/models.py#L86)) already supports arbitrary structure
- No migration needed - schema change is forward/backward compatible

### **Phase 2: Frontend - Type Definitions**

**2.1 Update TypeScript Types**
- Extend `GeneratedNote` in [frontend/lib/types.ts:33](frontend/lib/types.ts#L33)
  - Add `sentiment_timeline?: Array<{timestamp_seconds: number, sentiment: string, intensity: number, description: string}>`
  - Add `themes?: Array<{theme: string, frequency: number, key_moments?: string[]}>`
  - Add `actionable_insights?: string[]`

### **Phase 3: Frontend - UI Components**

**3.1 Create New Components**

**Sentiment Timeline Component** (`frontend/components/sentiment-timeline.tsx`)
- Emotion graph visualization using SVG/canvas
- X-axis: video timeline (minutes:seconds)
- Y-axis: emotional intensity (-100 to +100)
- Color-coded sentiment: positive (green), negative (red), neutral (gray)
- Hoverable points showing description

**Themes Component** (`frontend/components/themes-visualization.tsx`)
- Tag cloud with frequency-based sizing
- Pills layout with color coding
- Click to filter/highlight related sections (future enhancement)

**Actionable Insights Component** (`frontend/components/actionable-insights.tsx`)
- Dedicated card section with distinct styling
- Icon-based recommendations (💡 for insights)
- Clear formatting for clinical/professional context

**3.2 Navigation Enhancements**

**Sticky Table of Contents** (`frontend/components/sticky-toc.tsx`)
- Fixed position sidebar on desktop (hidden on mobile)
- Auto-highlight current section on scroll
- Smooth scroll to section on click
- Sections: Summary, Key Points, Detailed Notes, Takeaways, Quotes, Questions, Themes, Sentiment, Insights

**Collapsible Section Wrapper** (`frontend/components/collapsible-section.tsx`)
- Reusable component wrapping each notes section
- Chevron icon toggle
- Smooth expand/collapse animation
- Remember expanded state in localStorage

### **Phase 4: Frontend - Integration**

**4.1 Update Video Detail Page**
- Modify [frontend/app/videos/[id]/page.tsx:365](frontend/app/videos/[id]/page.tsx#L365) (Notes tab)
- Add two-column layout on desktop:
  - Left: Sticky TOC (20% width)
  - Right: Content sections (80% width)
- Wrap each section in `CollapsibleSection`
- Add new sections after existing ones:
  - Sentiment Timeline (if `sentiment_timeline` exists)
  - Themes & Patterns (if `themes` exists)
  - Actionable Insights (if `actionable_insights` exists)

**4.2 Responsive Design**
- Mobile: Hide TOC, stack sections vertically
- Tablet: Collapsible TOC drawer
- Desktop: Fixed sidebar TOC

### **Phase 5: Styling & Polish**

**5.1 Component Styling**
- Sentiment chart: Tailwind + recharts library for visualization
- Themes: Tag cloud with `transform: scale()` based on frequency
- Insights: Distinct background color (blue-50), icon prefixes
- TOC: Subtle shadow, sticky positioning, active state highlight

**5.2 Accessibility**
- ARIA labels for expandable sections
- Keyboard navigation for TOC
- Screen reader announcements for sentiment data

## 🛠️ Technical Decisions

**Sentiment Analysis**: LLM-based extraction from transcript context (no external APIs)
**Visualization Library**: recharts (already compatible with Next.js/React)
**State Management**: React hooks (useState for collapse state)
**Persistence**: localStorage for section expand/collapse preferences

## 📊 Expected Impact

- **Better navigation**: Sticky TOC reduces scroll time for 9k+ word documents
- **Deeper insights**: Sentiment timeline reveals emotional patterns in therapy/counseling videos
- **Actionable value**: Clinical recommendations improve session follow-up
- **Cognitive load**: Collapsible sections let users focus on relevant content

## 🔄 Phase Execution Order

1. Backend schema + service (independent)
2. Frontend types (depends on #1)
3. UI components (independent, can parallelize)
4. Integration (depends on #2, #3)
5. Polish (depends on #4)

## 📝 Implementation Notes

### Sentiment Timeline Data Structure
```typescript
{
  timestamp_seconds: number,    // Position in video (e.g., 120 for 2:00)
  sentiment: 'positive' | 'negative' | 'neutral',
  intensity: number,            // -100 to +100
  description: string           // "Initial activation discussing past trauma"
}
```

### Themes Data Structure
```typescript
{
  theme: string,               // "perfectionism", "attachment patterns"
  frequency: number,           // How many times mentioned/discussed
  key_moments?: string[]       // Optional: specific quotes or timestamps
}
```

### Actionable Insights Examples
- "Consider grounding exercise earlier next time due to initial activation"
- "Explore feelings around perfectionism further in next session"
- "Client showed readiness to discuss relational wounds - prioritize in follow-up"

## 🎨 UI Design Considerations

### Sentiment Timeline Chart
- Use area chart for visual impact
- Gradient fill from baseline (neutral) to intensity peaks
- Tooltip shows exact timestamp + description on hover
- Click point to jump to that moment in transcript (future enhancement)

### Themes Tag Cloud
- Font size: 12px-24px based on frequency
- Color palette: Blue spectrum for professional context
- Spacing: Flexbox with gap-2 for clean layout
- Max 10 themes displayed (top frequency)

### Sticky TOC Behavior
- Position: `sticky top-[73px]` (below TopNav)
- Max height: `calc(100vh - 100px)` with overflow-y-auto
- Active section: Bold + left border accent
- Smooth scroll: `scroll-behavior: smooth` on click

### Collapsible Sections
- Default state: All expanded on first visit
- Persist state: `localStorage.setItem('notes-section-${id}', 'collapsed')`
- Animation: `transition-all duration-200` for height changes
- Icon: ChevronDown/ChevronRight from lucide-react
