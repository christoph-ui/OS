# 0711 Website

Customer-facing website and signup flow for 0711 Intelligence Platform.

## Features

- **Homepage** - "The End of Enterprise Software" - Main marketing page
- **Builders Page** - Satirical page targeting founders, CEOs, CTOs
- **Expert Network** - Expert marketplace and application flow
- **Signup Flow** - Multi-step customer registration with plan selection
- **API Integration** - Connected to Control Plane backend

## Getting Started

### Prerequisites

- Node.js 20+
- Running Control Plane API (port 8080)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local with your settings
nano .env.local

# Run development server
npm run dev
```

The website will be available at http://localhost:3000

### Pages

- `/` - Homepage (The End of Enterprise Software)
- `/builders` - Built For Builders, Not Bureaucrats
- `/experts` - Expert Network marketplace
- `/signup` - Customer signup form
- `/signup/plan` - Plan selection
- `/signup/payment` - Payment (coming soon)
- `/signup/complete` - Download installer (coming soon)

## Development

```bash
# Development mode with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Docker

Build and run with Docker:

```bash
# Build
docker build -t 0711-website .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api:8080 \
  -e NEXT_PUBLIC_STRIPE_KEY=pk_... \
  0711-website
```

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Control Plane API URL (default: http://localhost:8080)
- `NEXT_PUBLIC_STRIPE_KEY` - Stripe publishable key
- `NEXT_PUBLIC_WEBSITE_URL` - Website URL for redirects (default: http://localhost:3000)

## Project Structure

```
apps/website/
├── app/                    # Next.js app router
│   ├── page.tsx            # Homepage
│   ├── builders/           # Builders page
│   ├── experts/            # Expert network
│   ├── signup/             # Signup flow
│   │   ├── page.tsx        # Step 1: Registration
│   │   ├── plan/           # Step 2: Plan selection
│   │   ├── payment/        # Step 3: Payment
│   │   └── complete/       # Step 4: Complete
│   ├── layout.tsx          # Root layout
│   └── globals.css         # Global styles
├── components/             # Reusable components
│   ├── Navigation.tsx      # Site navigation
│   └── Footer.tsx          # Site footer
├── lib/                    # Utilities
│   └── api.ts              # API client
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── next.config.js
└── Dockerfile

```

## API Integration

The website connects to the Control Plane API for:

- Customer signup and authentication
- Plan/subscription creation
- License key generation
- Payment processing (Stripe)
- German invoice generation

See `lib/api.ts` for the complete API client.

## Design System

### Colors

- `--dark`: #141413
- `--light`: #faf9f5
- `--mid-gray`: #b0aea5
- `--orange`: #d97757 (primary)
- `--blue`: #6a9bcc
- `--green`: #788c5d

### Fonts

- **Headings**: Poppins (300, 400, 500, 600, 700)
- **Body**: Lora (400, 500, 600, italic)

### Brand Voice

- Direct, no-nonsense
- Provocative and opinionated
- For builders, not bureaucrats
- German market adapted

## License

Proprietary - © 2025 0711 Intelligence GmbH
