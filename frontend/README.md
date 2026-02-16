# Handball Manager Frontend

A React + TypeScript frontend for the Handball Club Management System.

## Features

- Responsive design (mobile-first)
- JWT authentication
- Role-based UI
- Real-time updates via WebSocket
- Calendar view
- Team & player management
- Game & event scheduling
- Attendance tracking
- News system

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router
- **Build Tool**: Vite
- **Icons**: Lucide React

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
src/
├── components/      # React components
│   ├── layout/      # Layout components
│   └── ui/          # UI components
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── services/        # API services
├── store/           # State management (Zustand)
├── styles/          # Global styles
├── types/           # TypeScript types
└── utils/           # Utility functions
```

## Environment Variables

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```
