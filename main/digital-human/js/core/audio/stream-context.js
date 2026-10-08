import BlockingQueue from '../../utils/blocking-queue.js?v=0205';
import { log } from '../../utils/logger.js?v=0205';

// Audio streaming playback context
export class StreamingContext {
    constructor(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
        this.opusDecoder = opusDecoder;
        this.audioContext = audioContext;

        // Audio parameters
        this.sampleRate = sampleRate;
        this.channels = channels;
        this.minAudioDuration = minAudioDuration;

        // Initialize queues and state
        this.queue = [];          // Decoded PCM queue currently playing
        this.activeQueue = new BlockingQueue(); // Decoded PCM queue ready for playback
        this.pendingAudioBufferQueue = [];  // Pending buffer queue
        this.audioBufferQueue = new BlockingQueue();  // Buffer queue
        this.playing = false;     // Whether playback is active
        this.endOfStream = false; // Whether end-of-stream was received
        this.source = null;       // Current audio source
        this.totalSamples = 0;    // Total accumulated samples
        this.lastPlayTime = 0;    // Last playback timestamp
        this.scheduledEndTime = 0; // End time of scheduled audio

        // Initialize audio analyzer for Live2D
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
    }

    // Buffer audio packets
    pushAudioBuffer(item) {
        this.audioBufferQueue.enqueue(...item);
    }

    // Get pending buffer queue; single-threaded updates avoid races
    async getPendingAudioBufferQueue() {
        // Wait for data and retrieve it
        const data = await this.audioBufferQueue.dequeue();
        // Assign to pending queue
        this.pendingAudioBufferQueue = data;
    }

    // Get decoded PCM playback queue; single-threaded updates avoid races
    async getQueue(minSamples) {
        const num = minSamples - this.queue.length > 0 ? minSamples - this.queue.length : 1;

        // Wait for and retrieve data
        const tempArray = await this.activeQueue.dequeue(num);
        this.queue.push(...tempArray);
    }

    // Convert Int16 audio to Float32
    convertInt16ToFloat32(int16Data) {
        const float32Data = new Float32Array(int16Data.length);
        for (let i = 0; i < int16Data.length; i++) {
            // Map Int16 range to [-1, 1] using 32768.0 to avoid asymmetrical distortion
            float32Data[i] = int16Data[i] / 32768.0;
        }
        return float32Data;
    }

    // Count packets pending decoding
    getPendingDecodeCount() {
        return this.audioBufferQueue.length + this.pendingAudioBufferQueue.length;
    }

    // Count queued playback samples (converted to 960-sample packets)
    getPendingPlayCount() {
        // Calculate samples currently queued
        const queuedSamples = this.activeQueue.length + this.queue.length;

        // Calculate scheduled but unplayed samples in Web Audio buffer
        let scheduledSamples = 0;
        if (this.playing && this.scheduledEndTime) {
            const currentTime = this.audioContext.currentTime;
            const remainingTime = Math.max(0, this.scheduledEndTime - currentTime);
            scheduledSamples = Math.floor(remainingTime * this.sampleRate);
        }

        const totalSamples = queuedSamples + scheduledSamples;
        return Math.ceil(totalSamples / 960);
    }

    // Clear all audio buffers
    clearAllBuffers() {
        log('Clear all audio buffers', 'info');

        // Clear queues while preserving references
        this.audioBufferQueue.clear();
        this.pendingAudioBufferQueue = [];
        this.activeQueue.clear();
        this.queue = [];

        // Stop current audio source
        if (this.source) {
            try {
                this.source.stop();
                this.source.disconnect();
            } catch (e) {
                // Ignore errors for already stopped sources
            }
            this.source = null;
        }

        // Reset state
        this.playing = false;
        this.scheduledEndTime = this.audioContext.currentTime;
        this.totalSamples = 0;

        log('Audio buffer cleared', 'success');
    }

    // Get analyzer node for Live2D
    getAnalyser() {
        return this.analyser;
    }

    // Decode Opus data to PCM
    async decodeOpusFrames() {
        if (!this.opusDecoder) {
            log('Opus decoder is uninitialized; cannot decode', 'error');
            return;
        } else {
            log('Opus decoder started', 'info');
        }

        while (true) {
            let decodedSamples = [];
            for (const frame of this.pendingAudioBufferQueue) {
                try {
                    // Decode using Opus decoder
                    const frameData = this.opusDecoder.decode(frame);
                    if (frameData && frameData.length > 0) {
                        // Convert to Float32
                        const floatData = this.convertInt16ToFloat32(frameData);
                        // Use loop rather than spread operator
                        for (let i = 0; i < floatData.length; i++) {
                            decodedSamples.push(floatData[i]);
                        }
                    }
                } catch (error) {
                    log("Opus decoding failed: " + error.message, 'error');
                }
            }

            if (decodedSamples.length > 0) {
                // Use loop rather than spread operator
                for (let i = 0; i < decodedSamples.length; i++) {
                    this.activeQueue.enqueue(decodedSamples[i]);
                }
                this.totalSamples += decodedSamples.length;
            } else {
                log('No samples decoded successfully', 'warning');
            }
            await this.getPendingAudioBufferQueue();
        }
    }

    // Start audio playback
    async startPlaying() {
        this.scheduledEndTime = this.audioContext.currentTime; // Track scheduled audio end time

        while (true) {
            // Initial buffer: wait for enough samples before playback
            const minSamples = this.sampleRate * this.minAudioDuration * 2;
            if (!this.playing && this.queue.length < minSamples) {
                await this.getQueue(minSamples);
            }
            this.playing = true;

            // Continuously play small blocks from the queue
            while (this.playing && this.queue.length > 0) {
                // Play 120 ms per chunk (two Opus packets)
                const playDuration = 0.12;
                const targetSamples = Math.floor(this.sampleRate * playDuration);
                const actualSamples = Math.min(this.queue.length, targetSamples);

                if (actualSamples === 0) break;

                const currentSamples = this.queue.splice(0, actualSamples);
                const audioBuffer = this.audioContext.createBuffer(this.channels, currentSamples.length, this.sampleRate);
                audioBuffer.copyToChannel(new Float32Array(currentSamples), 0);

                // Create audio source
                this.source = this.audioContext.createBufferSource();
                this.source.buffer = audioBuffer;

                // Schedule exact playback timing
                const currentTime = this.audioContext.currentTime;
                const startTime = Math.max(this.scheduledEndTime, currentTime);

                // Connect to analyzer and output
                this.source.connect(this.analyser);
                this.source.connect(this.audioContext.destination);

                log(`Scheduling playback for ${currentSamples.length}  samples, approximately ${(currentSamples.length / this.sampleRate).toFixed(2)} seconds`, 'debug');
                this.source.start(startTime);

                // Update scheduled start time for next audio block
                const duration = audioBuffer.duration;
                this.scheduledEndTime = startTime + duration;
                this.lastPlayTime = startTime;

                // Wait for more data if queue is empty
                if (this.queue.length < targetSamples) {
                    break;
                }
            }

            // Wait for new data
            await this.getQueue(minSamples);
        }
    }
}

// Factory for creating streamingContext instances
export function createStreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
    return new StreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration);
}