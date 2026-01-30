# 0711 Platform Integration Guide

**Connecting Next.js Expert Network ↔ FastAPI MCP Platform**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  NEXT.JS EXPERT NETWORK (Port 3000)                             │
│  Responsibilities:                                              │
│  ✓ User authentication & sessions                              │
│  ✓ Expert/Company profiles & matching                          │
│  ✓ Engagement contracts                                         │
│  ✓ Stripe payments & payouts                                    │
│  ✓ React UI & real-time updates                                │
│                                                                  │
│  Database: Prisma + PostgreSQL (Users, Engagements, Payments)  │
└─────────────────────────────────────────────────────────────────┘
                    │                          ↑
                    │ REST API                 │
                    ↓                          │ Webhooks
┌─────────────────────────────────────────────────────────────────┐
│  FASTAPI MCP PLATFORM (Port 8080)                               │
│  Responsibilities:                                              │
│  ✓ MCP SDK & marketplace                                       │
│  ✓ AI task processing & orchestration                          │
│  ✓ Model loading & vLLM management                             │
│  ✓ Lakehouse (Delta Lake + LanceDB)                            │
│  ✓ Document processing & AI inference                          │
│                                                                  │
│  Database: SQLAlchemy + PostgreSQL (MCPs, Tasks, Installations)│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow & Ownership

### Next.js Owns
- `User` - Auth, profiles, sessions
- `Expert` - Personal info, availability, ratings
- `Company` - Company info, billing
- `Engagement` - Contracts between experts & companies
- `Payment` - Stripe invoices from companies
- `Payout` - Weekly payouts to experts
- `Review` - Expert reviews
- `Message` - Chat between expert & company

### FastAPI Owns
- `MCP` - MCP catalog & metadata
- `Task` - AI-driven work items with results
- `MCPInstallation` - Deployed MCPs
- `Model` stats - GPU usage, loading state
- Lakehouse data - Document storage, vectors

### Shared Data (Synchronized)
- `engagement_id` - Links Next.js engagement to FastAPI tasks
- `expert_id` / `customer_id` - Cross-referenced in both systems
- Task status - Updated by FastAPI, read by Next.js

---

## 🔌 Integration Patterns

### Pattern 1: Next.js → FastAPI (Direct API Calls)

**Use for**: Creating tasks, checking MCP status, fetching AI results

```typescript
// Next.js calls FastAPI
const mcpClient = createMCPClient(process.env.FASTAPI_URL);

// Create AI task
const task = await mcpClient.createTask({
  engagement_id: engagement.id,
  mcp_id: 'TENDER',
  task_type: 'parse_rfp',
  data: { file_path: documentUrl }
});

// Check task status
const status = await mcpClient.getTask(task.id);

// Get AI result
if (status.status === 'completed') {
  const result = status.output_data;
}
```

### Pattern 2: FastAPI → Next.js (Webhooks)

**Use for**: Task completion, model events, errors

```python
# FastAPI sends webhook to Next.js when task completes
async def on_task_complete(task: Task):
    await send_webhook(
        url=f"{NEXTJS_URL}/api/webhooks/mcp",
        event="task.completed",
        data={
            "task_id": str(task.id),
            "engagement_id": str(task.engagement_id),
            "status": task.status,
            "ai_confidence": task.ai_confidence,
            "output_data": task.output_data
        }
    )
```

### Pattern 3: Polling (For Real-time Updates)

**Use for**: Live task status, model loading state

```typescript
// Next.js polls FastAPI for task updates
const { data } = useQuery({
  queryKey: ['task', taskId],
  queryFn: () => mcpClient.getTask(taskId),
  refetchInterval: 5000, // Poll every 5s while in_progress
  enabled: status === 'in_progress'
});
```

---

## 📡 API Client Implementation

### File: `nextjs-app/src/lib/mcp-client.ts`

