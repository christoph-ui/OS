/**
 * MCP Platform Client for Next.js
 *
 * Type-safe TypeScript wrapper for calling FastAPI MCP Platform
 *
 * Usage:
 *   import { mcpClient } from '@/lib/mcp-client';
 *
 *   const task = await mcpClient.createTask({...});
 *   const mcps = await mcpClient.listMCPs();
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================================================
// TYPES
// ============================================================================

export interface MCPTask {
  id: string;
  engagement_id: string;
  expert_id: string;
  customer_id: string;
  mcp_id: string;
  title: string;
  description?: string;
  task_type: string;
  status: 'todo' | 'in_progress' | 'needs_review' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  ai_handled: 'no' | 'partial' | 'full';
  ai_confidence: number;
  requires_human_review: boolean;
  ai_model_used?: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  artifacts?: Array<Record<string, any>>;
  due_date?: string;
  estimated_duration_minutes?: number;
  actual_duration_minutes?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface CreateTaskRequest {
  engagement_id: string;
  mcp_id: string;
  task_type: string;
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  data: Record<string, any>;
  due_date?: string;
  estimated_duration_minutes?: number;
}

export interface MCP {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  icon?: string;
  color?: string;
  publisher: string;
  version: string;
  tools: string[];
  supported_languages: string[];
  supported_file_types: string[];
  integrations: string[];
  compliance_standards: string[];
  pricing_model: string;
  subscription_monthly_cents: number;
  usage_price_per_unit_cents: number;
  usage_unit: string;
  free_tier_limit: number;
  automation_rate: number;
  accuracy_rate: number;
  min_gpu_memory_gb: number;
  rating: number;
  total_reviews: number;
  active_installations: number;
  status: string;
  is_official: boolean;
}

export interface MCPInstallation {
  id: string;
  engagement_id: string;
  mcp_id: string;
  customer_id: string;
  expert_id: string;
  version: string;
  status: 'pending' | 'installing' | 'active' | 'paused' | 'error' | 'uninstalled';
  config: Record<string, any>;
  enabled_features: string[];
  health_score: number;
  automation_rate: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  cost_this_month_cents: number;
  installed_at?: string;
  activated_at?: string;
  last_used_at?: string;
  created_at: string;
}

export interface ExpertDashboard {
  name: string;
  avatar: string;
  role: string;
  rating: number;
  mcps: string[];
  clients: number;
  maxClients: number;
  monthlyEarnings: number;
  weeklyPayout: number;
  nextPayout: string;
  automationRate: number;
  todaysTasks: number;
  tasksCompleted: number;
  tasksNeedsReview: number;
  clients_data: Array<{
    id: string;
    company: string;
    logo: string;
    mcps: string[];
    rate: number;
    health: number;
    tasks: { done: number; total: number };
    lastActivity: string;
    aiRate: number;
  }>;
}

// ============================================================================
// CLIENT CLASS
// ============================================================================

export class MCPClient {
  private client: AxiosInstance;

  constructor(baseURL: string, apiKey?: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { Authorization: `Bearer ${apiKey}` }),
      },
      timeout: 60000, // 60s for AI processing
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          console.error('MCP API Error:', {
            status: error.response.status,
            data: error.response.data,
          });
        }
        throw error;
      }
    );
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
    customer_id?: string;
    status?: string;
    priority?: string;
    due_date?: 'today' | 'this_week' | 'overdue';
    limit?: number;
    offset?: number;
  }): Promise<{ tasks: MCPTask[]; total: number; status_counts: Record<string, number> }> {
    const response = await this.client.get('/api/tasks', { params });
    return response.data;
  }

  async completeTask(
    taskId: string,
    outputData: Record<string, any>,
    notes?: string
  ): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'complete',
      output_data: outputData,
      notes,
    });
  }

  async reviewTask(
    taskId: string,
    approve: boolean,
    notes?: string
  ): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'review',
      approve,
      notes,
    });
  }

  async startTask(taskId: string): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'start',
    });
  }

  async cancelTask(taskId: string): Promise<void> {
    await this.client.post(`/api/tasks/${taskId}/actions`, {
      action: 'cancel',
    });
  }

  // =========================================================================
  // MCPs
  // =========================================================================

  async listMCPs(params?: {
    category?: string;
    search?: string;
    official_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ mcps: MCP[]; total: number; categories: Array<{ name: string; count: number }> }> {
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
    enabled_features?: string[];
  }): Promise<MCPInstallation> {
    const response = await this.client.post<MCPInstallation>('/api/mcps/install', params);
    return response.data;
  }

  async uninstallMCP(installationId: string, reason?: string): Promise<void> {
    await this.client.delete(`/api/mcps/install/${installationId}`, {
      params: { reason },
    });
  }

  async listInstallations(params?: {
    engagement_id?: string;
    expert_id?: string;
    status?: string;
  }): Promise<MCPInstallation[]> {
    const response = await this.client.get('/api/mcps/installations', { params });
    return response.data;
  }

  async getMCPStats(mcpId: string): Promise<any> {
    const response = await this.client.get(`/api/mcps/${mcpId}/stats`);
    return response.data;
  }

  // =========================================================================
  // EXPERTS (Dashboard)
  // =========================================================================

  async getExpertDashboard(expertId: string): Promise<ExpertDashboard> {
    const response = await this.client.get<ExpertDashboard>('/api/experts/dashboard', {
      params: { expert_id: expertId },
    });
    return response.data;
  }

  async getExpertClients(expertId: string, status?: string): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/clients`, {
      params: { status },
    });
    return response.data;
  }

  async getExpertTasks(
    expertId: string,
    params?: { status?: string; due_date?: string; limit?: number }
  ): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/tasks`, { params });
    return response.data;
  }

  async getExpertEarnings(expertId: string): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/earnings`);
    return response.data;
  }

  async getExpertMCPs(expertId: string): Promise<any> {
    const response = await this.client.get(`/api/experts/${expertId}/mcps`);
    return response.data;
  }

  // =========================================================================
  // ENGAGEMENTS
  // =========================================================================

  async listEngagements(params?: {
    expert_id?: string;
    customer_id?: string;
    status?: string;
  }): Promise<any> {
    const response = await this.client.get('/api/engagements', { params });
    return response.data;
  }

  async getEngagement(engagementId: string): Promise<any> {
    const response = await this.client.get(`/api/engagements/${engagementId}`);
    return response.data;
  }

  async getEngagementStats(engagementId: string): Promise<any> {
    const response = await this.client.get(`/api/engagements/${engagementId}/stats`);
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

  // =========================================================================
  // HEALTH
  // =========================================================================

  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// ============================================================================
// FACTORY & HOOKS
// ============================================================================

/**
 * Create MCP client instance
 */
