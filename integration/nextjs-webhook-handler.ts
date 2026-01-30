/**
 * Next.js Webhook Handler for FastAPI Events
 *
 * File: nextjs-app/src/app/api/webhooks/mcp/route.ts
 *
 * Receives events from FastAPI MCP Platform and updates Next.js database
 */

import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { prisma } from '@/lib/prisma';
import { pusher } from '@/lib/pusher'; // For real-time updates
import { sendEmail } from '@/lib/email';

// ============================================================================
// WEBHOOK SIGNATURE VERIFICATION
// ============================================================================

function verifyWebhookSignature(request: NextRequest): boolean {
  const headersList = headers();
  const signature = headersList.get('X-Webhook-Secret');
  const webhookSecret = process.env.WEBHOOK_SECRET;

  if (!webhookSecret) {
    console.error('WEBHOOK_SECRET not configured');
    return false;
  }

  return signature === webhookSecret;
}

// ============================================================================
// IDEMPOTENCY CHECK
// ============================================================================

const processedWebhooks = new Set<string>();
const CACHE_TTL = 3600000; // 1 hour

function checkIdempotency(key: string): boolean {
  if (processedWebhooks.has(key)) {
    return false; // Already processed
  }

  processedWebhooks.add(key);

  // Clean up old entries after TTL
  setTimeout(() => {
    processedWebhooks.delete(key);
  }, CACHE_TTL);

  return true;
}

// ============================================================================
// WEBHOOK HANDLER
// ============================================================================

