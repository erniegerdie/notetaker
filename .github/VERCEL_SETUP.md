# Vercel Deployment Setup

This repository is configured to automatically deploy the frontend to Vercel when changes are pushed to the `main` branch or when pull requests are opened.

## Required GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions → New repository secret):

### 1. VERCEL_TOKEN
Your Vercel authentication token.

**How to get it:**
1. Go to https://vercel.com/account/tokens
2. Click "Create Token"
3. Give it a descriptive name (e.g., "GitHub Actions - notetaker")
4. Copy the token and add it as `VERCEL_TOKEN` in GitHub secrets

### 2. VERCEL_ORG_ID
Your Vercel organization/team ID.

**How to get it:**
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel link` in the `frontend/` directory
3. Follow the prompts to link your project
4. Run `cat frontend/.vercel/project.json`
5. Copy the `orgId` value and add it as `VERCEL_ORG_ID` in GitHub secrets

### 3. VERCEL_PROJECT_ID
Your Vercel project ID.

**How to get it:**
1. After running `vercel link` (see above)
2. Run `cat frontend/.vercel/project.json`
3. Copy the `projectId` value and add it as `VERCEL_PROJECT_ID` in GitHub secrets

## Workflow Behavior

### On Push to `main` (Production Deployment)
- Triggers when changes are pushed to the `main` branch
- Only runs if files in `frontend/` directory changed
- Deploys to production URL (e.g., `your-project.vercel.app`)

### On Pull Request (Preview Deployment)
- Triggers when PRs targeting `main` are opened/updated
- Only runs if files in `frontend/` directory changed
- Deploys to a unique preview URL
- Preview URL is posted as a comment on the PR

## Manual Deployment

If you need to deploy manually:

```bash
cd frontend
vercel --prod  # Deploy to production
vercel         # Deploy to preview
```

## Environment Variables

Make sure to configure your environment variables in Vercel dashboard:
- Go to your project → Settings → Environment Variables
- Add `NEXT_PUBLIC_API_URL` with your backend API URL

## Vercel Project Setup

If you haven't created a Vercel project yet:

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set the **Root Directory** to `frontend`
4. Framework Preset: Next.js
5. Build Command: `npm run build` (default)
6. Output Directory: `.next` (default)
7. Install Command: `npm install` (default)
8. Add environment variables
9. Deploy

## Troubleshooting

### Build fails with "Missing required secrets"
- Ensure all three secrets (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID) are set in GitHub repository settings

### Deployment doesn't trigger
- Check that your changes modified files in the `frontend/` directory
- Verify the workflow file is on the `main` branch

### "Project not found" error
- Verify VERCEL_PROJECT_ID matches your Vercel project
- Ensure VERCEL_ORG_ID is correct
- Re-run `vercel link` in the frontend directory

### Build succeeds but site shows old version
- Check if the deployment actually went to production (not preview)
- Clear your browser cache
- Check Vercel dashboard for deployment status
