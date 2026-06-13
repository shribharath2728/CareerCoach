# Requirements Document

## Introduction

SkillLens is an AI-powered career coaching platform with a React + Vite frontend and a FastAPI backend. The current UI uses a functional but visually dated design with a teal/slate color palette and standard chatbot aesthetics. This feature covers a complete UI redesign to elevate the product into a premium, futuristic AI career platform — visually consistent with products like Perplexity, Linear, and Notion.

The redesign targets the existing React + Vite project (not a migration to Next.js). All existing routing, state management via `AppContext`, API integrations, and page/component structure are preserved. Only the visual design system, layout, component styling, and UI presentation layer are changed.

The new design language is: **dark-mode-first, glassmorphic, minimalist, and premium** — using indigo/violet as the primary brand palette, subtle animated backgrounds, elegant micro-interactions, and a structured three-region dashboard layout.

---

## Glossary

- **Design_System**: The collection of CSS custom properties, utility classes, and component styles defined in `index.css` and shared across all pages.
- **Sidebar**: The fixed left navigation panel in the app shell.
- **Topbar**: The fixed top navigation bar visible on all authenticated pages.
- **App_Shell**: The outer layout comprising the Sidebar, Topbar, and main content area.
- **Dashboard**: The main landing page after login, showing stats, quick actions, and career insights.
- **Chat_Interface**: The AI conversation page (`Chat.jsx`) where users interact with the career coach.
- **Career_Roadmap**: A visual, interactive representation of a user's career progression path.
- **Analytics_Page**: The page displaying skill scores, interview readiness, progress charts, and streak data.
- **Onboarding_Flow**: The pre-login/registration screens presented when no user session exists.
- **Landing_Page**: A public-facing hero screen shown before authentication, within the Onboarding flow.
- **Glassmorphism**: A UI style using semi-transparent backgrounds, backdrop blur, and subtle borders to simulate frosted glass.
- **Micro_Interaction**: A small animation or transition triggered by user action (hover, click, focus) that provides feedback.
- **Token**: A CSS custom property (variable) representing a design decision such as a color, spacing value, or radius.
- **Card**: A surface element with background, border, and shadow used to group related content.
- **Progress_Indicator**: A visual element (ring, bar, or chart segment) that communicates completion percentage.
- **Career_Score**: A composite numeric score (0–100) reflecting overall career readiness across multiple dimensions.
- **Streak**: A count of consecutive days the user has engaged with the platform.

---

## Requirements

### Requirement 1: Design System Token Update

**User Story:** As a developer, I want a unified CSS design token system, so that all components reference a single source of truth for colors, spacing, and visual properties that reflect the new premium dark-mode aesthetic.

#### Acceptance Criteria

1. THE Design_System SHALL define the following dark-mode base tokens as CSS custom properties on `:root`: `--bg-primary: #0B0F19`, `--surface: #111827`, `--primary: #6366F1`, `--accent: #8B5CF6`, `--success: #10B981`, `--text-primary: #F9FAFB`, `--text-secondary: #9CA3AF`.
2. THE Design_System SHALL define a light-mode override token set on `[data-theme="light"]` that explicitly reassigns all seven tokens from Criterion 1 to semantically equivalent light-mode values: `--bg-primary: #F9FAFB`, `--surface: #FFFFFF`, `--primary: #4F46E5`, `--accent: #7C3AED`, `--success: #059669`, `--text-primary: #111827`, `--text-secondary: #6B7280`.
3. WHEN the user toggles between dark and light mode, THE Design_System SHALL apply the corresponding token set by toggling the `data-theme` attribute on the `<html>` element; the visual transition SHALL complete within 300ms without a full page reload.
4. THE Design_System SHALL define border-radius tokens: `--radius-sm: 10px`, `--radius: 16px`, `--radius-lg: 24px`, `--radius-xl: 32px`.
5. THE Design_System SHALL define shadow tokens using `rgba(0,0,0,N)` values: `--shadow-sm: 0 1px 3px rgba(0,0,0,0.12)`, `--shadow-md: 0 8px 24px rgba(0,0,0,0.20)`, `--shadow-lg: 0 20px 50px rgba(0,0,0,0.30)`.
6. THE Design_System SHALL define a `--accent-glow` token as `rgba(99, 102, 241, 0.3)` for use in focus rings, hover glows, and button shadows.
7. THE Design_System SHALL expose a `--glass-bg` token as `rgba(17, 24, 39, 0.7)` and a `--glass-border` token as `rgba(255, 255, 255, 0.08)` for glassmorphic surfaces.
8. THE Design_System SHALL define transition tokens: `--transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1)` and `--transition-slow: 0.45s cubic-bezier(0.4, 0, 0.2, 1)`.

