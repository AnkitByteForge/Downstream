# Reference Engineering System — Frontend

A Next.js (App Router, TypeScript) presentation layer for the Reference
Engineering System's backend. Modern-enterprise-construction-software look
(inspired by Procore/ACC/Trimble navigation and information-density patterns
— no branding or proprietary assets copied), built with Tailwind CSS and
shadcn/ui.

Every page is a **client component that calls the backend's own REST API**
(`src/lib/api-client/`) — nothing here bypasses the backend or fabricates
data client-side.

## Pages (RES-1)

| Route | Page |
|---|---|
| `/login` | Login |
| `/dashboard` | Dashboard |
| `/projects` | Project Explorer |
| `/projects/[projectId]/rfis` | RFI Register |
| `/projects/[projectId]/rfis/[rfiId]` | RFI Detail |

Drawing Register/Detail/Revision Timeline, Submittal Register, Specification
Browser, Location Hierarchy, and Activity Feed land in RES-2/RES-3/RES-4 per
the approved milestone plan, alongside the backend slices that back them.

## Running locally

```bash
npm install
cp .env.example .env.local   # point NEXT_PUBLIC_API_BASE_URL at the backend
npm run dev -- --port 3100
```

Requires the backend running (see `../backend/README.md`) and seeded, so
`/login` has a real account to authenticate against.

## Auth

Login posts to the backend's `/auth/login`, which sets an httpOnly session
cookie. Every subsequent API call is made with `credentials: "include"`; the
frontend never stores or reads the session token itself — it only asks the
backend's `/auth/session` endpoint whether it's still valid.
