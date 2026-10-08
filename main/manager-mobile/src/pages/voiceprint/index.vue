<script lang="ts" setup>
import type { ChatHistory, CreateSpeakerData, VoicePrint } from '@/api/voiceprint'
import { computed, onMounted, ref } from 'vue'
import { useMessage } from 'wot-design-uni/components/wd-message-box'
import { useToast } from 'wot-design-uni/components/wd-toast'
import { createVoicePrint, deleteVoicePrint, getAudioDownloadId, getChatHistory, getVoicePrintList, updateVoicePrint } from '@/api/voiceprint'
import { t } from '@/i18n'
import { getEnvBaseUrl } from '@/utils'

defineOptions({
  name: 'VoicePrintManage',
})

const props = withDefaults(defineProps<Props>(), {
  agentId: 'default',
})

const emits = defineEmits(['update-refresher-enabled'])

// Receive props
interface Props {
  agentId?: string
}

// Get safe-area inset
let safeAreaInsets: any
let systemInfo: any

// #ifdef MP-WEIXIN
systemInfo = uni.getWindowInfo()
safeAreaInsets = systemInfo.safeArea
  ? {
      top: systemInfo.safeArea.top,
      right: systemInfo.windowWidth - systemInfo.safeArea.right,
      bottom: systemInfo.windowHeight - systemInfo.safeArea.bottom,
      left: systemInfo.safeArea.left,
    }
  : null
// #endif

// #ifndef MP-WEIXIN
systemInfo = uni.getSystemInfoSync()
safeAreaInsets = systemInfo.safeAreaInsets
// #endif

const message = useMessage()
const toast = useToast()

// Page data
const voicePrintList = ref<VoicePrint[]>([])
const chatHistoryList = ref<ChatHistory[]>([])
const chatHistoryActions = ref<any[]>([])
const swipeStates = ref<Record<string, 'left' | 'close' | 'right'>>({})
const loading = ref(false)

// Audio playback state
const audioRef = ref<UniApp.InnerAudioContext | null>(null)
const playingAudioId = ref<string>('')

// Use provided agent ID
const currentAgentId = computed(() => {
  return props.agentId
})

// Agent selection has been removed

// Dialog state
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showChatHistoryDialog = ref(false)
const addForm = ref<CreateSpeakerData>({
  agentId: '',
  audioId: '',
  sourceName: '',
  introduce: '',
})
const editForm = ref<VoicePrint>({
  id: '',
  audioId: '',
  sourceName: '',
  introduce: '',
  createDate: '',
})

// Get voiceprint list
async function loadVoicePrintList() {
  try {
    console.log('Get voiceprint list')

    // Check for selected agent
    if (!currentAgentId.value) {
      console.warn(t('voiceprint.noSelectedAgent'))
      voicePrintList.value = []
      return
    }

    loading.value = true
    const data = await getVoicePrintList(currentAgentId.value)

    // Initialize swipe state
    const list = data || []
    list.forEach((item) => {
      if (!swipeStates.value[item.id]) {
        swipeStates.value[item.id] = 'close'
      }
    })

    voicePrintList.value = list
  }
  catch (error) {
    console.error('Failed to retrieve voiceprints:', error)
    voicePrintList.value = []
  }
  finally {
    loading.value = false
  }
}

// Expose refresh method to parent
async function refresh() {
  await loadVoicePrintList()
}

// Get voice conversation history
async function loadChatHistory() {
  try {
    if (!currentAgentId.value) {
      toast.error(t('voiceprint.pleaseSelectAgent'))
      return
    }

    const data = await getChatHistory(currentAgentId.value)
    chatHistoryList.value = data || []
    // Convert to ActionSheet format
    chatHistoryActions.value = chatHistoryList.value.map((item, index) => ({
      name: item.content,
      audioId: item.audioId,
      index,
    }))
  }
  catch (error) {
    console.error('Failed to retrieve conversation history:', error)
    toast.error(t('voiceprint.fetchHistoryFailed'))
  }
}

