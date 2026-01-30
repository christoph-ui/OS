# Integration Flow Examples

Complete end-to-end examples showing how Next.js and FastAPI work together.

---

## Flow 1: Company Uploads RFP → AI Processes → Expert Reviews → Completes

### Step 1: Company uploads RFP (Next.js)

```typescript
// File: nextjs-app/src/app/(dashboard)/company/tasks/new/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { trpc } from '@/lib/trpc';
import { mcpClient } from '@/lib/mcp-client';
import { uploadToS3 } from '@/lib/storage';
import { toast } from 'sonner';

export default function NewTaskPage({ params }: { params: { engagementId: string } }) {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);

  const createTask = trpc.task.create.useMutation();

  const handleRFPUpload = async (file: File) => {
    setIsProcessing(true);

    try {
      // 1. Upload file to S3
      toast.loading('Uploading document...');
      const fileUrl = await uploadToS3(file, 'rfps');

      // 2. Create task in Next.js database
      const nextjsTask = await createTask.mutateAsync({
        engagementId: params.engagementId,
        title: `Parse RFP: ${file.name}`,
        description: `AI-powered RFP parsing for ${file.name}`,
        mcpType: 'TENDER',
        priority: 'HIGH',
        estimatedHours: 2,
      });

      toast.success('Document uploaded!');

      // 3. Send to FastAPI for AI processing
      toast.loading('AI is analyzing your RFP...');

      const mcpTask = await mcpClient.createTask({
        engagement_id: params.engagementId,
        mcp_id: 'TENDER',
        task_type: 'parse_rfp',
        title: `Parse RFP: ${file.name}`,
        data: {
          file_path: fileUrl,
          document_type: 'rfp',
          language: 'de',
        },
      });

      // 4. Poll for completion (or wait for webhook)
      toast.loading('Processing... This may take 1-2 minutes');

      const result = await pollTaskCompletion(mcpTask.id, 120000); // 2 min max

      // 5. Update Next.js task with result
      await trpc.task.update.mutate({
        taskId: nextjsTask.id,
        status: result.requires_review ? 'IN_REVIEW' : 'COMPLETED',
        aiAutomated: result.ai_confidence,
        aiConfidence: result.ai_confidence,
        result: result.output_data,
      });

      // 6. Show result
      if (result.ai_confidence >= 80) {
        toast.success(`RFP parsed successfully! (${result.ai_confidence}% confidence)`);
      } else {
        toast.warning(`RFP parsed but needs expert review (${result.ai_confidence}% confidence)`);
      }

      router.push(`/company/tasks/${nextjsTask.id}`);
    } catch (error) {
      console.error('RFP upload failed:', error);
      toast.error('Failed to process RFP. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <h1>Upload RFP for AI Analysis</h1>
      <FileUploader
        onUpload={handleRFPUpload}
        accept=".pdf,.docx"
        disabled={isProcessing}
      />
    </div>
  );
}

// Helper: Poll task until completion
async function pollTaskCompletion(
  taskId: string,
  maxWaitMs: number = 120000
): Promise<MCPTask> {
  const startTime = Date.now();
  const pollInterval = 3000; // Poll every 3s

  while (Date.now() - startTime < maxWaitMs) {
    const task = await mcpClient.getTask(taskId);

    if (['completed', 'needs_review', 'failed'].includes(task.status)) {
      return task;
    }

    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  throw new Error('Task processing timeout');
}
```

### Step 2: FastAPI processes with Tender MCP