---

### Requirement 2: App Shell Layout Redesign

**User Story:** As a user, I want a polished three-region layout with a sleek sidebar, minimal topbar, and spacious main content area, so that navigating the app feels like using a world-class SaaS product.

#### Acceptance Criteria

1. THE App_Shell SHALL render a fixed left Sidebar of width 260px on viewports ≥ 768px, a fixed Topbar of height 64px, and a scrollable main content area that fills the remaining space.
2. THE Sidebar SHALL use `var(--glass-bg)` background with `backdrop-filter: blur(20px)` and a right border using `var(--glass-border)`.
3. THE Sidebar SHALL display the SkillLens logo mark, the brand name "SkillLens" in Outfit font weight 800, and the subtitle "Career Coach AI" below it.
4. WHEN a nav item is active, THE Sidebar SHALL highlight it with a left accent border of 2px using `var(--primary)`, a background of `rgba(99,102,241,0.12)`, and text color `var(--primary)`.
5. WHEN a nav item is hovered, THE Sidebar SHALL transition its background to `rgba(255,255,255,0.05)` and text color to `var(--text-primary)` within 0.3s.
6. THE Topbar SHALL use `var(--glass-bg)` background with `backdrop-filter: blur(12px)` and a bottom border using `var(--glass-border)`.
7. THE Topbar SHALL display the current page title on the left and a user avatar chip on the right showing the user's initials (first letter of first name + first letter of last name; first letter only if single name) and full name.
8. THE App_Shell SHALL render an animated background layer consisting of two radial gradient blobs using `var(--primary)` and `var(--accent)` at opacity ≤ 0.06, fixed position, non-interactive (`pointer-events: none`), drifting continuously on a 20s loop.
9. WHEN the viewport width is less than 768px, THE App_Shell SHALL hide the Sidebar by default and show a hamburger toggle button in the Topbar to reveal it as a slide-over overlay.
10. THE App_Shell SHALL keep the hamburger toggle button visible on all viewport sizes including desktop, allowing the Sidebar to be manually collapsed on any screen size.

---

### Requirement 3: Landing Page / Onboarding Hero

**User Story:** As a new visitor, I want to see a compelling hero section before signing in, so that I understand the product's value proposition and feel confident it is a premium AI tool.

#### Acceptance Criteria

1. THE Landing_Page SHALL render a full-viewport hero section with the headline "Your Personal AI Career Coach" in Outfit font at font-size ≥ 48px and font-weight 800.
2. THE Landing_Page SHALL render the subheading "Get personalized career guidance, skill roadmaps, resume analysis, interview preparation, and industry insights powered by AI." in `var(--text-secondary)` color, below the headline.
3. THE Landing_Page SHALL display a row of six non-navigating pill elements labeled: Career Path Planning, Resume Analyzer, Interview Coach, Skill Gap Analysis, Job Readiness Score, Industry Trends — clicking a pill SHALL produce no navigation or state change.
4. WHEN the Landing_Page is rendered, THE Landing_Page SHALL display an animated background of floating orbs or particles maintaining a frame rate ≥ 30fps on a modern device.
5. THE Landing_Page SHALL display a primary call-to-action button labeled "Get Started" and a secondary button labeled "Sign In".
6. WHEN the "Get Started" button is clicked, THE Landing_Page SHALL navigate to the account registration step of the Onboarding_Flow. WHILE neither button has been clicked, THE Landing_Page SHALL display no navigation or modal and require explicit user action.
7. WHEN the "Sign In" button is clicked, THE Landing_Page SHALL navigate to the login step of the Onboarding_Flow.
8. THE Landing_Page SHALL render a radial gradient glow element behind the headline using `var(--primary)` and `var(--accent)` at opacity ≤ 0.4.

---

### Requirement 4: Premium Dashboard Redesign

**User Story:** As a logged-in user, I want a visually rich dashboard with career stats, quick actions, and AI insights presented in a modern card-based grid, so that I immediately see my progress and know what to do next.

#### Acceptance Criteria