// Open add dialog
function openAddDialog() {
  if (!currentAgentId.value) {
    toast.error(t('voiceprint.pleaseSelectAgent'))
    return
  }

  // Check voiceprint API configuration by fetching the list
  const checkVoicePrintConfig = async () => {
    try {
      await getVoicePrintList(currentAgentId.value)
      // API available, open add dialog
      addForm.value = {
        agentId: currentAgentId.value,
        audioId: '',
        sourceName: '',
        introduce: '',
      }
      showAddDialog.value = true
    }
    catch (error: any) {
      // Handle unconfigured voiceprint API
      if (error.message && error.message.includes('[10054]')) {
        toast.error(t('voiceprint.voiceprintInterfaceNotConfigured'))
      }
      else {
        // Continue opening dialog for other errors
        addForm.value = {
          agentId: currentAgentId.value,
          audioId: '',
          sourceName: '',
          introduce: '',
        }
        showAddDialog.value = true
      }
    }
  }

  checkVoicePrintConfig()
}

// Open edit dialog
function openEditDialog(item: VoicePrint) {
  editForm.value = { ...item }
  showEditDialog.value = true
}

// Get display text for selected audio
function getSelectedAudioContent(audioId: string) {
  if (!audioId)
    return t('voiceprint.clickToSelectVector')
  const chatItem = chatHistoryList.value.find(item => item.audioId === audioId)
  return chatItem ? chatItem.content : `Selected: ${audioId.substring(0, 8)}...`
}

// Select voiceprint embedding
function selectAudioId({ item }: { item: any }) {
  if (showAddDialog.value) {
    addForm.value.audioId = item.audioId
  }
  else if (showEditDialog.value) {
    editForm.value.audioId = item.audioId
  }
  showChatHistoryDialog.value = false
}

// Tap to select
function handleItemClick(item: any) {
  selectAudioId({ item })
}

// Submit new speaker
async function submitAdd() {
  if (!addForm.value.sourceName.trim()) {
    toast.error(t('voiceprint.pleaseInputName'))
    return
  }
  if (!addForm.value.audioId) {
    toast.error(t('voiceprint.pleaseSelectVector'))
    return
  }

  try {
    await createVoicePrint(addForm.value)
    toast.success(t('voiceprint.addSuccess'))
    showAddDialog.value = false
    await loadVoicePrintList()
  }
  catch (error) {
    console.error('Failed to add speaker:', error)
    toast.error(t('voiceprint.addFailed'))
  }
}

// Submit speaker edit
async function submitEdit() {
  if (!editForm.value.sourceName.trim()) {
    toast.error(t('voiceprint.pleaseInputName'))
    return
  }
  if (!editForm.value.audioId) {
    toast.error(t('voiceprint.pleaseSelectVector'))
    return
  }

  try {
    await updateVoicePrint({
      id: editForm.value.id,
      audioId: editForm.value.audioId,
      sourceName: editForm.value.sourceName,
      introduce: editForm.value.introduce,
      createDate: editForm.value.createDate,
    })
    toast.success(t('voiceprint.editSuccess'))
    showEditDialog.value = false
    await loadVoicePrintList()
  }
  catch (error) {
    console.error('Failed to edit speaker:', error)
    toast.error(t('voiceprint.editFailed'))
  }
}

// Handle edit action
function handleEdit(item: VoicePrint) {
  openEditDialog(item)
  swipeStates.value[item.id] = 'close'
}

// Delete voiceprint
async function handleDelete(id: string) {
  message.confirm({
    msg: t('voiceprint.deleteConfirmMsg'),
    title: t('voiceprint.deleteConfirmTitle'),
  }).then(async () => {
    await deleteVoicePrint(id)
    toast.success(t('voiceprint.deleteSuccess'))
    await loadVoicePrintList()
  }).catch(() => {
    console.log('Cancel button clicked')
  })
}