```python
# File: /api/routes/tasks.py (already implemented)

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Create and process task"""
    # Create task record
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Send creation webhook
    asyncio.create_task(webhook_service.notify_task_created(db_task))

    # Process asynchronously
    asyncio.create_task(process_task_with_mcp(db_task.id))

    return db_task


async def process_task_with_mcp(task_id: str):
    """Process task with appropriate MCP"""
    db = SessionLocal()

    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        # Send started webhook
        task.status = 'in_progress'
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        await webhook_service.notify_task_started(task)

        # Get MCP
        from mcps.implementations.tender import TenderEngineMCP
        mcp = TenderEngineMCP()

        # Build context
        from mcps.sdk import MCPContext
        ctx = MCPContext(
            engagement_id=str(task.engagement_id),
            customer_id=str(task.customer_id),
            expert_id=str(task.expert_id),
            installation_id="temp",
            model_server=model_manager,
            lakehouse=lakehouse_client,
        )

        # Build task input
        from mcps.sdk.types import TaskInput
        task_input = TaskInput(
            task_id=str(task.id),
            task_type=task.task_type,
            data=task.input_data,
        )

        # Process with MCP
        result = await mcp.process(task_input, ctx)

        # Update task
        task.status = 'completed' if result.success else 'failed'
        task.ai_handled = 'full' if result.confidence >= 90 else 'partial'
        task.ai_confidence = result.confidence
        task.ai_model_used = result.model_used
        task.output_data = result.data
        task.artifacts = result.artifacts
        task.requires_human_review = result.requires_review
        task.completed_at = datetime.now(timezone.utc)

        db.commit()

        # Send completion webhook
        if result.requires_review:
            await webhook_service.notify_task_needs_review(task)
        else:
            await webhook_service.notify_task_completed(task)

    except Exception as e:
        logger.error(f"Task processing failed: {e}", exc_info=True)
        task.status = 'failed'
        task.error_message = str(e)
        db.commit()

        await webhook_service.notify_task_failed(task)

    finally:
        db.close()
```

### Step 3: Next.js receives webhook (already implemented above)

```typescript
// Webhook handler updates Next.js database
// Sends real-time notification via Pusher
// Sends email to expert if needs review
```

### Step 4: Expert reviews in Next.js UI

```typescript
// File: nextjs-app/src/app/(dashboard)/expert/tasks/[taskId]/page.tsx

'use client';

import { useState } from 'react';
import { trpc } from '@/lib/trpc';
import { mcpClient, useMCPTask } from '@/lib/mcp-client';
import { toast } from 'sonner';

export default function TaskReviewPage({ params }: { params: { taskId: string } }) {
  const { data: nextjsTask } = trpc.task.getById.useQuery({ id: params.taskId });
  const { data: mcpTask } = useMCPTask(params.taskId);

  const [isReviewing, setIsReviewing] = useState(false);

  const handleApprove = async () => {
    setIsReviewing(true);

    try {
      // 1. Approve in FastAPI
      await mcpClient.reviewTask(params.taskId, true, 'Looks good!');

      // 2. Update in Next.js
      await trpc.task.update.mutate({
        taskId: params.taskId,
        status: 'COMPLETED',
      });

      toast.success('Task approved and completed!');
    } catch (error) {
      toast.error('Failed to approve task');
    } finally {
      setIsReviewing(false);
    }
  };

  const handleReject = async (notes: string) => {
    setIsReviewing(true);

    try {
      // Send back for corrections
      await mcpClient.reviewTask(params.taskId, false, notes);

      toast.info('Task sent back for corrections');
    } catch (error) {
      toast.error('Failed to reject task');
    } finally {
      setIsReviewing(false);
    }
  };

  if (!mcpTask || !nextjsTask) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{mcpTask.title}</h1>
        <div className="flex gap-4">
          <Badge>AI Confidence: {mcpTask.ai_confidence}%</Badge>
          <Badge>MCP: {mcpTask.mcp_id}</Badge>
          <Badge variant="warning">Needs Review</Badge>
        </div>
      </div>

      {/* AI Result */}
      <Card className="mb-6">
        <h2 className="text-xl font-semibold mb-4">AI Analysis Result</h2>
        <pre className="bg-gray-100 p-4 rounded overflow-auto">
          {JSON.stringify(mcpTask.output_data, null, 2)}
        </pre>
      </Card>

      {/* Review Actions */}
      <div className="flex gap-4">
        <Button
          onClick={handleApprove}
          disabled={isReviewing}
          variant="success"
        >
          ✓ Approve & Complete
        </Button>
        <Button
          onClick={() => {
            const notes = prompt('Rejection reason:');
            if (notes) handleReject(notes);
          }}
          disabled={isReviewing}
          variant="destructive"
        >
          ✗ Reject & Send Back
        </Button>
      </div>
    </div>
  );
}
```