```typescript
/**
 * MCP Platform Client
 *
 * Type-safe wrapper for calling FastAPI MCP Platform
 */

import axios, { AxiosInstance } from 'axios';

interface MCPTask {
  id: string;
  engagement_id: string;
  expert_id: string;
  customer_id: string;
  mcp_id: string;
  title: string;
  description?: string;
  task_type: string;
  status: 'todo' | 'in_progress' | 'needs_review' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  ai_handled: 'no' | 'partial' | 'full';
  ai_confidence: number;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  created_at: string;
  completed_at?: string;
}

interface CreateTaskRequest {
  engagement_id: string;
  mcp_id: string;
  task_type: string;
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  data: Record<string, any>;
  due_date?: string;
}

interface MCPInstallation {
  id: string;
  engagement_id: string;
  mcp_id: string;
  customer_id: string;
  expert_id: string;
  version: string;
  status: 'pending' | 'installing' | 'active' | 'paused' | 'error';
  health_score: number;
  automation_rate: number;
  total_requests: number;
}

interface MCP {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  color: string;
  tools: string[];
  automation_rate: number;
  pricing_model: string;
  subscription_monthly_cents: number;
  usage_price_per_unit_cents: number;
}

export class MCPClient {
  private client: AxiosInstance;

  constructor(baseURL: string, apiKey?: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'X-API-Key': apiKey }),
      },
      timeout: 30000,
    });
  }

  // =========================================================================
  // TASKS
  // =========================================================================

  async createTask(request: CreateTaskRequest): Promise<MCPTask> {
    const response = await this.client.post<MCPTask>('/api/tasks', request);
    return response.data;
  }

  async getTask(taskId: string): Promise<MCPTask> {
    const response = await this.client.get<MCPTask>(`/api/tasks/${taskId}`);
    return response.data;
  }

  async listTasks(params: {
    engagement_id?: string;
    expert_id?: string;
    status?: string;
    limit?: number;
  }): Promise<{ tasks: MCPTask[]; total: number }> {
    const response = await this.client.get('/api/tasks', { params });
    return response.data;
  }

  async completeTask(taskId: string, outputData: Record<string, any>): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'complete',
      output_data: outputData,
    });
  }

  async reviewTask(taskId: string, approve: boolean, notes?: string): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'review',
      approve,
      notes,
    });
  }

  // =========================================================================
  // MCPs
  // =========================================================================

  async listMCPs(params?: {
    category?: string;
    search?: string;
  }): Promise<{ mcps: MCP[]; total: number }> {
    const response = await this.client.get('/api/mcps/catalog', { params });
    return response.data;
  }

  async getMCP(mcpId: string): Promise<MCP> {
    const response = await this.client.get<MCP>(`/api/mcps/${mcpId}`);
    return response.data;
  }

  async installMCP(params: {
    engagement_id: string;
    mcp_id: string;
    config?: Record<string, any>;
  }): Promise<MCPInstallation> {
    const response = await this.client.post<MCPInstallation>(
      '/api/mcps/install',
      params
    );
    return response.data;
  }

  async listInstallations(params: {
    engagement_id?: string;
    expert_id?: string;
  }): Promise<MCPInstallation[]> {
    const response = await this.client.get('/api/mcps/installations', { params });
    return response.data;
  }

  // =========================================================================
  // EXPERTS (Dashboard Data)
  // =========================================================================

  async getExpertDashboard(expertId: string): Promise<any> {
    const response = await this.client.get(`/api/experts/dashboard`, {
      params: { expert_id: expertId },
    });
    return response.data;
  }

  async getExpertClients(expertId: string): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/clients`);
    return response.data;
  }

  async getExpertEarnings(expertId: string): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/earnings`);
    return response.data;
  }

  // =========================================================================
  // MODEL STATUS
  // =========================================================================

  async getModelStats(): Promise<any> {
    const response = await this.client.get('/api/models/stats');
    return response.data;
  }

  async getLoadedModels(): Promise<string[]> {
    const response = await this.client.get('/api/models/loaded');
    return response.data;
  }
}

// Singleton instance
export const mcpClient = new MCPClient(
  process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8080',
  process.env.FASTAPI_API_KEY
);

// React hooks
export function useMCPTask(taskId: string) {
  return useQuery({
    queryKey: ['mcp-task', taskId],
    queryFn: () => mcpClient.getTask(taskId),
    refetchInterval: (data) => {
      // Poll every 5s if in progress
      return data?.status === 'in_progress' ? 5000 : false;
    },
  });
}

export function useCreateMCPTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: mcpClient.createTask.bind(mcpClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-tasks'] });
    },
  });
}
```