1. IF the user is authenticated, THEN THE Dashboard SHALL render a welcome banner with a radial gradient background from `var(--accent)` to `var(--accent-dark)`, displaying the user's first name, the AI coach name, and a prominent call-to-action button.
2. THE Dashboard SHALL render a stats row of five metric cards — Interviews Done, Average Score, Best Score, Questions Answered, and Day Streak — each with an icon, numeric value, and label.
3. WHEN a stat card is hovered, THE Dashboard SHALL animate it upward by 4px and apply `var(--shadow-md)` box shadow within `var(--transition)`.
4. THE Dashboard SHALL render a "Quick Actions" grid of six action cards: Start Mock Interview, Chat with AI Coach, Voice Practice Mode, View Analytics, Review History, and Connect Telegram.
5. WHEN a quick action card is hovered, THE Dashboard SHALL apply a scale transform of 1.02 and transition the border color to `var(--primary)` within `var(--transition)`.
6. IF the Pro Tips array from the analytics API is empty or absent, THEN THE Dashboard SHALL hide the entire Career Insights card.
7. THE Dashboard SHALL display a Career_Score ring indicator as a circular SVG progress ring filled with a gradient from `var(--accent)` to `var(--accent-dark)`, showing the user's `average_score` as a percentage.
8. WHEN analytics data is loading, THE Dashboard SHALL render skeleton placeholder elements with a shimmer animation in place of stat values.

---

### Requirement 5: Futuristic Chat Interface

**User Story:** As a user, I want the AI chat experience to feel like ChatGPT or Perplexity, with clean message bubbles, streaming-ready design, markdown rendering, and elegant input controls, so that conversations with my career coach feel premium and professional.

#### Acceptance Criteria

1. THE Chat_Interface SHALL render user messages in right-aligned bubbles with background `var(--accent)` and white text, and AI messages in left-aligned bubbles with background `var(--surface)` and a 2px left border using `var(--primary)`.
2. THE Chat_Interface SHALL render AI message content using a Markdown renderer that supports bold, italic, ordered and unordered lists, inline code (monospace background), fenced code blocks (distinct background with `var(--font-mono)` font), and paragraph spacing of ≥ 0.5em.
3. WHEN an AI response is being generated, THE Chat_Interface SHALL display an animated three-dot typing indicator within an AI bubble, with each dot cycling opacity 1→0.3→1 at 0.6s intervals staggered by 0.2s.
4. THE Chat_Interface SHALL render the message input as a full-width rounded textarea with a minimum height of 48px, a border that transitions from `var(--glass-border)` to `var(--primary)` on focus within `var(--transition)`, and a send button with `var(--primary)` background.
5. WHEN speech recognition is available in the browser, THE Chat_Interface SHALL render a voice input button (microphone icon) to the left of the textarea that toggles speech recognition on click.
6. WHILE voice recording is in the active capture state (permission granted and audio stream open), THE Chat_Interface SHALL animate the microphone button with a pulsing ring that expands to 2× the button diameter and fades to opacity 0 at 1.2s intervals using `var(--primary)` color. WHEN recording is initializing or awaiting permission, THE Chat_Interface SHALL not show the pulse animation.
7. THE Chat_Interface SHALL render a collapsible left panel listing chat session history; WHEN the panel collapse toggle is clicked, THE Chat_Interface SHALL slide the panel in or out within `var(--transition-slow)`.
8. WHEN a new session is selected or created, THE Chat_Interface SHALL load and display the corresponding messages without a full page reload.
9. THE Chat_Interface SHALL render an AI model/coach identity header at the top of the chat area, showing the AI name, an avatar, and a status indicator that reads "Online" when the API is reachable and "Connecting…" otherwise.
10. WHEN the message list overflows the container, THE Chat_Interface SHALL automatically scroll to the latest message using smooth scroll behavior (`scroll-behavior: smooth`).

---

### Requirement 6: Career Roadmap Visualization

**User Story:** As a user, I want to see an interactive visual roadmap of my career trajectory, so that I can understand the skills and milestones needed to reach my target role.

#### Acceptance Criteria