export function createMCPClient(baseURL?: string, apiKey?: string): MCPClient {
  return new MCPClient(
    baseURL || process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8080',
    apiKey || process.env.FASTAPI_API_KEY
  );
}

/**
 * Singleton instance
 */
export const mcpClient = createMCPClient();

// ============================================================================
// REACT HOOKS (for use in Next.js components)
// ============================================================================

/**
 * Hook to fetch task with auto-refresh
 *
 * Usage:
 *   const { data: task, isLoading } = useMCPTask(taskId);
 */
export function useMCPTask(taskId: string | null) {
  return useQuery({
    queryKey: ['mcp-task', taskId],
    queryFn: () => (taskId ? mcpClient.getTask(taskId) : null),
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Auto-refresh every 5s if in progress
      return data?.status === 'in_progress' ? 5000 : false;
    },
  });
}

/**
 * Hook to create task
 */
export function useCreateMCPTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateTaskRequest) => mcpClient.createTask(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-tasks'] });
    },
  });
}

/**
 * Hook to list tasks
 */
export function useMCPTasks(params: Parameters<typeof mcpClient.listTasks>[0]) {
  return useQuery({
    queryKey: ['mcp-tasks', params],
    queryFn: () => mcpClient.listTasks(params),
  });
}

/**
 * Hook to get expert dashboard from FastAPI
 */
export function useMCPExpertDashboard(expertId: string | null) {
  return useQuery({
    queryKey: ['mcp-expert-dashboard', expertId],
    queryFn: () => (expertId ? mcpClient.getExpertDashboard(expertId) : null),
    enabled: !!expertId,
    refetchInterval: 30000, // Refresh every 30s
  });
}

/**
 * Hook to list MCPs
 */
export function useMCPCatalog(params?: Parameters<typeof mcpClient.listMCPs>[0]) {
  return useQuery({
    queryKey: ['mcp-catalog', params],
    queryFn: () => mcpClient.listMCPs(params),
  });
}

/**
 * Hook to install MCP
 */
export function useInstallMCP() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: Parameters<typeof mcpClient.installMCP>[0]) =>
      mcpClient.installMCP(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-installations'] });
    },
  });
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

export class MCPAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'MCPAPIError';
  }
}

export function isMCPAPIError(error: unknown): error is MCPAPIError {
  return error instanceof MCPAPIError;
}

// ============================================================================
// EXAMPLE USAGE IN NEXT.JS COMPONENTS
// ============================================================================

/**
 * Example: Upload RFP and process with Tender MCP
 *
 * async function handleRFPUpload(file: File, engagementId: string) {
 *   // 1. Upload to S3
 *   const fileUrl = await uploadToS3(file);
 *
 *   // 2. Create task in FastAPI
 *   const task = await mcpClient.createTask({
 *     engagement_id: engagementId,
 *     mcp_id: 'TENDER',
 *     task_type: 'parse_rfp',
 *     title: `Parse RFP: ${file.name}`,
 *     data: {
 *       file_path: fileUrl,
 *       document_type: 'rfp',
 *       language: 'de'
 *     }
 *   });
 *
 *   // 3. Show loading state
 *   toast.loading('AI is parsing your RFP...');
 *
 *   // 4. Poll for completion (or wait for webhook)
 *   const result = await pollTaskCompletion(task.id);
 *
 *   // 5. Show result
 *   if (result.ai_confidence >= 80) {
 *     toast.success('RFP parsed successfully!');
 *   } else {
 *     toast.warning('RFP parsed but needs expert review');
 *   }
 * }
 */

/**
 * Example: Install MCP when engagement starts
 *
 * async function onEngagementAccepted(engagementId: string, mcpIds: string[]) {
 *   for (const mcpId of mcpIds) {
 *     const installation = await mcpClient.installMCP({
 *       engagement_id: engagementId,
 *       mcp_id: mcpId,
 *       config: {}
 *     });
 *
 *     console.log(`Installed ${mcpId}:`, installation.status);
 *   }
 * }
 */

/**
 * Example: Expert reviews AI result
 *
 * async function handleTaskReview(taskId: string, approve: boolean, notes?: string) {
 *   await mcpClient.reviewTask(taskId, approve, notes);
 *
 *   if (approve) {
 *     toast.success('Task approved and completed');
 *   } else {
 *     toast.info('Task sent back for corrections');
 *   }
 * }
 */