---

## 🪝 FastAPI Webhook System

### File: `/api/webhooks.py`

```python
"""
Webhook system for notifying Next.js of events
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebhookService:
    """Send webhooks to Next.js app"""

    def __init__(self, nextjs_url: str, webhook_secret: str):
        self.nextjs_url = nextjs_url
        self.webhook_secret = webhook_secret

    async def send_webhook(
        self,
        event: str,
        data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> bool:
        """
        Send webhook to Next.js

        Args:
            event: Event name (e.g., 'task.completed')
            data: Event data
            idempotency_key: Optional key to prevent duplicate processing

        Returns:
            True if successful
        """
        url = f"{self.nextjs_url}/api/webhooks/mcp"

        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Secret": self.webhook_secret,
        }

        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(f"Webhook sent: {event}")
                    return True
                else:
                    logger.error(
                        f"Webhook failed: {event}, "
                        f"status={response.status_code}, "
                        f"response={response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Webhook exception: {event}, error={e}")
            return False


# Initialize webhook service
from api.config import settings

webhook_service = WebhookService(
    nextjs_url=settings.nextjs_url,
    webhook_secret=settings.webhook_secret
)


# ============================================================================
# WEBHOOK EVENTS
# ============================================================================

async def notify_task_created(task):
    """Notify Next.js when task is created"""
    await webhook_service.send_webhook(
        event="task.created",
        data={
            "task_id": str(task.id),
            "engagement_id": str(task.engagement_id),
            "expert_id": str(task.expert_id),
            "customer_id": str(task.customer_id),
            "mcp_id": task.mcp_id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
        },
        idempotency_key=f"task.created.{task.id}"
    )


async def notify_task_completed(task):
    """Notify Next.js when task is completed"""
    await webhook_service.send_webhook(
        event="task.completed",
        data={
            "task_id": str(task.id),
            "engagement_id": str(task.engagement_id),
            "expert_id": str(task.expert_id),
            "customer_id": str(task.customer_id),
            "status": task.status,
            "ai_handled": task.ai_handled,
            "ai_confidence": task.ai_confidence,
            "output_data": task.output_data,
            "requires_review": task.requires_human_review,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        },
        idempotency_key=f"task.completed.{task.id}"
    )


async def notify_task_needs_review(task):
    """Notify Next.js when task needs expert review"""
    await webhook_service.send_webhook(
        event="task.needs_review",
        data={
            "task_id": str(task.id),
            "engagement_id": str(task.engagement_id),
            "expert_id": str(task.expert_id),
            "title": task.title,
            "ai_confidence": task.ai_confidence,
            "output_data": task.output_data,
        }
    )


async def notify_mcp_installed(installation):
    """Notify Next.js when MCP is installed"""
    await webhook_service.send_webhook(
        event="mcp.installed",
        data={
            "installation_id": str(installation.id),
            "engagement_id": str(installation.engagement_id),
            "mcp_id": installation.mcp_id,
            "status": installation.status,
        }
    )
```

### File: `/api/config.py` (Add webhook settings)

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Integration with Next.js
    nextjs_url: str = "http://localhost:3000"
    webhook_secret: str  # Shared secret for webhook verification
    fastapi_api_key: str  # API key for Next.js → FastAPI calls

    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
```

---

## 🔐 Authentication & Security

### API Key Authentication (Next.js → FastAPI)

```python
# File: /api/middleware/auth.py

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.config import settings

security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> bool:
    """Verify API key from Next.js"""
    if credentials.credentials != settings.fastapi_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True


