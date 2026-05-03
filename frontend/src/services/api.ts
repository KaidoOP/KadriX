/**
 * KadriX API Client
 * TypeScript client for campaign generation and improvement
 */
import axios, { AxiosError } from 'axios';

// ============================================================================
// Request Interfaces
// ============================================================================

export interface CampaignGenerateRequest {
  product_idea: string;
  description: string;
  campaign_goal: string;
  target_audience: string;
  tone: string;
  video_context?: string;
  tts_voice?: string;
}

export interface CampaignImproveRequest {
  campaign_id: string;
  original_campaign: CampaignData;
  feedback: string;
}

export interface RenderPreviewVideoRequest {
  campaign_id: string;
  main_hook: string;
  voiceover_script: string;
  video_concept: string;
  storyboard_scenes: StoryboardScene[];
  mood_direction: string;
  music_direction: string;
  visual_style: string;
  call_to_action: string;
  source_video_url?: string;
  source_video_path?: string;
  source_file_id?: string;
  require_source_video?: boolean;
  tts_voice?: string;
}

// ============================================================================
// Response Interfaces
// ============================================================================

export interface AdCopyVariant {
  platform: string;
  headline: string;
  body: string;
  character_count: number;
}

export interface StoryboardScene {
  timestamp: string;
  scene_title: string;
  visual_direction: string;
  narration: string;
}

export interface CampaignData {
  campaign_id: string;
  version: number;
  generated_at: string;
  product_summary: string;
  target_audience: string;
  campaign_angle: string;
  value_proposition: string;
  marketing_hooks: string[];
  ad_copy_variants: AdCopyVariant[];
  call_to_action: string;
  video_script: string;
  main_hook: string;
  voiceover_script: string;
  video_concept: string;
  storyboard_scenes: StoryboardScene[];
  mood_direction: string;
  music_direction: string;
  visual_style: string;
  one_minute_video_plan: string;
  generation_source?: string;
  model_id?: string | null;
}

export interface CampaignGenerateResponse extends CampaignData {}

export interface CampaignImproveResponse {
  campaign_id: string;
  version: number;
  generated_at: string;
  original: CampaignData;
  improved: CampaignData;
  changes: string[];
}

export interface MediaUploadResponse {
  file_id: string;
  filename: string;
  file_url: string;
  internal_file_path: string;
  size_bytes: number;
  format: string;
  transcript: string;
  product_context: string;
}

export interface RenderPreviewVideoResponse {
  campaign_id: string;
  video_url: string;
  filename: string;
  duration_seconds: number;
  status: string;
  used_source_video: boolean;
  render_mode: string;  // "source_video" or "fallback_slides"
  voiceover_enabled: boolean;
  audio_filename: string | null;
}

// ============================================================================
// Error Handling
// ============================================================================

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}

function handleApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    return {
      message: axiosError.response?.data?.detail || axiosError.message || 'An error occurred',
      status: axiosError.response?.status,
      detail: axiosError.response?.data?.detail,
    };
  }
  return {
    message: error instanceof Error ? error.message : 'An unknown error occurred',
  };
}

// ============================================================================
// API Client
// ============================================================================

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Generate a new marketing campaign
 * @param payload Campaign generation request
 * @returns Generated campaign data
 */
export async function generateCampaign(
  payload: CampaignGenerateRequest
): Promise<CampaignGenerateResponse> {
  try {
    const response = await apiClient.post<CampaignGenerateResponse>(
      '/campaigns/generate',
      payload
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * Improve an existing campaign based on feedback
 * @param payload Campaign improvement request
 * @returns Improved campaign data with changes
 */
export async function improveCampaign(
  payload: CampaignImproveRequest
): Promise<CampaignImproveResponse> {
  try {
    const response = await apiClient.post<CampaignImproveResponse>(
      '/campaigns/improve',
      payload
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * Upload an optional product demo video and receive extracted MVP context.
 * @param file Video file selected by the user
 * @returns Mock transcript and product context from the media service
 */
export async function uploadMedia(file: File): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post<MediaUploadResponse>('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 180000,
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * Render a blueprint-based preview video from the current campaign.
 * @param payload Video blueprint payload
 * @returns Generated preview video metadata and asset URL
 */
export async function renderPreviewVideo(
  payload: RenderPreviewVideoRequest
): Promise<RenderPreviewVideoResponse> {
  try {
    const response = await apiClient.post<RenderPreviewVideoResponse>(
      '/creative/render-preview-video',
      payload,
      {
        timeout: 120000,
      }
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * Health check for API availability
 * @returns Health status
 */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
}

// Made with Bob
