# RAG Pipeline Web App

Next.js frontend for the Production RAG Pipeline.

## Local Development

```bash
npm install
copy .env.local.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the FastAPI backend URL.

## Deployment

Deploy this folder as the Vercel project root.

Required Vercel environment variable:

```bash
NEXT_PUBLIC_API_URL=https://your-render-backend-url
```

## Validation

```bash
npm run lint
npm run build
```
