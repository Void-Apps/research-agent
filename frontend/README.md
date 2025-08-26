# AI Research Agent Frontend

This is the frontend application for the AI Research Agent, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- Modern React application with Next.js 15
- TypeScript for type safety
- Tailwind CSS for styling
- React Query for state management and API caching
- Axios for API communication
- Error boundaries for graceful error handling
- Responsive design for mobile and desktop

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── history/           # Research history page
│   ├── results/[id]/      # Dynamic results page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── layout/           # Layout components
│   └── ui/               # UI components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and API clients
└── providers/            # React context providers
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env.local
   ```

3. Update the API URL in `.env.local` if needed:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the FastAPI backend through:

- **Research API**: Submit queries and retrieve results
- **React Query**: Automatic caching and background updates
- **Error Handling**: Graceful degradation when APIs are unavailable

## Next Steps

This is the basic project structure. The following components will be implemented in subsequent tasks:

- Research form component (Task 13)
- Results display components (Task 14)
- Complete page implementations (Task 15)
- Error handling and UX improvements (Task 16)
- Full API integration (Task 17)