# Use in routes
@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    authenticated: bool = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    # ...
```

### Webhook Signature Verification (FastAPI → Next.js)

```typescript
// File: nextjs-app/src/app/api/webhooks/mcp/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';

function verifyWebhookSignature(request: NextRequest): boolean {
  const headersList = headers();
  const signature = headersList.get('X-Webhook-Secret');
  return signature === process.env.WEBHOOK_SECRET;
}

export async function POST(request: NextRequest) {
  if (!verifyWebhookSignature(request)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const payload = await request.json();
  const { event, data } = payload;

  // Handle events
  switch (event) {
    case 'task.completed':
      await handleTaskCompleted(data);
      break;

    case 'task.needs_review':
      await handleTaskNeedsReview(data);
      break;

    case 'mcp.installed':
      await handleMCPInstalled(data);
      break;

    default:
      console.warn(`Unknown event: ${event}`);
  }

  return NextResponse.json({ received: true });
}

async function handleTaskCompleted(data: any) {
  // Update task in Prisma DB
  await prisma.task.update({
    where: { id: data.task_id },
    data: {
      status: 'COMPLETED',
      aiAutomated: data.ai_handled === 'full' ? 100 : data.ai_handled === 'partial' ? 50 : 0,
      aiConfidence: data.ai_confidence,
      completedAt: new Date(data.completed_at),
    },
  });

  // Send real-time notification to expert
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'task-completed',
    data
  );

  // Send email if needs review
  if (data.requires_review) {
    await sendTaskReviewEmail(data.expert_id, data.task_id);
  }
}
```

---

## 🔄 Complete Integration Flows

### Flow 1: Company Uploads RFP → AI Processes → Expert Reviews

```typescript
// ============================================================================
// NEXT.JS: Company uploads RFP document
// ============================================================================

// 1. Upload file to S3
const file = await uploadToS3(rfpFile);

// 2. Create engagement task in Next.js DB
const task = await prisma.task.create({
  data: {
    engagementId: engagement.id,
    expertId: engagement.expertId,
    companyId: engagement.companyId,
    title: 'Parse RFP: Municipal IT Tender',
    description: file.name,
    mcpType: 'TENDER',
    status: 'IN_PROGRESS',
  },
});

// 3. Send to FastAPI for AI processing
const mcpTask = await mcpClient.createTask({
  engagement_id: engagement.id,
  mcp_id: 'TENDER',
  task_type: 'parse_rfp',
  title: task.title,
  data: {
    file_path: file.url,
    document_type: 'rfp',
    language: 'de',
  },
});

// 4. Poll for completion (or wait for webhook)
const interval = setInterval(async () => {
  const status = await mcpClient.getTask(mcpTask.id);

  if (status.status === 'completed' || status.status === 'needs_review') {
    clearInterval(interval);

    // Update Next.js task
    await prisma.task.update({
      where: { id: task.id },
      data: {
        status: status.requires_review ? 'IN_REVIEW' : 'COMPLETED',
        aiAutomated: status.ai_confidence,
        result: status.output_data,
      },
    });

    // Notify expert if needs review
    if (status.requires_review) {
      await sendPushNotification(engagement.expertId, {
        title: 'Task needs your review',
        body: `RFP parsing completed with ${status.ai_confidence}% confidence`,
        data: { taskId: task.id },
      });
    }
  }
}, 5000);
```

```python
# ============================================================================
# FASTAPI: Process RFP with Tender MCP
# ============================================================================

from mcps.implementations.tender import TenderEngineMCP
from mcps.sdk import MCPContext, TaskInput