// Play audio
async function playAudio(audioId: string, event: Event) {
  event.stopPropagation() // Stop event propagation to keep dropdown open

  if (!audioId) {
    toast.warning(t('voiceprint.audioNotExist'))
    return
  }

  // Stop if same audio is playing
  if (playingAudioId.value === audioId) {
    stopAudio()
    return
  }

  // Stop previous audio
  stopAudio()

  try {
    // Get audio download ID first
    playingAudioId.value = audioId
    const downloadId = await getAudioDownloadId(audioId)

    if (!downloadId) {
      toast.error(t('voiceprint.getAudioFailed'))
      playingAudioId.value = ''
      return
    }

    // Get baseURL
    const baseURL = getEnvBaseUrl()
    const audioUrl = `${baseURL}/agent/play/${downloadId}`

    // Create audio instance
    audioRef.value = uni.createInnerAudioContext()
    audioRef.value.src = audioUrl
    audioRef.value.autoplay = true

    // Listen for playback end
    audioRef.value.onEnded(() => {
      playingAudioId.value = ''
    })

    // Listen for playback error
    audioRef.value.onError((error) => {
      console.error('Audio playback error:', error)
      toast.error(t('voiceprint.audioPlayFailed'))
      playingAudioId.value = ''
    })
  }
  catch (error) {
    console.error('Failed to play audio:', error)
    toast.error(t('voiceprint.audioPlayFailed'))
    playingAudioId.value = ''
  }
}

// Stop audio
function stopAudio() {
  if (audioRef.value) {
    audioRef.value.stop()
    audioRef.value.destroy()
    audioRef.value = null
  }
  playingAudioId.value = ''
}

watch(() => [showAddDialog.value, showEditDialog.value], (newValues) => {
  if (newValues.some((value: boolean) => value)) {
    emits('update-refresher-enabled', false)
  }
  else {
    emits('update-refresher-enabled', true)
  }
})

onMounted(async () => {
  // Agent selection defaults simplified

  loadVoicePrintList()
  loadChatHistory()
})

// Expose methods to parent
defineExpose({
  showAddDialog,
  showEditDialog,
  refresh,
})
</script>

