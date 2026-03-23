/**
 * API client for Cadence backend.
 * All requests include credentials for HttpOnly cookie auth.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown,
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(response.status, response.statusText, data);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  return handleResponse<T>(response);
}

// Auth
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export const auth = {
  login: (credentials: LoginCredentials) =>
    request<{ message: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  logout: () =>
    request<{ message: string }>("/auth/logout", {
      method: "POST",
    }),

  me: () => request<User>("/auth/me"),

  refresh: () =>
    request<{ message: string }>("/auth/refresh", {
      method: "POST",
    }),
};

// Projects
export interface Project {
  id: number;
  uu_id: string | null;
  name: string;
  description: string | null;
  status: string;
  owner_id: number;
  owner_email: string;
  participant_count?: number;
  node_count?: number;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  size: number;
}

export interface ProjectCreate {
  name: string;
  code?: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

export const projects = {
  list: () => request<ProjectListResponse>("/admin/projects"),

  get: (id: number) => request<Project>(`/admin/projects/${id}`),

  create: (data: ProjectCreate) =>
    request<Project>("/admin/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ProjectUpdate) =>
    request<Project>(`/admin/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/admin/projects/${id}`, {
      method: "DELETE",
    }),

  activate: (id: number) =>
    request<Project>(`/admin/projects/${id}/activate`, {
      method: "POST",
    }),

  suspend: (id: number) =>
    request<Project>(`/admin/projects/${id}/suspend`, {
      method: "POST",
    }),
};

// Participants
export interface Participant {
  id: number;
  uu_id: string | null;
  project_id: number;
  external_id: string | null;
  status: string;
  channel_type: string;
  language_id: number;
  is_test_participant: boolean;
  enrolled_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ParticipantListResponse {
  items: Participant[];
  total: number;
  page: number;
  size: number;
}

export interface ParticipantCreate {
  project_id: number;
  external_id?: string;
  phone_number?: string;
  fcm_token?: string;
  channel_type?: string;
  language_id?: number;
  is_test_participant?: boolean;
}

export interface ParticipantUpdate {
  status?: string;
  phone_number?: string;
  fcm_token?: string;
  language_id?: number;
}

export interface ParticipantVariable {
  id: number;
  variable_id: number;
  variable_name: string;
  variable_display_name: string | null;
  variable_type: string;
  value: string | null;
}

export interface ParticipantMessage {
  id: number;
  node_id: number | null;
  template_id: number | null;
  status: string;
  message_body: string | null;
  scheduled_at: string;
  sent_at: string | null;
  direction: string;
}

export const participants = {
  list: (projectId: number, page = 1, size = 50, status?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (status) params.set("status_filter", status);
    return request<ParticipantListResponse>(
      `/admin/participants/project/${projectId}?${params}`,
    );
  },

  get: (id: number) => request<Participant>(`/admin/participants/${id}`),

  create: (data: ParticipantCreate) =>
    request<Participant>("/admin/participants", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ParticipantUpdate) =>
    request<Participant>(`/admin/participants/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getVariables: (id: number) =>
    request<ParticipantVariable[]>(`/admin/participants/${id}/variables`),

  updateVariable: (
    participantId: number,
    variableId: number,
    value: string | null,
  ) =>
    request<ParticipantVariable>(
      `/admin/participants/${participantId}/variables/${variableId}`,
      {
        method: "PUT",
        body: JSON.stringify({ value }),
      },
    ),

  getMessages: (id: number, limit = 100) =>
    request<ParticipantMessage[]>(
      `/admin/participants/${id}/messages?limit=${limit}`,
    ),
};

// Templates
export interface TemplateText {
  id: number;
  language_id: number;
  message_text: string | null;
  media_url: string | null;
  media_type: string | null;
  quick_replies: Record<string, unknown>[];
}

export interface Template {
  id: number;
  project_id: number;
  name: string;
  description: string | null;
  type: string;
  texts: TemplateText[];
}

export interface TemplateCreate {
  project_id: number;
  name: string;
  description?: string;
  type?: string;
  texts?: {
    language_id: number;
    message_text: string;
    media_url?: string;
    media_type?: string;
    quick_replies?: Record<string, unknown>[];
  }[];
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  type?: string;
  texts?: {
    language_id: number;
    message_text: string;
    media_url?: string;
    media_type?: string;
    quick_replies?: Record<string, unknown>[];
  }[];
}

export const templates = {
  list: (projectId: number) =>
    request<Template[]>(`/admin/templates/project/${projectId}`),

  get: (id: number) => request<Template>(`/admin/templates/${id}`),

  create: (data: TemplateCreate) =>
    request<Template>("/admin/templates", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: TemplateUpdate) =>
    request<Template>(`/admin/templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/admin/templates/${id}`, {
      method: "DELETE",
    }),
};

// Nodes
export interface Node {
  id: number;
  project_id: number;
  name: string;
  display_name: string | null;
  description: string | null;
  is_terminal_node: boolean;
  is_entry_node: boolean;
  template_id: number | null;
  timing_element_id: number | null;
  conditional_expression_id: number | null;
  node_order: number;
  outgoing_edge_count?: number;
  incoming_edge_count?: number;
}

export interface Edge {
  id: number;
  parent_node_id: number;
  child_node_id: number;
  edge_label: string | null;
  edge_order: number;
}

export interface GraphResponse {
  nodes: Node[];
  edges: Edge[];
}

export interface NodeCreate {
  project_id: number;
  name: string;
  display_name?: string;
  description?: string;
  is_terminal_node?: boolean;
  is_entry_node?: boolean;
  template_id?: number;
  timing_element_id?: number;
  conditional_expression_id?: number;
  node_order?: number;
}

export interface NodeUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  is_terminal_node?: boolean;
  is_entry_node?: boolean;
  template_id?: number;
  timing_element_id?: number;
  node_order?: number;
}

export interface EdgeCreate {
  parent_node_id: number;
  child_node_id: number;
  edge_label?: string;
  edge_order?: number;
}

export const nodes = {
  list: (projectId: number) =>
    request<Node[]>(`/admin/nodes/project/${projectId}`),

  get: (id: number) => request<Node>(`/admin/nodes/${id}`),

  create: (data: NodeCreate) =>
    request<Node>("/admin/nodes", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: NodeUpdate) =>
    request<Node>(`/admin/nodes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/admin/nodes/${id}`, {
      method: "DELETE",
    }),

  getGraph: (projectId: number) =>
    request<GraphResponse>(`/admin/nodes/project/${projectId}/graph`),

  createEdge: (data: EdgeCreate) =>
    request<Edge>("/admin/nodes/edges", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteEdge: (id: number) =>
    request<void>(`/admin/nodes/edges/${id}`, {
      method: "DELETE",
    }),

  validateGraph: (projectId: number) =>
    request<GraphValidationResult>(
      `/admin/nodes/project/${projectId}/validate`,
    ),
};

// Graph Validation
export interface GraphValidationIssue {
  severity: "error" | "warning";
  message: string;
  node_id: number | null;
}

export interface GraphValidationResult {
  valid: boolean;
  issues: GraphValidationIssue[];
  node_count: number;
  edge_count: number;
  entry_nodes: number;
  terminal_nodes: number;
}

// Variables
export interface Variable {
  id: number;
  project_id: number;
  name: string;
  display_name: string | null;
  description: string | null;
  type: string;
  source_type: string;
  default_value: string | null;
}

export interface VariableCreate {
  project_id: number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  source_type?: string;
  default_value?: string;
}

export interface VariableUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  type?: string;
  default_value?: string;
}

export const variables = {
  list: (projectId: number) =>
    request<Variable[]>(`/admin/variables/project/${projectId}`),

  get: (id: number) => request<Variable>(`/admin/variables/${id}`),

  create: (data: VariableCreate) =>
    request<Variable>("/admin/variables", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: VariableUpdate) =>
    request<Variable>(`/admin/variables/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/admin/variables/${id}`, {
      method: "DELETE",
    }),
};

// Analytics
export interface OverviewStats {
  total_participants: number;
  active_participants: number;
  completed_participants: number;
  total_messages_sent: number;
  messages_pending: number;
  messages_failed: number;
  delivery_rate: number;
}

export interface DeliveryStats {
  total_sent: number;
  total_pending: number;
  total_failed: number;
  total_aborted: number;
  sent_today: number;
  sent_this_week: number;
}

export const analytics = {
  overview: (projectId: number) =>
    request<OverviewStats>(`/admin/analytics/project/${projectId}/overview`),

  delivery: (projectId: number) =>
    request<DeliveryStats>(`/admin/analytics/project/${projectId}/delivery`),
};

// Scheduler
export interface QueueHealth {
  pending_count: number;
  in_progress_count: number;
  failed_count: number;
  sent_today: number;
  oldest_pending_minutes: number | null;
}

export interface ScheduledMessage {
  id: number;
  participant_id: number;
  node_id: number;
  status: string;
  scheduled_at: string;
  sent_at: string | null;
  attempt_count: number;
  error_message: string | null;
}

export const scheduler = {
  health: () => request<QueueHealth>("/scheduler/health"),

  pending: (projectId?: number, limit = 100) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (projectId) params.set("project_id", projectId.toString());
    return request<ScheduledMessage[]>(`/scheduler/messages/pending?${params}`);
  },

  failed: (projectId?: number, limit = 100) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (projectId) params.set("project_id", projectId.toString());
    return request<ScheduledMessage[]>(`/scheduler/messages/failed?${params}`);
  },

  requeue: (maxAgeHours = 24) =>
    request<{ requeued_count: number; message: string }>(
      `/scheduler/requeue?max_age_hours=${maxAgeHours}`,
      { method: "POST" },
    ),

  abortParticipant: (participantId: number) =>
    request<{ aborted_count: number; message: string }>(
      `/scheduler/abort/participant/${participantId}`,
      { method: "POST" },
    ),

  abortProject: (projectId: number) =>
    request<{ aborted_count: number; message: string }>(
      `/scheduler/abort/project/${projectId}`,
      { method: "POST" },
    ),
};

// Testing
export interface TestResult {
  file: string;
  name: string;
  status: "passed" | "failed" | "error" | "skipped";
  full_name: string;
}

export interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  errors: number;
  skipped: number;
  pass_rate: number;
}

export interface TestRunResponse {
  timestamp: string;
  summary: TestSummary;
  tests: TestResult[];
  exit_code: number;
  raw_output: string;
}

export interface TestHealthResponse {
  status: string;
  tests_directory: string;
  test_files_count: number;
  test_files: string[];
}

export const testing = {
  run: () =>
    request<TestRunResponse>("/admin/testing/run", {
      method: "POST",
    }),

  health: () => request<TestHealthResponse>("/admin/testing/health"),
};

// Protocol Testing
export interface FlowStep {
  step: number;
  node_id: number;
  node_name: string;
  display_name: string | null;
  message_text: string | null;
  scheduled_time: string;
  delay_minutes: number | null;
  is_entry: boolean;
  is_terminal: boolean;
  edges: {
    to_node_id: number;
    to_node_name: string;
    label: string | null;
  }[];
}

export interface ProtocolOverview {
  project_id: number;
  project_name: string;
  total_nodes: number;
  total_edges: number;
  total_templates: number;
  total_variables: number;
  entry_nodes: { id: number; name: string }[];
  terminal_nodes: { id: number; name: string }[];
  nodes: {
    id: number;
    name: string;
    display_name: string | null;
    is_entry: boolean;
    is_terminal: boolean;
    template_id: number | null;
    timing_element_id: number | null;
  }[];
  edges: {
    id: number;
    from_node: number;
    to_node: number;
    label: string | null;
  }[];
}

export interface ProtocolTestResult {
  project_id: number;
  project_name: string;
  test_started_at: string;
  total_nodes_in_flow: number;
  total_nodes_in_project: number;
  estimated_duration_days: number;
  language_id: number;
  flow_steps: FlowStep[];
  variables: {
    id: number;
    name: string;
    display_name: string | null;
    type: string;
    default_value: string | null;
  }[];
}

export interface TestParticipantResult {
  message: string;
  participant_id: number;
  participant_uuid: string;
  external_id: string;
  first_message_scheduled_at: string;
  entry_node: string;
}

export const protocolTest = {
  overview: (projectId: number) =>
    request<ProtocolOverview>(`/admin/protocol-test/${projectId}/overview`),

  run: (
    projectId: number,
    data?: {
      participant_name?: string;
      language_id?: number;
      variables?: Record<string, string>;
    },
  ) =>
    request<ProtocolTestResult>(`/admin/protocol-test/${projectId}/run`, {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),

  createTestParticipant: (
    projectId: number,
    data?: { participant_name?: string; language_id?: number },
  ) =>
    request<TestParticipantResult>(
      `/admin/protocol-test/${projectId}/create-test-participant`,
      {
        method: "POST",
        body: JSON.stringify(data || {}),
      },
    ),
};

// Interactive Protocol Simulator
export interface QuickReply {
  label: string;
  value: string;
}

export interface SimulatorEdge {
  to_node_id: number;
  to_node_name: string;
  to_display_name: string | null;
  label: string | null;
}

export interface SimulatorMessage {
  node_id: number;
  node_name: string;
  display_name: string | null;
  message_text: string | null;
  media_url: string | null;
  scheduled_time: string;
  delay_description: string | null;
  is_entry: boolean;
  is_terminal: boolean;
  quick_replies: QuickReply[];
  available_edges: SimulatorEdge[];
  expects_reply: boolean;
}

export interface SimulatorStartResponse {
  project_id: number;
  project_name: string;
  simulation_started_at: string;
  language_id: number;
  message: SimulatorMessage;
}

export interface SimulatorReplyResponse {
  project_id: number;
  reply_received: string;
  reply_received_at: string;
  matched_edge_label: string | null;
  message: SimulatorMessage | null;
  end_reason?: string;
}

export const simulator = {
  start: (
    projectId: number,
    data?: { language_id?: number; start_time?: string },
  ) =>
    request<SimulatorStartResponse>(
      `/admin/protocol-test/${projectId}/simulate/start`,
      {
        method: "POST",
        body: JSON.stringify(data || {}),
      },
    ),

  reply: (
    projectId: number,
    data: {
      current_node_id: number;
      reply_value: string;
      current_time: string;
      language_id?: number;
    },
  ) =>
    request<SimulatorReplyResponse>(
      `/admin/protocol-test/${projectId}/simulate/reply`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    ),

  advance: (
    projectId: number,
    data: {
      current_node_id: number;
      current_time: string;
      language_id?: number;
    },
  ) =>
    request<SimulatorReplyResponse>(
      `/admin/protocol-test/${projectId}/simulate/advance`,
      {
        method: "POST",
        body: JSON.stringify({ ...data, reply_value: "" }),
      },
    ),
};

// Protocol Import/Export
export interface ImportResult {
  variables_created: number;
  timing_elements_created: number;
  templates_created: number;
  conditions_created: number;
  nodes_created: number;
  edges_created: number;
  keywords_created: number;
}

export const protocolData = {
  export: (projectId: number) =>
    request<Record<string, unknown>>(
      `/admin/protocol/projects/${projectId}/export`,
    ),

  import: (projectId: number, protocol: Record<string, unknown>) =>
    request<ImportResult>(`/admin/protocol/projects/${projectId}/import`, {
      method: "POST",
      body: JSON.stringify(protocol),
    }),
};

// User Management (admin only)
export interface UserListItem {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

export const users = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    request<UserListItem>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ── Delivery Management ──────────────────────────────────────────────

export interface QueueStats {
  pending: number;
  in_progress: number;
  sent: number;
  failed: number;
  skipped: number;
  aborted: number;
  total: number;
}

export interface MessageSummary {
  id: number;
  participant_id: number;
  participant_uuid: string | null;
  project_id: number;
  messaging_node_id: number | null;
  template_id: number | null;
  status: string;
  channel_type: string;
  message_body: string | null;
  send_at: string;
  sent_at: string | null;
  attempt_count: number;
  last_error_message: string | null;
  external_id: string | null;
  created_at: string | null;
}

export interface MessageListResponse {
  messages: MessageSummary[];
  total: number;
  page: number;
  limit: number;
}

export interface TestSendResponse {
  success: boolean;
  channel: string;
  external_id: string | null;
  error: string | null;
}

export interface ChannelStatus {
  twilio_configured: boolean;
  twilio_phone_number: string;
  fcm_configured: boolean;
  simulation_mode: boolean;
}

export const delivery = {
  getStats: (projectId: number) =>
    request<QueueStats>(`/admin/delivery/project/${projectId}/stats`),

  listMessages: (
    projectId: number,
    params?: {
      status?: string;
      channel?: string;
      participant_id?: number;
      page?: number;
      limit?: number;
    },
  ) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.channel) qs.set("channel", params.channel);
    if (params?.participant_id)
      qs.set("participant_id", String(params.participant_id));
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<MessageListResponse>(
      `/admin/delivery/project/${projectId}/messages${suffix}`,
    );
  },

  testSend: (data: {
    participant_id: number;
    message_text: string;
    channel_override?: string;
  }) =>
    request<TestSendResponse>("/admin/delivery/test-send", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  channelStatus: () => request<ChannelStatus>("/admin/delivery/channel-status"),

  retryFailed: (projectId: number) =>
    request<{ retried_count: number }>(
      `/admin/delivery/project/${projectId}/retry-failed`,
      { method: "POST" },
    ),
};