@router.post("/tasks")
async def create_task(
    task_req: TaskCreate,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    # Create task record
    task = Task(**task_req.dict())
    db.add(task)
    db.commit()

    # Send creation webhook
    await notify_task_created(task)

    # Process asynchronously
    asyncio.create_task(process_task_async(task.id))

    return task


async def process_task_async(task_id: str):
    """Process task with MCP in background"""
    db = SessionLocal()

    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        # Get MCP
        mcp = TenderEngineMCP()

        # Build context
        ctx = MCPContext(
            engagement_id=str(task.engagement_id),
            customer_id=str(task.customer_id),
            expert_id=str(task.expert_id),
            installation_id="...",
            model_server=model_manager,
            lakehouse=lakehouse_client,
        )

        # Build task input
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
        task.output_data = result.data
        task.requires_human_review = result.requires_review
        task.completed_at = datetime.now(timezone.utc)

        db.commit()

        # Send completion webhook
        if result.requires_review:
            await notify_task_needs_review(task)
        else:
            await notify_task_completed(task)

    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        task.status = 'failed'
        task.error_message = str(e)
        db.commit()

    finally:
        db.close()
```

---

### Flow 2: Expert Creates Engagement → Install MCPs → Start Working

```typescript
// ============================================================================
// NEXT.JS: Expert accepts engagement
// ============================================================================

// In tRPC router
async acceptEngagement({ engagementId }) {
  // 1. Update engagement in Prisma
  const engagement = await prisma.engagement.update({
    where: { id: engagementId },
    data: { status: 'ACTIVE', startDate: new Date() },
  });

  // 2. Install MCPs in FastAPI
  for (const mcpType of engagement.mcpTypes) {
    await mcpClient.installMCP({
      engagement_id: engagement.id,
      mcp_id: mcpType,
      config: {},
    });
  }

  // 3. Create Stripe subscription
  await stripeConnectService.createEngagementPayment(engagement.id);

  return engagement;
}
```

```python
# ============================================================================
# FASTAPI: Install MCP for engagement
# ============================================================================

@router.post("/mcps/install")
async def install_mcp(
    request: MCPInstallRequest,
    db: Session = Depends(get_db)
):
    # Create installation record
    installation = MCPInstallation(
        engagement_id=request.engagement_id,
        mcp_id=request.mcp_id,
        customer_id=request.customer_id,
        expert_id=request.expert_id,
        status='installing',
    )
    db.add(installation)
    db.commit()

    # Download models (if not cached)
    mcp = db.query(MCP).filter(MCP.id == request.mcp_id).first()
    for model_spec in mcp.models:
        await model_downloader.ensure_downloaded(model_spec)

    # Mark as active
    installation.status = 'active'
    installation.activated_at = datetime.now(timezone.utc)
    db.commit()

    # Send webhook
    await notify_mcp_installed(installation)

    return installation
```

---

## 📊 Data Synchronization

### Sync Service (Runs every 5 minutes)

```python
# File: /api/services/sync_service.py

"""
Synchronize data between Next.js and FastAPI
"""

from sqlalchemy.orm import Session
from api.models import Expert, Customer, Engagement
import httpx


class SyncService:
    """Sync data from Next.js to FastAPI"""

    def __init__(self, nextjs_api_url: str, api_key: str):
        self.nextjs_api_url = nextjs_api_url
        self.api_key = api_key

    async def sync_experts(self, db: Session):
        """Sync expert data from Next.js"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.nextjs_api_url}/api/sync/experts",
                headers={"X-API-Key": self.api_key}
            )

            experts_data = response.json()

            for expert_data in experts_data:
                # Upsert expert
                expert = db.query(Expert).filter(
                    Expert.id == expert_data['id']
                ).first()

                if expert:
                    # Update existing
                    expert.first_name = expert_data['first_name']
                    expert.last_name = expert_data['last_name']
                    expert.certified_mcps = expert_data['certified_mcps']
                    # ... update other fields
                else:
                    # Create new
                    expert = Expert(**expert_data)
                    db.add(expert)

            db.commit()

    async def sync_engagements(self, db: Session):
        """Sync engagement data from Next.js"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.nextjs_api_url}/api/sync/engagements",
                headers={"X-API-Key": self.api_key}
            )

            engagements_data = response.json()

            for eng_data in engagements_data:
                engagement = db.query(Engagement).filter(
                    Engagement.id == eng_data['id']
                ).first()

                if engagement:
                    engagement.status = eng_data['status']
                    engagement.mcp_ids = eng_data['mcp_types']
                else:
                    engagement = Engagement(**eng_data)
                    db.add(engagement)

            db.commit()