<template>
  <view class="voiceprint-container" style="background: #f5f7fb; min-height: 100%;">
    <!-- Loading state -->
    <view v-if="loading && voicePrintList.length === 0" class="loading-container">
      <wd-loading color="#336cff" />
      <text class="loading-text">
        {{ t('voiceprint.loading') }}
      </text>
    </view>

    <!-- Voiceprint list -->
    <view v-else-if="voicePrintList.length > 0" class="voiceprint-list">
      <!-- Voiceprint cards -->
      <view class="box-border flex flex-col gap-[24rpx] p-[20rpx]">
        <view v-for="item in voicePrintList" :key="item.id">
          <wd-swipe-action
            :model-value="swipeStates[item.id] || 'close'"
            @update:model-value="swipeStates[item.id] = $event"
          >
            <view class="bg-[#fbfbfb] p-[32rpx]" @click="handleEdit(item)">
              <view>
                <text class="mb-[12rpx] block text-[32rpx] text-[#232338] font-semibold">
                  {{ item.sourceName }}
                </text>
                <text class="mb-[12rpx] block text-[28rpx] text-[#65686f] leading-[1.4]">
                  {{ item.introduce || 'No description' }}
                </text>
                <text class="block text-[24rpx] text-[#9d9ea3]">
                  {{ item.createDate }}
                </text>
              </view>
            </view>

            <template #right>
              <view class="h-full flex">
                <view
                  class="h-full min-w-[120rpx] flex items-center justify-center bg-[#ff4d4f] p-x-[32rpx] text-[28rpx] text-white font-medium"
                  @click="handleDelete(item.id)"
                >
                  <wd-icon name="delete" />
                  {{ t('voiceprint.delete') }}
                </view>
              </view>
            </template>
          </wd-swipe-action>
        </view>
      </view>
    </view>

    <!-- Empty state -->
    <view v-else-if="!loading" class="empty-container">
      <view class="flex flex-col items-center justify-center p-[100rpx_40rpx] text-center">
        <wd-icon name="voice" custom-class="text-[120rpx] text-[#d9d9d9] mb-[32rpx]" />
        <text class="mb-[32rpx] text-[32rpx] text-[#666666] font-medium">
          {{ t('voiceprint.emptyTitle') }}
        </text>
        <text class="text-[26rpx] text-[#999999] leading-[1.5]">
          {{ t('voiceprint.emptyDesc') }}
        </text>
      </view>
    </view>

    <!-- Floating action button -->
    <wd-fab custom-style="z-index:10" type="primary" size="small" :draggable="true" :expandable="false" @click="openAddDialog">
      <wd-icon name="add" />
    </wd-fab>

    <!-- MessageBox component -->
    <wd-message-box />
  </view>

  <!-- Add speaker dialog -->
  <wd-popup
    v-model="showAddDialog"
    position="center"
    custom-style="width: 90%; max-width: 400px; border-radius: 16px;"
    safe-area-inset-bottom
  >
    <view>
      <view class="p-[32rpx]">
        <!-- Select voiceprint embedding -->
        <view class="mb-[32rpx]">
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.voiceVector') }}
          </text>
          <view
            class="flex cursor-pointer items-center justify-between border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[20rpx] transition-all duration-300 active:bg-[#eef3ff]"
            @click="showChatHistoryDialog = true"
          >
            <text
              class="m-r-[16rpx] flex-1 text-left text-[26rpx] text-[#232338]"
              :class="{ 'text-[#9d9ea3]': !addForm.audioId }"
            >
              {{ getSelectedAudioContent(addForm.audioId) }}
            </text>
            <wd-icon name="arrow-down" custom-class="text-[20rpx] text-[#9d9ea3]" />
          </view>
        </view>

        <!-- Name -->
        <view class="mb-[32rpx]">
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.name') }}
          </text>
          <input
            v-model="addForm.sourceName"
            class="box-border h-[80rpx] w-full border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[16rpx_20rpx] text-[28rpx] text-[#232338] leading-[1.4] outline-none focus:border-[#336cff] focus:bg-white placeholder:text-[#9d9ea3]"
            type="text" :placeholder="t('voiceprint.pleaseInputName')"
          >
        </view>

        <!-- Description -->
        <view>
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.description') }}
          </text>
          <textarea
            v-model="addForm.introduce" :maxlength="100" :placeholder="t('voiceprint.pleaseInputDescription')"
            class="box-border h-[200rpx] w-full resize-none border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[20rpx] text-[26rpx] text-[#232338] leading-[1.6] outline-none focus:border-[#336cff] focus:bg-white placeholder:text-[#9d9ea3]"
          />
          <view class="mt-[8rpx] text-right text-[22rpx] text-[#9d9ea3]">
            {{ (addForm.introduce || '').length }}/100
          </view>
        </view>
      </view>

      <view class="flex gap-[16rpx] border-t-[2rpx] border-[#eeeeee] p-[24rpx_32rpx_32rpx]">
        <wd-button type="info" custom-class="flex-1" @click="showAddDialog = false">
          {{ t('voiceprint.cancel') }}
        </wd-button>
        <wd-button type="primary" custom-class="flex-1" @click="submitAdd">
          {{ t('voiceprint.save') }}
        </wd-button>
      </view>
    </view>
  </wd-popup>

  <!-- Edit speaker dialog -->
  <wd-popup
    v-model="showEditDialog" position="center" custom-style="width: 90%; max-width: 400px; border-radius: 16px;"
    safe-area-inset-bottom
  >
    <view>
      <view class="box-border w-full flex items-center justify-between border-b-[2rpx] border-[#eeeeee] p-[32rpx_32rpx_24rpx]">
        <text class="w-full text-center text-[32rpx] text-[#232338] font-semibold">
          {{ t('voiceprint.editSpeaker') }}
        </text>
      </view>

      <view class="p-[32rpx]">
        <!-- Select voiceprint embedding -->
        <view class="mb-[32rpx]">
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.voiceVector') }}
          </text>
          <view
            class="flex cursor-pointer items-center justify-between border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[20rpx] transition-all duration-300 active:bg-[#eef3ff]"
            @click="showChatHistoryDialog = true"
          >
            <text
              class="m-r-[16rpx] flex-1 text-left text-[26rpx] text-[#232338]"
              :class="{ 'text-[#9d9ea3]': !editForm.audioId }"
            >
              {{ getSelectedAudioContent(editForm.audioId) }}
            </text>
            <wd-icon name="arrow-down" custom-class="text-[20rpx] text-[#9d9ea3]" />
          </view>
        </view>

        <!-- Name -->
        <view class="mb-[32rpx]">
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.name') }}
          </text>
          <input
            v-model="editForm.sourceName"
            class="box-border h-[80rpx] w-full border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[16rpx_20rpx] text-[28rpx] text-[#232338] leading-[1.4] outline-none focus:border-[#336cff] focus:bg-white placeholder:text-[#9d9ea3]"
            type="text" :placeholder="t('voiceprint.pleaseInputName')"
          >
        </view>

        <!-- Description -->
        <view>
          <text class="mb-[16rpx] block text-[28rpx] text-[#232338] font-medium">
            <text class="text-red">
              *
            </text>
            {{ t('voiceprint.description') }}
          </text>
          <textarea
            v-model="editForm.introduce" :maxlength="100" :placeholder="t('voiceprint.pleaseInputDescription')"
            class="box-border h-[200rpx] w-full resize-none border-[1rpx] border-[#eeeeee] rounded-[12rpx] bg-[#f5f7fb] p-[20rpx] text-[26rpx] text-[#232338] leading-[1.6] outline-none focus:border-[#336cff] focus:bg-white placeholder:text-[#9d9ea3]"
          />
          <view class="mt-[8rpx] text-right text-[22rpx] text-[#9d9ea3]">
            {{ (editForm.introduce || '').length }}/100
          </view>
        </view>
      </view>

      <view class="flex gap-[16rpx] border-t-[2rpx] border-[#eeeeee] p-[24rpx_32rpx_32rpx]">
        <wd-button type="info" custom-class="flex-1" @click="showEditDialog = false">
          {{ t('voiceprint.cancel') }}
        </wd-button>
        <wd-button type="primary" custom-class="flex-1" @click="submitEdit">
          {{ t('voiceprint.save') }}
        </wd-button>
      </view>
    </view>
  </wd-popup>

  <!-- Custom voice conversation selector popup -->
  <wd-popup v-model="showChatHistoryDialog" class="custom-popup" position="bottom" @close="stopAudio">
    <view class="rounded-[20rpx] bg-white pb-[20rpx] pt-[20rpx]">
      <view class="max-h-[600rpx] overflow-y-auto rounded-[20rpx]">
        <view
          v-for="item in chatHistoryActions"
          :key="item.audioId"
          class="flex items-center justify-between border-b border-[#f5f5f5] p-[32rpx] transition-all active:bg-[#f5f7fb]"
          @click="handleItemClick(item)"
        >
          <text class="flex-1 text-[28rpx] text-[#232338]">
            {{ item.name }}
          </text>
          <view class="ml-[20rpx]" @click.stop="playAudio(item.audioId, $event)">
            <wd-icon
              :name="playingAudioId === item.audioId ? 'pause-circle' : 'play-circle'"
              size="24px"
              :custom-class="playingAudioId === item.audioId ? 'text-[#336cff]' : 'text-[#9d9ea3]'"
            />
          </view>
        </view>
      </view>
    </view>
  </wd-popup>
</template>

<style lang="scss" scoped>
.voiceprint-container {
  position: relative;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 40rpx;
}

.loading-text {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #666666;
}

::v-deep .custom-popup {
  .wd-popup {
    padding: 20rpx !important;
    background: transparent;
  }
}
</style>