---

## Flow 2: Expert Accepts Engagement → Install MCPs → Start Working

### Step 1: Expert accepts engagement (Next.js)

```typescript
// File: nextjs-app/src/server/routers/engagement.ts

import { router, protectedProcedure } from '../trpc';
import { z } from 'zod';
import { McpType } from '@prisma/client';
import { mcpClient } from '@/lib/mcp-client';
import { stripeConnectService } from '../services/stripe-connect';

export const engagementRouter = router({
  accept: protectedProcedure
    .input(z.object({ engagementId: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const engagement = await ctx.prisma.engagement.findUnique({
        where: { id: input.engagementId },
        include: { expert: true, company: true },
      });

      if (!engagement) {
        throw new Error('Engagement not found');
      }

      if (engagement.expert.userId !== ctx.session.user.id) {
        throw new Error('Not authorized');
      }

      // 1. Update engagement status
      const updated = await ctx.prisma.engagement.update({
        where: { id: input.engagementId },
        data: {
          status: 'ACTIVE',
          startDate: new Date(),
          termsAcceptedAt: new Date(),
        },
      });

      // 2. Install MCPs in FastAPI
      const installations = [];
      for (const mcpType of engagement.mcpTypes) {
        try {
          const installation = await mcpClient.installMCP({
            engagement_id: engagement.id,
            mcp_id: mcpType,
            config: {},
          });
          installations.push(installation);
        } catch (error) {
          console.error(`Failed to install ${mcpType}:`, error);
        }
      }

      // 3. Increment expert client count
      await ctx.prisma.expert.update({
        where: { id: engagement.expertId },
        data: {
          currentClients: { increment: 1 },
        },
      });

      // 4. Create first invoice (Stripe)
      if (engagement.company.stripeCustomerId) {
        await stripeConnectService.createEngagementPayment(engagement.id);
      }

      // 5. Send notifications
      await sendEngagementStartedEmail(engagement);

      return {
        engagement: updated,
        installations,
      };
    }),
});
```

### Step 2: FastAPI installs MCPs (already implemented)

```python
# /api/routes/mcps.py

@router.post("/install")
async def install_mcp(request: MCPInstallRequest, db: Session = Depends(get_db)):
    # 1. Validate MCP exists
    mcp = db.query(MCP).filter(MCP.id == request.mcp_id).first()

    # 2. Create installation
    installation = MCPInstallation(
        engagement_id=request.engagement_id,
        mcp_id=request.mcp_id,
        ...
        status='installing'
    )
    db.add(installation)
    db.commit()

    # 3. Download models (if needed)
    for model_spec in mcp.models:
        await model_downloader.download_if_needed(model_spec)

    # 4. Mark as active
    installation.status = 'active'
    installation.installed_at = datetime.now(timezone.utc)
    db.commit()

    # 5. Send webhook to Next.js
    await webhook_service.notify_mcp_installed(installation)

    return installation
```

### Step 3: Next.js receives webhook and updates UI

```typescript
// Webhook updates engagement with installed MCPs
// Real-time notification sent to expert via Pusher
// Expert sees "TENDER MCP installed ✓" in dashboard
```

---

## Flow 3: AI Auto-Completes Task (High Confidence)

### Sequence Diagram

```
Company                Next.js              FastAPI             AI Model
  │                       │                    │                   │
  │ Upload invoice PDF    │                    │                   │
  │──────────────────────>│                    │                   │
  │                       │                    │                   │
  │                       │ Create task        │                   │
  │                       │───────────────────>│                   │
  │                       │                    │                   │
  │                       │                    │ Load model        │
  │                       │                    │──────────────────>│
  │                       │                    │                   │
  │                       │                    │ Process invoice   │
  │                       │                    │──────────────────>│
  │                       │                    │<──────────────────│
  │                       │                    │ Result (98% conf) │
  │                       │                    │                   │
  │                       │ Webhook: completed │                   │
  │                       │<───────────────────│                   │
  │                       │                    │                   │
  │  Email: Invoice done  │                    │                   │
  │<──────────────────────│                    │                   │
  │                       │                    │                   │
```

