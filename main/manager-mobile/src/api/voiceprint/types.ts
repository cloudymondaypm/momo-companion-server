// Voiceprint information response type
export interface VoicePrint {
  id: string
  audioId: string
  sourceName: string
  introduce: string
  createDate: string
}

// Voice conversation history type
export interface ChatHistory {
  content: string
  audioId: string
}

// Create speaker payload type
export interface CreateSpeakerData {
  agentId: string
  audioId: string
  sourceName: string
  introduce: string
}

// Generic response type
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}
