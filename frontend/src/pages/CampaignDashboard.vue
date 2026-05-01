<template>
  <q-page class="campaign-dashboard">
    <div class="dashboard-container">
      <!-- Header Section -->
      <div class="dashboard-header">
        <div class="header-content">
          <p class="eyebrow">IBM Bob Dev Day Hackathon</p>
          <h1>Campaign Workflow Dashboard</h1>
          <p class="tagline">
            Transform product ideas into launch-ready marketing campaigns with AI-powered insights
          </p>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="dashboard-grid">
        <!-- Product Input Panel -->
        <q-card class="input-panel" flat bordered>
          <q-card-section class="panel-header">
            <div class="text-h6">Product Input</div>
            <p class="text-caption text-grey-7">
              Provide your product details to generate a marketing campaign
            </p>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <q-form @submit="handleGenerateCampaign" class="input-form">
              <q-input
                v-model="formData.product_idea"
                label="Product Idea *"
                placeholder="e.g., Smart Home Energy Monitor"
                outlined
                dense
                :rules="[val => !!val || 'Product idea is required']"
                class="q-mb-md"
              />

              <q-input
                v-model="formData.description"
                label="Description *"
                placeholder="Describe your product's key features and benefits"
                outlined
                dense
                type="textarea"
                rows="3"
                :rules="[
                  val => !!val || 'Description is required',
                  val => val.length >= 20 || 'Description must be at least 20 characters'
                ]"
                class="q-mb-md"
              />

              <q-input
                v-model="formData.campaign_goal"
                label="Campaign Goal *"
                placeholder="e.g., Increase brand awareness, Drive sales"
                outlined
                dense
                :rules="[val => !!val || 'Campaign goal is required']"
                class="q-mb-md"
              />

              <q-input
                v-model="formData.target_audience"
                label="Target Audience *"
                placeholder="e.g., Tech-savvy homeowners aged 30-50"
                outlined
                dense
                :rules="[val => !!val || 'Target audience is required']"
                class="q-mb-md"
              />

              <q-select
                v-model="formData.tone"
                label="Tone *"
                :options="toneOptions"
                outlined
                dense
                :rules="[val => !!val || 'Tone is required']"
                class="q-mb-md"
              />

              <div class="demo-video-section q-mb-md">
                <div class="demo-video-section__header">
                  <div>
                    <div class="section-title">Optional Demo Video</div>
                    <p class="section-description">
                      Upload a short product walkthrough or app demo.
                    </p>
                  </div>
                  <q-chip
                    v-if="mediaUploadResult"
                    color="positive"
                    text-color="white"
                    icon="check_circle"
                    size="sm"
                  >
                    Context added
                  </q-chip>
                </div>

                <q-banner class="demo-video-banner" rounded>
                  <template v-slot:avatar>
                    <q-icon name="movie" color="primary" />
                  </template>
                  KadriX will use the extracted context to improve the campaign direction.
                  Recommended max file size: 100MB.
                </q-banner>

                <q-file
                  v-model="selectedVideoFile"
                  label="Select video file"
                  accept="video/*"
                  outlined
                  dense
                  clearable
                  class="q-mt-md"
                  :disable="isUploadingMedia"
                  @update:model-value="handleVideoFileSelected"
                >
                  <template v-slot:prepend>
                    <q-icon name="attach_file" />
                  </template>
                </q-file>

                <div v-if="selectedVideoFile" class="selected-file-row">
                  <q-chip icon="movie" color="grey-3" text-color="dark">
                    {{ selectedVideoFile.name }}
                  </q-chip>
                  <span class="selected-file-size">
                    {{ formatFileSize(selectedVideoFile.size) }}
                  </span>
                </div>

                <q-linear-progress
                  v-if="isUploadingMedia"
                  indeterminate
                  color="primary"
                  class="q-mt-md"
                />

                <div class="demo-video-actions">
                  <q-btn
                    label="Analyze Demo Video"
                    color="primary"
                    outline
                    icon="analytics"
                    :loading="isUploadingMedia"
                    :disable="isGenerating || isUploadingMedia"
                    @click="handleUploadMedia"
                  />
                </div>

                <q-card
                  v-if="mediaUploadResult"
                  flat
                  bordered
                  class="media-preview-card"
                >
                  <q-card-section>
                    <div class="media-preview-card__meta">
                      <q-chip color="positive" text-color="white" icon="task_alt" size="sm">
                        Analyzed
                      </q-chip>
                      <span>{{ mediaUploadResult.filename }}</span>
                      <span>{{ formatFileSize(mediaUploadResult.size_bytes) }}</span>
                      <span>{{ mediaUploadResult.format }}</span>
                    </div>

                    <div class="media-preview-card__content">
                      <div class="preview-label">
                        {{ mediaPreviewLabel }}
                      </div>
                      <p>{{ mediaPreviewText }}</p>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <q-input
                v-model="formData.video_context"
                label="Video Context (Optional)"
                placeholder="Add extracted demo context or describe relevant product visuals"
                outlined
                dense
                type="textarea"
                rows="3"
                class="q-mb-md"
              />

              <div class="form-actions">
                <q-btn
                  label="Load Demo Data"
                  color="grey-7"
                  outline
                  @click="loadDemoData"
                  :disable="isGenerating"
                  class="q-mr-sm"
                />
                <q-btn
                  type="submit"
                  label="Generate Campaign"
                  color="primary"
                  :loading="isGenerating"
                  :disable="isGenerating"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Campaign Workspace -->
        <q-card class="workspace-panel" flat bordered>
          <q-card-section class="panel-header">
            <div class="workspace-title">
              <div class="text-h6">Campaign Workspace</div>
              <q-badge
                v-if="currentCampaign"
                :label="`Version ${currentCampaign.version}`"
                color="primary"
              />
            </div>
            <p class="text-caption text-grey-7">
              Your generated marketing campaign content
            </p>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <!-- Empty State -->
            <div v-if="!currentCampaign && !isGenerating" class="empty-state">
              <q-icon name="campaign" size="64px" color="grey-5" />
              <p class="text-h6 q-mt-md">No Campaign Yet</p>
              <p class="text-body2 text-grey-7">
                Fill out the product input form and click "Generate Campaign" to get started
              </p>
            </div>

            <!-- Loading State -->
            <div v-if="isGenerating" class="loading-state">
              <q-spinner-dots size="64px" color="primary" />
              <p class="text-h6 q-mt-md">Generating Campaign...</p>
              <p class="text-body2 text-grey-7">
                AI is crafting your marketing strategy
              </p>
            </div>

            <!-- Campaign Content -->
            <div v-if="currentCampaign && !isGenerating" class="campaign-content">
              <!-- Product Summary -->
              <div class="content-section">
                <div class="section-label">Product Summary</div>
                <p class="section-text">{{ currentCampaign.product_summary }}</p>
              </div>

              <!-- Target Audience -->
              <div class="content-section">
                <div class="section-label">Target Audience</div>
                <p class="section-text">{{ currentCampaign.target_audience }}</p>
              </div>

              <!-- Campaign Angle -->
              <div class="content-section">
                <div class="section-label">Campaign Angle</div>
                <p class="section-text">{{ currentCampaign.campaign_angle }}</p>
              </div>

              <!-- Value Proposition -->
              <div class="content-section">
                <div class="section-label">Value Proposition</div>
                <p class="section-text highlight">{{ currentCampaign.value_proposition }}</p>
              </div>

              <!-- Marketing Hooks -->
              <div class="content-section">
                <div class="section-label">Marketing Hooks</div>
                <q-list bordered separator class="hooks-list">
                  <q-item v-for="(hook, index) in currentCampaign.marketing_hooks" :key="index">
                    <q-item-section avatar>
                      <q-icon name="check_circle" color="positive" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>{{ hook }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </div>

              <!-- Ad Copy Variants -->
              <div class="content-section">
                <div class="section-label">Ad Copy Variants</div>
                <div class="ad-variants">
                  <q-card
                    v-for="(variant, index) in currentCampaign.ad_copy_variants"
                    :key="index"
                    flat
                    bordered
                    class="ad-variant-card"
                  >
                    <q-card-section>
                      <div class="platform-badge">
                        <q-badge :label="variant.platform" color="accent" />
                        <span class="char-count">{{ variant.character_count }} chars</span>
                      </div>
                      <div class="ad-headline">{{ variant.headline }}</div>
                      <div class="ad-body">{{ variant.body }}</div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>

              <!-- Call to Action -->
              <div class="content-section">
                <div class="section-label">Call to Action</div>
                <q-banner class="cta-banner" rounded>
                  <template v-slot:avatar>
                    <q-icon name="campaign" color="primary" />
                  </template>
                  {{ currentCampaign.call_to_action }}
                </q-banner>
              </div>

              <!-- Video Script -->
              <div class="content-section">
                <div class="section-label">Video Script</div>
                <q-card flat bordered class="script-card">
                  <q-card-section>
                    <pre class="video-script">{{ currentCampaign.video_script }}</pre>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Feedback Panel (only shown after v1 exists) -->
        <q-card
          v-if="currentCampaign && currentCampaign.version === 1"
          class="feedback-panel"
          flat
          bordered
        >
          <q-card-section class="panel-header">
            <div class="text-h6">Feedback & Improve</div>
            <p class="text-caption text-grey-7">
              Provide feedback to refine your campaign
            </p>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <q-form @submit="handleImproveCampaign">
              <q-input
                v-model="feedbackText"
                label="Your Feedback"
                placeholder="e.g., Make it more professional, target younger audience, add more urgency..."
                outlined
                dense
                type="textarea"
                rows="4"
                :rules="[
                  val => !!val || 'Feedback is required',
                  val => val.length >= 10 || 'Please provide more detailed feedback'
                ]"
                class="q-mb-md"
              />

              <div class="feedback-suggestions">
                <p class="text-caption text-grey-7 q-mb-sm">Quick suggestions:</p>
                <div class="suggestion-chips">
                  <q-chip
                    v-for="suggestion in feedbackSuggestions"
                    :key="suggestion"
                    clickable
                    @click="feedbackText = suggestion"
                    color="grey-3"
                    text-color="dark"
                    size="sm"
                  >
                    {{ suggestion }}
                  </q-chip>
                </div>
              </div>

              <q-btn
                type="submit"
                label="Improve Campaign"
                color="primary"
                :loading="isImproving"
                :disable="isImproving"
                class="q-mt-md"
              />
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Version Comparison (shown after improvement) -->
        <q-card
          v-if="improvedCampaign"
          class="comparison-panel"
          flat
          bordered
        >
          <q-card-section class="panel-header">
            <div class="text-h6">Version Comparison</div>
            <p class="text-caption text-grey-7">
              See what changed in your improved campaign
            </p>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <!-- Changes Summary -->
            <div class="changes-summary q-mb-lg">
              <div class="section-label">Applied Changes</div>
              <q-list bordered separator>
                <q-item v-for="(change, index) in improvedCampaign.changes" :key="index">
                  <q-item-section avatar>
                    <q-icon name="auto_fix_high" color="accent" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ change }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <!-- Side-by-side Comparison -->
            <div class="comparison-grid">
              <!-- Version 1 -->
              <div class="version-column">
                <div class="version-header">
                  <q-badge label="Version 1" color="grey-7" />
                </div>
                <div class="comparison-content">
                  <div class="comparison-item">
                    <div class="item-label">Value Proposition</div>
                    <p class="item-text">{{ improvedCampaign.original.value_proposition }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Campaign Angle</div>
                    <p class="item-text">{{ improvedCampaign.original.campaign_angle }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Target Audience</div>
                    <p class="item-text">{{ improvedCampaign.original.target_audience }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Call to Action</div>
                    <p class="item-text">{{ improvedCampaign.original.call_to_action }}</p>
                  </div>
                </div>
              </div>

              <!-- Version 2 -->
              <div class="version-column improved">
                <div class="version-header">
                  <q-badge label="Version 2 (Improved)" color="positive" />
                </div>
                <div class="comparison-content">
                  <div class="comparison-item">
                    <div class="item-label">Value Proposition</div>
                    <p class="item-text highlight">{{ improvedCampaign.improved.value_proposition }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Campaign Angle</div>
                    <p class="item-text highlight">{{ improvedCampaign.improved.campaign_angle }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Target Audience</div>
                    <p class="item-text highlight">{{ improvedCampaign.improved.target_audience }}</p>
                  </div>
                  <div class="comparison-item">
                    <div class="item-label">Call to Action</div>
                    <p class="item-text highlight">{{ improvedCampaign.improved.call_to_action }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="comparison-actions q-mt-lg">
              <q-btn
                label="Use Improved Version"
                color="positive"
                @click="useImprovedVersion"
                class="q-mr-sm"
              />
              <q-btn
                label="Keep Original"
                color="grey-7"
                outline
                @click="improvedCampaign = null"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import {
  generateCampaign,
  improveCampaign,
  uploadMedia,
  type CampaignGenerateRequest,
  type CampaignData,
  type CampaignImproveResponse,
  type MediaUploadResponse,
  type ApiError,
} from '../services/api';

const $q = useQuasar();

// Form data
const formData = ref<CampaignGenerateRequest>({
  product_idea: '',
  description: '',
  campaign_goal: '',
  target_audience: '',
  tone: '',
  video_context: '',
});

// Tone options
const toneOptions = [
  'Professional',
  'Casual',
  'Friendly',
  'Authoritative',
  'Inspirational',
  'Humorous',
  'Urgent',
  'Educational',
];

// Campaign state
const currentCampaign = ref<CampaignData | null>(null);
const improvedCampaign = ref<CampaignImproveResponse | null>(null);
const isGenerating = ref(false);
const isImproving = ref(false);
const isUploadingMedia = ref(false);
const selectedVideoFile = ref<File | null>(null);
const mediaUploadResult = ref<MediaUploadResponse | null>(null);
const maxVideoFileSizeBytes = 100 * 1024 * 1024;

// Feedback
const feedbackText = ref('');
const feedbackSuggestions = [
  'Make it more professional and formal',
  'Target younger audience (millennials and Gen Z)',
  'Add more urgency and conversion focus',
  'Make it more casual and friendly',
  'Focus on brand awareness',
];

const mediaPreviewLabel = computed(() =>
  mediaUploadResult.value?.product_context ? 'Extracted Product Context' : 'Transcript Preview'
);

const mediaPreviewText = computed(() => {
  const text =
    mediaUploadResult.value?.product_context ||
    mediaUploadResult.value?.transcript ||
    '';

  return text.length > 360 ? `${text.slice(0, 360)}...` : text;
});

// Load demo data
function loadDemoData() {
  formData.value = {
    product_idea: 'Smart Home Energy Monitor',
    description: 'An AI-powered device that tracks your home energy consumption in real-time, provides personalized recommendations to reduce costs, and integrates seamlessly with smart home systems. Features include mobile app control, automated scheduling, and detailed analytics.',
    campaign_goal: 'Drive product sales and increase market awareness',
    target_audience: 'Tech-savvy homeowners aged 30-50 who are environmentally conscious',
    tone: 'Professional',
    video_context: 'Product demonstration showing the device installation, mobile app interface, and real-time energy savings dashboard',
  };

  $q.notify({
    type: 'positive',
    message: 'Demo data loaded successfully',
    position: 'top',
  });
}

function handleVideoFileSelected(file: File | null) {
  mediaUploadResult.value = null;

  if (!file) {
    return;
  }

  if (!file.type.startsWith('video/')) {
    selectedVideoFile.value = null;
    $q.notify({
      type: 'warning',
      message: 'Please select a video file.',
      position: 'top',
    });
    return;
  }

  if (file.size > maxVideoFileSizeBytes) {
    selectedVideoFile.value = null;
    $q.notify({
      type: 'warning',
      message: 'Please select a video file up to 100MB.',
      position: 'top',
    });
  }
}

function formatFileSize(sizeBytes: number) {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }

  const sizeKb = sizeBytes / 1024;
  if (sizeKb < 1024) {
    return `${sizeKb.toFixed(1)} KB`;
  }

  return `${(sizeKb / 1024).toFixed(1)} MB`;
}

async function handleUploadMedia() {
  if (!selectedVideoFile.value) {
    $q.notify({
      type: 'warning',
      message: 'Select a demo video before analyzing it.',
      position: 'top',
    });
    return;
  }

  isUploadingMedia.value = true;

  try {
    const response = await uploadMedia(selectedVideoFile.value);
    mediaUploadResult.value = response;
    formData.value.video_context = response.product_context || response.transcript;

    $q.notify({
      type: 'positive',
      message: 'Demo video context added to the campaign input.',
      position: 'top',
    });
  } catch (error) {
    const apiError = error as ApiError;
    $q.notify({
      type: 'negative',
      message: `Could not analyze demo video: ${apiError.message}`,
      position: 'top',
      timeout: 5000,
    });
  } finally {
    isUploadingMedia.value = false;
  }
}

// Generate campaign
async function handleGenerateCampaign() {
  isGenerating.value = true;
  improvedCampaign.value = null;

  try {
    const response = await generateCampaign(formData.value);
    currentCampaign.value = response;

    $q.notify({
      type: 'positive',
      message: 'Campaign generated successfully!',
      position: 'top',
    });
  } catch (error) {
    const apiError = error as ApiError;
    $q.notify({
      type: 'negative',
      message: `Failed to generate campaign: ${apiError.message}`,
      position: 'top',
      timeout: 5000,
    });
  } finally {
    isGenerating.value = false;
  }
}

// Improve campaign
async function handleImproveCampaign() {
  if (!currentCampaign.value) return;

  isImproving.value = true;

  try {
    const response = await improveCampaign({
      campaign_id: currentCampaign.value.campaign_id,
      original_campaign: currentCampaign.value,
      feedback: feedbackText.value,
    });

    improvedCampaign.value = response;
    feedbackText.value = '';

    $q.notify({
      type: 'positive',
      message: 'Campaign improved successfully!',
      position: 'top',
    });
  } catch (error) {
    const apiError = error as ApiError;
    $q.notify({
      type: 'negative',
      message: `Failed to improve campaign: ${apiError.message}`,
      position: 'top',
      timeout: 5000,
    });
  } finally {
    isImproving.value = false;
  }
}

// Use improved version
function useImprovedVersion() {
  if (!improvedCampaign.value) return;

  currentCampaign.value = {
    ...improvedCampaign.value.improved,
    campaign_id: improvedCampaign.value.campaign_id,
    version: improvedCampaign.value.version,
    generated_at: improvedCampaign.value.generated_at,
  };

  improvedCampaign.value = null;

  $q.notify({
    type: 'positive',
    message: 'Now using improved campaign version',
    position: 'top',
  });
}
</script>

<style scoped lang="scss">
.campaign-dashboard {
  min-height: calc(100vh - 50px);
  background: #f6f8fa;
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
}

.dashboard-header {
  margin-bottom: 32px;

  .header-content {
    max-width: 800px;
  }

  .eyebrow {
    margin: 0 0 8px;
    color: #1f8a70;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  h1 {
    margin: 0 0 12px;
    color: #172033;
    font-size: 36px;
    line-height: 1.2;
    font-weight: 700;
  }

  .tagline {
    margin: 0;
    color: #4b5563;
    font-size: 16px;
    line-height: 1.6;
  }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  align-items: start;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.input-panel {
  border-radius: 8px;
  position: sticky;
  top: 24px;

  @media (max-width: 1200px) {
    position: static;
  }
}

.workspace-panel,
.feedback-panel,
.comparison-panel {
  border-radius: 8px;
  grid-column: 2;

  @media (max-width: 1200px) {
    grid-column: 1;
  }
}

.panel-header {
  background: #fafbfc;

  .workspace-title {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.input-form {
  .form-actions {
    display: flex;
    justify-content: flex-end;
  }
}

.demo-video-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fbfcfd;
  padding: 16px;
}

.demo-video-section__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.section-title {
  color: #172033;
  font-size: 14px;
  font-weight: 700;
}

.section-description {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.demo-video-banner {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  color: #334155;
  font-size: 13px;
}

.selected-file-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
}

.selected-file-size {
  color: #6b7280;
  font-size: 12px;
}

.demo-video-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.media-preview-card {
  margin-top: 14px;
  border-radius: 8px;
  background: #ffffff;
}

.media-preview-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  color: #6b7280;
  font-size: 12px;
}

.media-preview-card__content {
  margin-top: 12px;

  .preview-label {
    margin-bottom: 6px;
    color: #172033;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  p {
    margin: 0;
    color: #4b5563;
    font-size: 13px;
    line-height: 1.6;
  }
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.campaign-content {
  .content-section {
    margin-bottom: 32px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .section-label {
    margin-bottom: 12px;
    color: #172033;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .section-text {
    margin: 0;
    color: #4b5563;
    font-size: 15px;
    line-height: 1.6;

    &.highlight {
      padding: 16px;
      background: #f0f9ff;
      border-left: 4px solid #0ea5e9;
      border-radius: 4px;
      font-weight: 500;
    }
  }

  .hooks-list {
    border-radius: 8px;
  }

  .ad-variants {
    display: grid;
    gap: 16px;
  }

  .ad-variant-card {
    border-radius: 8px;

    .platform-badge {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .char-count {
        color: #6b7280;
        font-size: 12px;
      }
    }

    .ad-headline {
      margin-bottom: 8px;
      color: #172033;
      font-size: 16px;
      font-weight: 600;
    }

    .ad-body {
      color: #4b5563;
      font-size: 14px;
      line-height: 1.6;
    }
  }

  .cta-banner {
    background: #fef3c7;
    border: 1px solid #fbbf24;
    font-weight: 500;
  }

  .script-card {
    border-radius: 8px;

    .video-script {
      margin: 0;
      color: #374151;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
    }
  }
}

.feedback-suggestions {
  .suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.changes-summary {
  .section-label {
    margin-bottom: 12px;
    color: #172033;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.version-column {
  .version-header {
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #e5e7eb;
  }

  &.improved .version-header {
    border-bottom-color: #10b981;
  }

  .comparison-content {
    .comparison-item {
      margin-bottom: 24px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .item-label {
      margin-bottom: 8px;
      color: #6b7280;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .item-text {
      margin: 0;
      color: #374151;
      font-size: 14px;
      line-height: 1.6;

      &.highlight {
        padding: 12px;
        background: #d1fae5;
        border-left: 3px solid #10b981;
        border-radius: 4px;
        font-weight: 500;
      }
    }
  }
}

.comparison-actions {
  display: flex;
  justify-content: center;
}

@media (max-width: 640px) {
  .dashboard-container {
    padding: 24px 16px;
  }

  .dashboard-header h1 {
    font-size: 28px;
  }

  .dashboard-grid {
    gap: 16px;
  }
}
</style>