1. THE Career_Roadmap SHALL render a horizontal node-and-connector diagram by default (vertical on viewports < 480px) showing at least one example path: "Software Engineer → Frontend Developer → React Developer → Full Stack Developer → Senior Engineer".
2. THE Career_Roadmap SHALL color-code each node by status: completed nodes use `var(--success)`, the current node uses `var(--primary)` with `box-shadow: 0 0 0 6px var(--accent-glow)`, and future nodes use a border in `var(--text-secondary)` with muted fill.
3. WHEN a roadmap node is clicked, THE Career_Roadmap SHALL display a popover or side panel listing 3–8 required skills for that role, an estimated time in weeks, and 1–3 suggested learning resources.
4. THE Career_Roadmap SHALL render connectors between nodes as solid lines for completed steps and animated dashed lines (dash-offset animation over 2s) for future steps.
5. WHEN the roadmap data is loading, THE Career_Roadmap SHALL display a skeleton layout of node and connector placeholders.
6. WHEN the roadmap data fails to load, THE Career_Roadmap SHALL display an error message and a retry button.
7. WHILE the viewport is below 768px, THE Career_Roadmap SHALL be navigable by horizontal touch scroll without requiring zoom.

---

### Requirement 7: Analytics Page with Charts and Progress Indicators

**User Story:** As a user, I want visually compelling analytics showing my skill progress, interview scores, and learning streak, so that I feel motivated and can identify areas for improvement.

#### Acceptance Criteria

1. THE Analytics_Page SHALL render a Skill Completion section as a set of labeled horizontal progress bars, one per tracked skill dimension returned by the analytics API, each bar filled with `var(--primary)` proportional to the completion percentage.
2. THE Analytics_Page SHALL render a Resume Score indicator as a circular SVG progress ring labeled with the numeric score out of 100; the ring stroke color SHALL be red (`#EF4444`) for scores ≤ 40, orange (`#F59E0B`) for 41–70, and `var(--success)` for ≥ 71.
3. THE Analytics_Page SHALL render an Interview Readiness Score card showing the latest `average_score` as a percentage and an upward arrow if the current session score exceeds the previous session score, or a downward arrow if it is lower.
4. THE Analytics_Page SHALL render a Weekly Learning Streak heatmap showing the last 30 days of activity, with active days highlighted in `var(--accent)` and inactive days in `var(--surface)`.
5. THE Analytics_Page SHALL render a Career Growth Score chart (bar or line) showing `average_score` history over the user's last 10 sessions ordered chronologically.
6. WHEN any chart data is loading, THE Analytics_Page SHALL render an animated shimmer skeleton in place of each chart.
7. WHEN a bar, line data point, or heatmap cell is hovered, THE Analytics_Page SHALL display a tooltip showing the precise numeric value; for time-series charts the tooltip SHALL also show the session date.

---

### Requirement 8: Glassmorphic Card Component System

**User Story:** As a developer, I want a reusable glassmorphic card component system, so that all pages in the app can use consistent surface elements that reflect the premium design language without duplicating styles.

#### Acceptance Criteria

1. THE Design_System SHALL define a `.glass-card` CSS class that applies `background: var(--glass-bg)`, `backdrop-filter: blur(16px)`, `border: 1px solid var(--glass-border)`, and `border-radius: var(--radius)`.
2. THE Design_System SHALL define a `.glass-card-hover` modifier class that transitions the border color to `rgba(99,102,241,0.4)` and box shadow to `0 8px 32px rgba(99,102,241,0.12)` on hover within `var(--transition)`.
3. THE Design_System SHALL define a `.stat-card` class that extends `.glass-card` using `display: flex`, `align-items: center`, and `gap: 12px`, with child elements ordered as icon container, then a value+label stack.
4. THE Design_System SHALL define a `.feature-card` class that extends `.glass-card` with a `padding: 24px` container for icon, title, and description text; WHEN `.feature-card` is hovered, its top border SHALL transition to a 2px gradient from `var(--primary)` to `var(--accent)` within `var(--transition)`.
5. WHEN `.glass-card` is rendered on a `var(--bg-primary)` dark background, THE Design_System SHALL ensure a contrast ratio ≥ 4.5:1 between `var(--text-primary)` text and the `var(--glass-bg)` card background for font sizes ≥ 12px.

---

### Requirement 9: Micro-Interactions and Animation System

**User Story:** As a user, I want smooth, purposeful animations throughout the app, so that the UI feels alive and premium rather than static.

#### Acceptance Criteria