```

### Next.js Sync Endpoint

```typescript
// File: nextjs-app/src/app/api/sync/experts/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

function verifyAPIKey(request: NextRequest): boolean {
  const apiKey = request.headers.get('X-API-Key');
  return apiKey === process.env.FASTAPI_API_KEY;
}

export async function GET(request: NextRequest) {
  if (!verifyAPIKey(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const experts = await prisma.expert.findMany({
    where: { status: 'ACTIVE' },
    include: {
      user: { select: { id: true, email: true, name: true } },
      mcpExpertise: true,
    },
  });

  // Transform to FastAPI format
  const expertsData = experts.map((expert) => ({
    id: expert.id,
    first_name: expert.user.name?.split(' ')[0] || '',
    last_name: expert.user.name?.split(' ')[1] || '',
    email: expert.user.email,
    title: expert.title,
    domain: expert.mcpExpertise[0]?.mcpType || 'General',
    certified_mcps: expert.mcpExpertise.map((e) => e.mcpType),
    max_clients: expert.maxClients,
    current_clients: expert.currentClients,
    rating: Number(expert.avgRating),
    automation_rate: Number(expert.aiAutomationRate),
  }));

  return NextResponse.json(expertsData);
}
```

---

## 🚀 Deployment Configuration

### Environment Variables

```bash
# .env (Both systems need these)

# Shared Database (Optional - can use separate DBs)
DATABASE_URL="postgresql://0711:password@localhost:5432/0711_shared"

# Next.js → FastAPI
NEXT_PUBLIC_FASTAPI_URL="http://localhost:8080"  # Dev
# NEXT_PUBLIC_FASTAPI_URL="https://api.0711.io"  # Prod
FASTAPI_API_KEY="secret_key_here"

# FastAPI → Next.js
NEXTJS_URL="http://localhost:3000"  # Dev
# NEXTJS_URL="https://0711.io"  # Prod
WEBHOOK_SECRET="shared_webhook_secret"
```

### Docker Compose (Both Systems)

```yaml
version: '3.8'

services:
  # Shared PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: 0711
      POSTGRES_PASSWORD: 0711_dev
      POSTGRES_DB: 0711_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - 0711-network

  # Redis (shared cache)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - 0711-network

  # FastAPI - MCP Platform
  fastapi:
    build:
      context: ./0711-OS
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://0711:0711_dev@postgres:5432/0711_platform
      - REDIS_URL=redis://redis:6379
      - NEXTJS_URL=http://nextjs:3000
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - VLLM_URL=http://vllm:8000
    ports:
      - "8080:8080"
    volumes:
      - ./0711-OS:/app
    depends_on:
      - postgres
      - redis
    networks:
      - 0711-network

  # Next.js - Expert Network
  nextjs:
    build:
      context: ./expert-network
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://0711:0711_dev@postgres:5432/0711_platform
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXT_PUBLIC_FASTAPI_URL=http://fastapi:8080
      - FASTAPI_API_KEY=${FASTAPI_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    ports:
      - "3000:3000"
    volumes:
      - ./expert-network:/app
    depends_on:
      - postgres
      - fastapi
    networks:
      - 0711-network

  # vLLM (GPU required)
  # vllm:
  #   image: vllm/vllm-openai:latest
  #   ports:
  #     - "8000:8000"
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             capabilities: [gpu]
  #   networks:
  #     - 0711-network

networks:
  0711-network:
    driver: bridge

volumes:
  postgres_data:
```

---

## 📋 Integration Checklist

### Setup Tasks

- [ ] Add `NEXTJS_URL` and `WEBHOOK_SECRET` to FastAPI config
- [ ] Add `NEXT_PUBLIC_FASTAPI_URL` and `FASTAPI_API_KEY` to Next.js
- [ ] Implement API key middleware in FastAPI
- [ ] Implement webhook signature verification in Next.js
- [ ] Create webhook handler at `/api/webhooks/mcp`
- [ ] Add webhook calls to task completion in FastAPI
- [ ] Build MCP client wrapper in Next.js
- [ ] Test end-to-end flow: Create task → AI process → Webhook → Update UI

### Production Requirements

- [ ] Use HTTPS for all inter-service communication
- [ ] Implement retry logic for failed webhooks
- [ ] Add webhook delivery queue (Redis)
- [ ] Monitor webhook delivery success rate
- [ ] Setup Sentry for error tracking in both systems
- [ ] Configure CORS properly
- [ ] Rate limit API endpoints
- [ ] Add request logging with trace IDs

---

## 🧪 Testing Integration

```typescript
// File: nextjs-app/tests/integration/mcp-integration.test.ts

import { describe, it, expect, beforeAll } from 'vitest';
import { mcpClient } from '@/lib/mcp-client';

describe('MCP Platform Integration', () => {
  let testEngagementId: string;
  let testTaskId: string;

  beforeAll(async () => {
    // Setup test engagement
    testEngagementId = 'test-engagement-123';
  });

  it('should create task in FastAPI', async () => {
    const task = await mcpClient.createTask({
      engagement_id: testEngagementId,
      mcp_id: 'TENDER',
      task_type: 'parse_rfp',
      title: 'Test RFP Parsing',
      data: { file_path: '/test/rfp.pdf' },
    });

    expect(task).toBeDefined();
    expect(task.status).toBe('todo');
    testTaskId = task.id;
  });

  it('should retrieve task status', async () => {
    const task = await mcpClient.getTask(testTaskId);
    expect(task.id).toBe(testTaskId);
  });

  it('should list MCPs', async () => {
    const result = await mcpClient.listMCPs({ category: 'Sales' });
    expect(result.mcps.length).toBeGreaterThan(0);
    expect(result.mcps.some((m) => m.id === 'TENDER')).toBe(true);
  });

  it('should install MCP', async () => {
    const installation = await mcpClient.installMCP({
      engagement_id: testEngagementId,
      mcp_id: 'TENDER',
    });

    expect(installation.status).toBe('active');
  });
});
```

---

## 📖 Quick Reference

### Next.js → FastAPI Calls

| Action | Endpoint | Method |
|--------|----------|--------|
| Create task | `/api/tasks` | POST |
| Get task | `/api/tasks/{id}` | GET |
| List tasks | `/api/tasks?engagement_id=...` | GET |
| Install MCP | `/api/mcps/install` | POST |
| List MCPs | `/api/mcps/catalog` | GET |
| Get expert dashboard | `/api/experts/dashboard?expert_id=...` | GET |

### FastAPI → Next.js Webhooks

| Event | Payload |
|-------|---------|
| `task.created` | `{task_id, engagement_id, expert_id, ...}` |
| `task.completed` | `{task_id, status, ai_confidence, output_data}` |
| `task.needs_review` | `{task_id, ai_confidence, reason}` |
| `task.failed` | `{task_id, error_message}` |
| `mcp.installed` | `{installation_id, mcp_id, status}` |
| `model.loaded` | `{model_name, memory_gb}` |

---

## 🎯 Summary

**Next.js** handles:
- User experience (auth, profiles, dashboards)
- Business logic (matching, contracts)
- Payments (Stripe Connect, payouts)

**FastAPI** handles:
- AI/ML processing (MCPs, models)
- Heavy compute (vLLM, GPU)
- Data pipeline (lakehouse)

**Communication**:
- Next.js → FastAPI: REST API with API key auth
- FastAPI → Next.js: Webhooks with signature verification
- Shared: PostgreSQL database (optional - can be separate)

**This architecture gives you**:
- Best DX (TypeScript + Python)
- Independent scaling
- Technology optimization
- Team specialization

Ready to code! 🚀
