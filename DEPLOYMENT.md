# Deploy Canvas→Notion Sync to Vercel

This guide will help you deploy your Canvas assignment sync as a cloud function that can be triggered from a Notion button.

## Prerequisites

1. **Vercel Account** (free): https://vercel.com/signup
2. **Notion Integration Token**: Create at https://www.notion.so/my-integrations
3. **Canvas ICS URL**: You already have this (it's in canvas_to_notion_sync.py)

## Step 1: Create a Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click **"+ New integration"**
3. Name it: **"Canvas Sync"**
4. Select your workspace
5. Click **"Submit"**
6. **Copy the "Internal Integration Token"** (starts with `secret_...`)
7. Keep this safe - you'll need it in Step 4

## Step 2: Connect Integration to Your Database

1. Open your **"Tasks"** database in Notion
2. Click the **"..."** menu (top right)
3. Scroll down and click **"+ Add connections"**
4. Select **"Canvas Sync"** integration
5. Click **"Confirm"**

This gives the integration permission to create tasks in your database.

## Step 3: Install Vercel CLI

Open Terminal and run:

```bash
npm install -g vercel
```

If you don't have npm, install it first:
```bash
brew install node
```

## Step 4: Deploy to Vercel

1. Open Terminal and navigate to this directory:
   ```bash
   cd "/Users/budrey/Desktop/Notion x Canvas"
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```
   Follow the prompts to authenticate.

3. Deploy the project:
   ```bash
   vercel
   ```

4. Answer the prompts:
   - **Set up and deploy?** → Yes
   - **Which scope?** → Select your account
   - **Link to existing project?** → No
   - **Project name?** → `canvas-notion-sync` (or whatever you prefer)
   - **Directory?** → `.` (press Enter)
   - **Override settings?** → No

5. **Add environment variables:**

   After deployment, add your secrets:

   ```bash
   vercel env add CANVAS_ICS_URL
   ```
   Paste: `https://canvas.illinois.edu/feeds/calendars/user_XW4gRxHVVylnq1i5ro4T8rrecKOSXDZLip72fOf5.ics`
   Select: **Production** (press Space, then Enter)

   ```bash
   vercel env add NOTION_API_TOKEN
   ```
   Paste your Notion integration token (from Step 1)
   Select: **Production**

   ```bash
   vercel env add TASKS_DATABASE_ID
   ```
   Paste: `23e399d3-5713-805c-9c0a-000be677710c`
   Select: **Production**

6. **Redeploy with environment variables:**
   ```bash
   vercel --prod
   ```

7. **Get your webhook URL:**

   After deployment completes, you'll see:
   ```
   ✅ Production: https://canvas-notion-sync-xxxxx.vercel.app [1s]
   ```

   Your webhook URL is:
   ```
   https://canvas-notion-sync-xxxxx.vercel.app/api/sync
   ```

   **Copy this URL - you'll need it for Notion!**

## Step 5: Test the Webhook

Test it in your browser or with curl:

```bash
curl https://YOUR-URL.vercel.app/api/sync
```

You should see a JSON response like:
```json
{
  "success": true,
  "total_assignments": 15,
  "created": 3,
  "skipped": 12,
  "errors": []
}
```

## Step 6: Connect to Notion Button

Now, set up your Notion button to call this webhook:

### Option A: Using Notion Automations (Recommended)

1. In your **"Audrey's workspace"** page in Notion
2. Make sure your button exists (you mentioned you created one called "update projects")
3. Click the button to edit it
4. In the button settings:
   - **Button label:** "Update Projects" (or whatever you want)
   - **Action:** Click "+ Add automation"

5. Create the automation:
   - **Trigger:** "Button clicked"
   - **Action:** "Send notification" → but we'll actually use a workaround

   **NOTE:** Notion doesn't natively support webhook calls from buttons yet. You have two options:

### Option B: Use Make.com or Zapier (Free tier available)

1. Create a free account at https://make.com or https://zapier.com
2. Create a new scenario/zap:
   - **Trigger:** Webhook (they'll give you a URL)
   - **Action:** HTTP Request to your Vercel URL

3. In Notion:
   - Create a database with one row
   - Add automation: "When database updated" → Call webhook
   - Your button can update this database row

### Option C: Direct Link (Simplest)

Instead of a complex automation, make your button:
1. Open the button properties
2. Set action to: **"Open link"**
3. URL: Your Vercel webhook URL
4. This will open the sync URL in a new tab when clicked

The downside: You'll see a JSON response page instead of staying in Notion.

### Option D: Bookmark (Even Simpler!)

1. Bookmark this URL in your browser: `https://YOUR-URL.vercel.app/api/sync`
2. Click it whenever you want to sync
3. Keep the button in Notion as a reminder, or replace it with the bookmark

## Step 7: Set Up Automatic Daily Sync (Optional)

Vercel doesn't have built-in cron, but you can use:

### Option 1: Cron-job.org (Free)
1. Go to https://cron-job.org
2. Create free account
3. Add new cron job:
   - **URL:** Your Vercel webhook
   - **Schedule:** Every day at 7:00 AM
   - **Enabled:** Yes

### Option 2: GitHub Actions (Free)
I can help you set up a GitHub Action that runs daily if you prefer.

## Troubleshooting

**Error: "CANVAS_ICS_URL not configured"**
- Run: `vercel env ls` to check if variables are set
- Make sure you ran `vercel --prod` after adding env variables

**Error: "NOTION_API_TOKEN not configured"**
- Double-check you added the integration token correctly
- Make sure the token starts with `secret_`

**No tasks created (created: 0)**
- Check that assignments are in the future (past assignments are skipped)
- Verify your course codes in COURSE_MAPPING match Canvas

**Tasks created but not linked to projects**
- Make sure the Notion project IDs in api/sync.py are correct
- Check that the project pages exist

## Updating Course Mappings

If you add new courses, edit `api/sync.py` line 21-31:

```python
COURSE_MAPPING = {
    "NEW COURSE 101": "notion-page-id-here",
    # ... existing courses
}
```

Then redeploy:
```bash
vercel --prod
```

## Next Steps

1. ✅ Deploy to Vercel
2. ✅ Test the webhook
3. ✅ Set up Notion button (choose Option C or D for simplest)
4. ✅ Optional: Set up daily auto-sync with cron-job.org

You now have a cloud function that syncs Canvas to Notion on demand!