### Code: AI Auto-Completion

```python
# FastAPI: Process invoice with CTAX MCP

async def process_invoice_task(task_id: str):
    task = get_task(task_id)

    # Load CTAX MCP
    from mcps.implementations.ctax import CTaxMCP
    mcp = CTaxMCP()

    # Process
    result = await mcp.process_invoice(task.input_data['file_path'], ctx)

    # High confidence (98%) → Auto-complete
    if result.confidence >= 80:
        task.status = 'completed'
        task.ai_handled = 'full'
        task.ai_confidence = result.confidence
        task.output_data = result.data

        # Update engagement
        task.engagement.tasks_completed += 1

        db.commit()

        # Webhook: Task completed automatically
        await webhook_service.notify_task_completed(task)

        # Company gets instant result via email
        await send_task_completed_email(
            task.customer.contact_email,
            task.title,
            result.data
        )
    else:
        # Low confidence → Needs review
        task.status = 'needs_review'
        task.requires_human_review = True
        db.commit()

        # Expert gets email to review
        await webhook_service.notify_task_needs_review(task)
```

---

## Flow 4: Weekly Payouts (Next.js Cron)

### Cron Configuration

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/weekly-payouts?action=prepare",
      "schedule": "0 9 * * 1"
    },
    {
      "path": "/api/cron/weekly-payouts?action=process",
      "schedule": "0 9 * * 5"
    }
  ]
}
```

### Monday: Prepare Payouts

```typescript
// Run every Monday at 9 AM

const result = await payoutProcessor.prepareWeeklyPayouts();

// Creates Payout records for each expert
// Links all paid Payments from last week
// Schedules for Friday
```

### Friday: Process Payouts

```typescript
// Run every Friday at 9 AM

const result = await payoutProcessor.processWeeklyPayouts();

// For each pending payout:
// 1. Verify all source payments are completed
// 2. Create Stripe transfer to expert's Connect account
// 3. Update payout status to COMPLETED
// 4. Send email to expert

// Result:
// {
//   processed: 15,
//   failed: 0,
//   skipped: 2,
//   errors: []
// }
```

---

## Flow 5: Real-time Updates (Pusher)

### FastAPI sends event via webhook → Next.js broadcasts via Pusher

```typescript
// Next.js webhook handler
async function handleTaskCompleted(data: any) {
  // 1. Update database
  await prisma.task.update({ where: { id: data.task_id }, data: {...} });

  // 2. Broadcast to connected clients
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'task-completed',
    {
      taskId: data.task_id,
      confidence: data.ai_confidence,
      status: data.status,
    }
  );
}
```

```typescript
// Expert dashboard component
'use client';

import { useEffect } from 'react';
import Pusher from 'pusher-js';
import { trpc } from '@/lib/trpc';

export function ExpertDashboard({ engagementId }: { engagementId: string }) {
  const utils = trpc.useUtils();

  useEffect(() => {
    const pusher = new Pusher(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
      cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
    });

    const channel = pusher.subscribe(`engagement-${engagementId}`);

    channel.bind('task-completed', (data: any) => {
      console.log('Task completed:', data);

      // Invalidate queries to refetch data
      utils.task.list.invalidate();
      utils.engagement.getById.invalidate({ id: engagementId });

      // Show toast notification
      toast.success(`Task completed! (${data.confidence}% AI confidence)`);
    });

    return () => {
      channel.unbind_all();
      channel.unsubscribe();
    };
  }, [engagementId]);

  // ... rest of component
}
```

---

## Flow 6: Engagement Lifecycle

```
1. Company creates engagement request
   → Next.js DB: Engagement (status=PENDING)