1. WHEN a page is navigated to, THE App_Shell SHALL animate the new page in with opacity 0→1 and translateY 16px→0 over 350ms using Framer Motion `AnimatePresence`.
2. WHEN a card section enters the viewport during initial render, THE Dashboard SHALL stagger-animate up to 10 cards in sequence with opacity 0→1 and translateY 16px→0, applying a 60ms delay between each card using Framer Motion `variants`.
3. WHEN a button with class `.btn-primary` is hovered, THE Design_System SHALL apply `translateY(-2px)` and increase the button's `box-shadow` blur radius by at least 8px within 200ms.
4. WHEN a button with class `.btn-primary` is in the active (pressed) state, THE Design_System SHALL apply `scale(0.97)` and remove the box-shadow entirely within 100ms.
5. WHILE the app is rendered, THE App_Shell SHALL display a floating orb element that drifts continuously within a displacement bound of ≤ 40px from its origin, completing one full drift cycle every 8–12 seconds at opacity ≤ 0.08.
6. WHEN a nav item in the Sidebar is hovered, THE Sidebar SHALL transition its background opacity from 0 to ≤ 0.05 (white fill) over 200ms.
7. WHILE the voice recording button is in the active capture state, THE Chat_Interface SHALL display a `pulse-ring` element that expands from the button diameter to 2× the button diameter and fades from opacity 1 to opacity 0, repeating at 1.2-second intervals.

---

### Requirement 10: Typography and Font System

**User Story:** As a user, I want consistent, readable typography across the entire app, so that the interface feels cohesive and professional.

#### Acceptance Criteria

1. THE Design_System SHALL load Google Fonts: Outfit at weights 400, 600, 700, 800 for headings and brand elements; Inter at weights 400, 500, 600 for body text; and JetBrains Mono at weight 400 for code.
2. THE Design_System SHALL set `font-family: 'Inter', system-ui, sans-serif` as the base body font applied to the `<body>` element, and `font-family: 'Outfit', 'Inter', sans-serif` as the heading font applied to `h1`–`h4` elements.
3. THE Design_System SHALL define a type scale with the following explicit triplets (font-size / font-weight / line-height): display 2.5rem/800/1.1, h1 2rem/700/1.2, h2 1.5rem/700/1.3, h3 1.1rem/600/1.4, body 0.9rem/400/1.6, small 0.8rem/400/1.5, label 0.75rem/600/1.4.
4. THE Design_System SHALL define `--font-mono: 'JetBrains Mono', ui-monospace, monospace` and apply it via `font-family: var(--font-mono)` to all `<pre>`, `<code>`, and `<kbd>` elements.
5. WHEN text is rendered in dark mode (`data-theme="dark"`), THE Design_System SHALL apply `color: var(--text-primary)` (`#F9FAFB`) for `<p>`, `<span>`, `<li>`, and heading elements; `color: var(--text-secondary)` (`#9CA3AF`) for supporting/meta text; and `color: #6B7280` for placeholder and muted text.
6. WHEN text is rendered in light mode (`data-theme="light"`), THE Design_System SHALL apply `color: #111827` for primary content, `color: #6B7280` for supporting text, and `color: #9CA3AF` for placeholder text.

---

### Requirement 11: Responsive and Mobile-First Layout

**User Story:** As a user on a mobile device, I want the app to be fully usable with a touch-friendly layout, so that I can manage my career coaching sessions from any device.

#### Acceptance Criteria

1. THE App_Shell SHALL use `@media` breakpoints at 768px (tablet) and 480px (mobile) so that no content overflows its container and all content remains accessible without horizontal scrolling on viewports ≥ 320px wide.
2. WHEN the viewport width transitions below 768px, THE App_Shell SHALL collapse the Sidebar off-screen; WHEN the hamburger button in the Topbar is clicked, THE App_Shell SHALL slide the Sidebar in as a full-height overlay; WHEN the overlay backdrop is clicked or the Escape key is pressed, THE App_Shell SHALL slide the Sidebar back off-screen and return keyboard focus to the hamburger button.
3. WHEN the viewport width is below 768px, THE Dashboard stats grid SHALL collapse from 5 columns to 2 columns.
4. IF the viewport width is exactly 768px, THEN THE Dashboard stats grid SHALL maintain the 5-column layout.
5. WHEN the viewport width is below 480px, THE Dashboard stats grid SHALL collapse to a single column.
6. THE Chat_Interface SHALL render a fixed-position input area pinned to the bottom of the screen and a scrollable message history above it on viewports ≥ 320px wide.
7. WHILE the viewport width is below 768px, THE Career_Roadmap SHALL render within a horizontally scrollable container, allowing touch-swipe navigation without requiring zoom.
8. WHEN any interactive element (button, link, input, nav item) is rendered, THE Design_System SHALL ensure its clickable/tappable area is at least 44×44px and that adjacent touch targets are separated by at least 8px of non-interactive space.