export async function POST(request: NextRequest) {
  // 1. Verify signature
  if (!verifyWebhookSignature(request)) {
    console.error('Webhook signature verification failed');
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // 2. Parse payload
  const payload = await request.json();
  const { event, data, timestamp } = payload;

  // 3. Check idempotency
  const idempotencyKey = request.headers.get('X-Idempotency-Key');
  if (idempotencyKey && !checkIdempotency(idempotencyKey)) {
    console.log(`Duplicate webhook ignored: ${event}`);
    return NextResponse.json({ received: true, duplicate: true });
  }

  console.log(`Webhook received: ${event}`, data);

  // 4. Handle event
  try {
    switch (event) {
      case 'task.created':
        await handleTaskCreated(data);
        break;

      case 'task.started':
        await handleTaskStarted(data);
        break;

      case 'task.completed':
        await handleTaskCompleted(data);
        break;

      case 'task.needs_review':
        await handleTaskNeedsReview(data);
        break;

      case 'task.failed':
        await handleTaskFailed(data);
        break;

      case 'mcp.installed':
        await handleMCPInstalled(data);
        break;

      case 'mcp.uninstalled':
        await handleMCPUninstalled(data);
        break;

      case 'model.loaded':
        await handleModelLoaded(data);
        break;

      case 'model.evicted':
        await handleModelEvicted(data);
        break;

      default:
        console.warn(`Unknown webhook event: ${event}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error(`Webhook handler error for ${event}:`, error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

async function handleTaskCreated(data: any) {
  console.log('Task created:', data.task_id);

  // Update task in Next.js DB (if it exists)
  const existingTask = await prisma.task.findUnique({
    where: { id: data.task_id },
  });

  if (existingTask) {
    await prisma.task.update({
      where: { id: data.task_id },
      data: {
        status: 'IN_PROGRESS',
        mcpUsed: data.mcp_id,
      },
    });
  }

  // Send real-time update to expert
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'task-created',
    {
      taskId: data.task_id,
      title: data.title,
      mcp: data.mcp_id,
    }
  );
}

async function handleTaskStarted(data: any) {
  await prisma.task.updateMany({
    where: { id: data.task_id },
    data: {
      status: 'IN_PROGRESS',
      startedAt: new Date(data.started_at),
    },
  });

  // Real-time update
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'task-started',
    { taskId: data.task_id }
  );
}

async function handleTaskCompleted(data: any) {
  // Update task in Next.js DB
  await prisma.task.updateMany({
    where: { id: data.task_id },
    data: {
      status: data.requires_review ? 'IN_REVIEW' : 'COMPLETED',
      aiAutomated:
        data.ai_handled === 'full'
          ? 100
          : data.ai_handled === 'partial'
          ? 50
          : 0,
      aiConfidence: data.ai_confidence,
      mcpUsed: data.ai_model_used,
      result: data.output_data,
      completedAt: data.completed_at ? new Date(data.completed_at) : null,
    },
  });

  // Update engagement stats
  const task = await prisma.task.findUnique({
    where: { id: data.task_id },
    include: { engagement: true },
  });

  if (task && !data.requires_review) {
    await prisma.engagement.update({
      where: { id: task.engagementId },
      data: {
        tasksCompleted: { increment: 1 },
        aiAutomationRate: data.ai_confidence,
      },
    });
  }

  // Send real-time update
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'task-completed',
    {
      taskId: data.task_id,
      confidence: data.ai_confidence,
      needsReview: data.requires_review,
    }
  );

  // Send email if needs review
  if (data.requires_review) {
    const engagement = await prisma.engagement.findUnique({
      where: { id: data.engagement_id },
      include: {
        expert: { include: { user: true } },
      },
    });

    if (engagement?.expert.user.email) {
      await sendEmail({
        to: engagement.expert.user.email,
        subject: 'Task Needs Your Review',
        template: 'task-review-needed',
        data: {
          expertName: engagement.expert.user.name,
          taskTitle: data.title,
          aiConfidence: data.ai_confidence,
          taskUrl: `${process.env.NEXT_PUBLIC_APP_URL}/expert/tasks/${data.task_id}`,
        },
      });
    }
  }
}

async function handleTaskNeedsReview(data: any) {
  await prisma.task.updateMany({
    where: { id: data.task_id },
    data: {
      status: 'IN_REVIEW',
      aiConfidence: data.ai_confidence,
      result: data.output_data,
    },
  });

  // Get expert email
  const task = await prisma.task.findUnique({
    where: { id: data.task_id },
    include: {
      expert: { include: { user: true } },
    },
  });

  if (task?.expert.user.email) {
    await sendEmail({
      to: task.expert.user.email,
      subject: '⚠️ Task Needs Your Review',
      template: 'task-review-needed',
      data: {
        expertName: task.expert.user.name,
        taskTitle: data.title,
        aiConfidence: data.ai_confidence,
        reason: data.review_reason,
        taskUrl: `${process.env.NEXT_PUBLIC_APP_URL}/expert/tasks/${data.task_id}`,
      },
    });
  }

  // Real-time notification
  await pusher.trigger(
    `expert-${data.expert_id}`,
    'task-needs-review',
    {
      taskId: data.task_id,
      title: data.title,
      confidence: data.ai_confidence,
    }
  );
}

async function handleTaskFailed(data: any) {
  await prisma.task.updateMany({
    where: { id: data.task_id },
    data: {
      status: 'BLOCKED',
    },
  });

  // Notify expert
  const task = await prisma.task.findUnique({
    where: { id: data.task_id },
    include: { expert: { include: { user: true } } },
  });

  if (task?.expert.user.email) {
    await sendEmail({
      to: task.expert.user.email,
      subject: '❌ Task Processing Failed',
      template: 'task-failed',
      data: {
        taskTitle: data.title || 'Unknown',
        errorMessage: data.error_message,
        retryCount: data.retry_count,
      },
    });
  }
}

async function handleMCPInstalled(data: any) {
  console.log('MCP installed:', data.mcp_id, 'for engagement:', data.engagement_id);

  // Update engagement to include MCP
  const engagement = await prisma.engagement.findUnique({
    where: { id: data.engagement_id },
  });

  if (engagement) {
    const mcpTypes = engagement.mcpTypes || [];
    if (!mcpTypes.includes(data.mcp_id)) {
      await prisma.engagement.update({
        where: { id: data.engagement_id },
        data: {
          mcpTypes: [...mcpTypes, data.mcp_id],
        },
      });
    }
  }

  // Real-time update
  await pusher.trigger(
    `engagement-${data.engagement_id}`,
    'mcp-installed',
    {
      mcpId: data.mcp_id,
      status: data.status,
    }
  );
}

async function handleMCPUninstalled(data: any) {
  console.log('MCP uninstalled:', data.mcp_id);

  // Remove from engagement
  const engagement = await prisma.engagement.findUnique({
    where: { id: data.engagement_id },
  });

  if (engagement) {
    await prisma.engagement.update({
      where: { id: data.engagement_id },
      data: {
        mcpTypes: (engagement.mcpTypes || []).filter((mcp) => mcp !== data.mcp_id),
      },
    });
  }
}

async function handleModelLoaded(data: any) {
  console.log('Model loaded:', data.model_name, `(${data.memory_gb}GB)`);

  // Could store in Redis cache for model status dashboard
  // await redis.set(`model:${data.model_name}`, JSON.stringify(data), 'EX', 300);
}

async function handleModelEvicted(data: any) {
  console.log('Model evicted:', data.model_name, 'reason:', data.reason);
}