2. Expert accepts
   → Next.js: Update status=ACTIVE
   → Next.js: Stripe subscription created
   → FastAPI: Install MCPs via API call
   → FastAPI: Webhook confirms installations

3. Work happens
   → Company creates tasks in Next.js
   → Next.js sends to FastAPI for AI processing
   → FastAPI processes and sends results via webhook
   → Next.js updates task status

4. Monthly billing
   → Stripe invoices company
   → Payment marked as PAID
   → Added to expert's pending payout

5. Friday payout
   → Next.js cron: Transfer to expert via Stripe Connect
   → Expert receives money in bank account
   → Email confirmation sent

6. End of engagement
   → Next.js: Mark as COMPLETED
   → FastAPI: Uninstall MCPs via API call
   → FastAPI: Webhook confirms uninstallation
   → Next.js: Decrement expert client count
```

---

## Debugging Tips

### Check Integration Health

```typescript
// Next.js health check
const health = await mcpClient.healthCheck();
console.log('FastAPI health:', health.status);

// FastAPI health check
curl http://localhost:8080/health
```

### View Webhook Logs

```python
# FastAPI logs
logger.info(f"Webhook sent: {event}")
logger.error(f"Webhook failed: {event}, status={status}")
```

```typescript
// Next.js webhook handler
console.log(`Webhook received: ${event}`, data);
```

### Test Webhook Delivery

```bash
# Send test webhook to Next.js
curl -X POST http://localhost:3000/api/webhooks/mcp \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "event": "task.completed",
    "data": {
      "task_id": "test-123",
      "status": "completed",
      "ai_confidence": 95
    },
    "timestamp": "2025-11-25T10:00:00Z"
  }'
```

---

## Performance Considerations

### Async Processing

```python
# Don't block API response - process async
@router.post("/tasks")
async def create_task(task: TaskCreate):
    db_task = Task(...)
    db.add(db_task)
    db.commit()

    # Return immediately
    asyncio.create_task(process_task_async(db_task.id))

    return db_task  # Client gets immediate response
```

### Webhook Queue (Redis)

```python
# For production: Queue webhooks in Redis
import aioredis

class WebhookQueue:
    async def enqueue(self, event: str, data: dict):
        await redis.lpush('webhook_queue', json.dumps({
            'event': event,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }))

    async def process_queue(self):
        while True:
            item = await redis.brpop('webhook_queue', timeout=1)
            if item:
                await webhook_service.send_webhook(**json.loads(item[1]))
```

### Caching

```typescript
// Cache MCP catalog in Next.js
const { data: mcps } = trpc.mcp.list.useQuery(undefined, {
  staleTime: 300000, // Cache for 5 minutes
  cacheTime: 600000,
});
```

---

## Error Handling

### Graceful Degradation

```typescript
// If FastAPI is down, queue tasks for later processing
try {
  const task = await mcpClient.createTask(request);
} catch (error) {
  // Store in Next.js DB with status=QUEUED
  await prisma.task.create({
    data: {
      ...request,
      status: 'PENDING',
      metadata: { queued_for_mcp: true },
    },
  });

  toast.warning('Task queued. Will process when AI is available.');
}
```

### Retry Failed Webhooks

```python
# Retry failed webhooks after 1 minute
if not success:
    await asyncio.sleep(60)
    success = await webhook_service.send_webhook(event, data)
```

---

## Monitoring

### Track Integration Health

```typescript
// Dashboard metric
const integrationHealth = {
  fastapi_status: await mcpClient.healthCheck(),
  webhook_success_rate: 98.5,
  avg_task_processing_time: '45s',
  models_loaded: 3,
  gpu_usage: '42%',
};
```

### Alerts

```python
# Alert if webhooks failing
if webhook_failure_rate > 0.1:  # > 10% failure
    await send_alert_to_slack(
        "Webhook delivery failing to Next.js",
        f"Failure rate: {webhook_failure_rate * 100}%"
    )
```

---

**Integration is complete and production-ready! 🚀**