---

### Requirement 12: Accessibility Compliance

**User Story:** As a user relying on assistive technologies, I want the app to follow WCAG 2.1 AA accessibility standards, so that I can use the career coaching features without barriers.

#### Acceptance Criteria

1. WHEN a focusable element receives keyboard focus, THE Design_System SHALL display a visible focus indicator of at least 3px solid or equivalent, with a contrast ratio of at least 3:1 between the indicator color and adjacent colors.
2. THE Design_System SHALL maintain a minimum color contrast ratio of 4.5:1 for normal text (< 18pt regular or < 14pt bold) and 3:1 for large text (≥ 18pt regular or ≥ 14pt bold) and interactive components against their respective backgrounds, per WCAG 2.1 SC 1.4.3.
3. THE Sidebar navigation SHALL support Tab (forward focus), Shift+Tab (reverse focus), and Enter (activate) keyboard interactions, with each nav item's `aria-label` being non-empty and uniquely identifying the destination page in plain language.
4. WHEN a modal or overlay is open, THE App_Shell SHALL trap keyboard focus within the overlay, cycling from the last focusable element back to the first on Tab, and from the first to the last on Shift+Tab; WHEN the overlay is closed, THE App_Shell SHALL return focus to the element that triggered the overlay.
5. ALL icon-only buttons SHALL have an `aria-label` attribute that is non-empty, describes the button's action in plain language, and does not reference visual appearance (e.g., "Send message", "Start voice recording", "Stop recording").
6. WHEN a new AI message is appended to the message list, THE Chat_Interface SHALL announce it via an `aria-live="polite"` `aria-atomic="false"` region so screen readers read only the new message text.
7. ALL interactive elements in the application SHALL appear in the DOM in the same order as their visual reading sequence, so that keyboard focus order matches the visual layout.

---

### Requirement 13: Tailwind CSS Integration

**User Story:** As a developer, I want Tailwind CSS available as a utility layer alongside the existing custom CSS design system, so that I can build new components rapidly using utility classes without removing the existing CSS architecture.

#### Acceptance Criteria

1. THE Design_System SHALL install Tailwind CSS v3 as a dev dependency and configure it to scan `./src/**/*.{js,jsx}` for class names.
2. THE Design_System SHALL extend the Tailwind theme to expose token keys (`primary`, `accent`, `success`, `bg-primary`, `surface`, `text-primary`, `text-secondary`) whose values match the corresponding CSS custom properties already defined in `index.css`, so a developer can use both `var(--primary)` and `text-primary` Tailwind classes interchangeably.
3. THE Design_System SHALL add Tailwind's `@tailwind base`, `@tailwind components`, and `@tailwind utilities` directives to `index.css` without removing existing CSS custom property definitions.
4. IF a Tailwind utility class has the same name as an existing custom CSS class, THEN the existing custom CSS class styles SHALL remain visually unchanged after Tailwind is added.
5. THE Design_System SHALL configure Tailwind so that the `dark:` variant activates when `data-theme="dark"` is present on the `<html>` element.

---

### Requirement 14: Component Shimmer / Skeleton Loading States

**User Story:** As a user, I want to see skeleton loading states instead of blank areas while data loads, so that the app feels fast and polished even when API responses are slow.

#### Acceptance Criteria

1. THE Design_System SHALL define a `.skeleton` CSS class that applies a shimmer animation moving a highlight band from left to right over 1.5s using the project's existing `--surface` and `--bg-primary` CSS variables as the base and highlight colors.
2. WHEN the Dashboard analytics data is fetching, THE Dashboard SHALL render `.skeleton` placeholder elements with the same width and height as each stat card's value area, replacing the numeric values.
3. WHEN the Chat_Interface session list is loading, THE Chat_Interface SHALL render three `.skeleton` placeholder items with widths of approximately 80%, 60%, and 40% of the panel width, in that order.
4. WHEN the Analytics_Page charts are loading, THE Analytics_Page SHALL render `.skeleton` rectangles matching the layout dimensions of the Skill Completion bars, the Resume Score ring, the Career Growth chart, and the Streak heatmap.
5. WHEN data has successfully loaded, the component displaying the data SHALL fade in the real content with opacity 0→1 over 200ms and remove the skeleton element only after the fade transition completes.
6. WHEN a data fetch fails, THE component SHALL remove the skeleton element and display an inline error message with a retry action, preventing the skeleton from persisting indefinitely.

