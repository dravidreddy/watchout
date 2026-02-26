# Secret Rotation Runbook (Zero-Downtime)

This document outlines the standard operating procedure for rotating critical infrastructure secrets in the Watchout production environment without incurring downtime. This is made possible via Render's Blue-Green deployment architecture (configured in `render.yaml`).

## Philosophy
Secrets should be rotated:
1. Every 90 days as standard security hygiene.
2. Immediately upon suspected employee offboarding or credential compromise.

## Process Overview

Because Watchout uses Blue-Green deployments on Render, we can rotate secrets by deploying a parallel infrastructure ("Green") with the new secrets, ensuring it passes all health checks, and then routing traffic over to it.

### Step 1: Provision the New Secret
1. Go to the third-party provider (e.g., Groq, MongoDB Atlas, Firebase) and generate a **new** API key or connection string.
2. **DO NOT** delete the old key yet. The existing "Blue" production instances are still actively using it.

### Step 2: Update the Render Environment
1. Log into the Render Dashboard.
2. Navigate to the `watchout-backend` Web Service -> Environment.
3. Update the specific environment variable (e.g., `GROQ_API_KEY`) with the new secret value.
4. Save the changes. Render will automatically trigger a new deployment ("Green").

### Step 3: Monitor the Blue-Green Deployment
1. Render will spin up the "Green" instances with the new environment variables and run `pytest tests/ -v` (as defined in `preDeployCommand`).
2. If tests fail (e.g., the new API key is invalid), the deploy aborts. Traffic remains on the "Blue" instances. **Zero downtime.**
3. If tests pass, Render runs the `/health` endpoint on the Green instances to verify database and external API connectivity with the new secrets.
4. Once health checks pass, Render seamlessly switches the load balancer to route new traffic to the Green instances. Existing requests on Blue are allowed to drain gracefully.

### Step 4: Verify and Revoke
1. Monitor the Grafana dashboards for 15 minutes to ensure error rates are stable (`< 1%`) and latency is normal.
2. Verify in the third-party provider's dashboard that the new key is being actively used and the old key's usage has ceased.
3. **Delete/Revoke** the old key from the third-party provider's dashboard.

## Specific Services

- **Groq AI (`GROQ_API_KEY`)**: High frequency. Rotate quarterly.
- **MongoDB Atlas (`MONGODB_URI`)**: High impact. Rotate biannually. Generate a new database user credential.
- **Firebase Auth (`FIREBASE_PRIVATE_KEY`)**: Critical impact. Rotate yearly.
- **Razorpay (`RAZORPAY_KEY_SECRET`)**: Financial impact. Rotate quarterly.

## Emergency Rollback
If the new green deployment causes issues that bypassed the health checks:
1. Go to the Render Dashboard -> `watchout-backend` -> Events.
2. Find the previous successful deploy and click "Rollback to this commit".
3. Render will redeploy using the *previous* environment variables (standard Render behavior). Wait for the old key to fail? 
   - *Wait*: If you already revoked the old key in Step 4, you must restore the working environment variables manually in the dashboard before rolling back. Therefore, **always wait 15 minutes before revoking old keys.**
