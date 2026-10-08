import { log } from '../../utils/logger.js?v=0205';


// Check Opus library availability
export function checkOpusLoaded() {
    try {
        // Verify Module exported by local library exists
        if (typeof Module === 'undefined') {
            throw new Error('Opus library unavailable: Module object not found');
        }

        // Prefer Module.instance as exported by libopus.js
        if (typeof Module.instance !== 'undefined' && typeof Module.instance._opus_decoder_get_size === 'function') {
            // Use Module.instance instead of global Module
            window.ModuleInstance = Module.instance;
            log('Opus library loaded through Module.instance', 'success');

            // Hide status after three seconds
            const statusElement = document.getElementById('scriptStatus');
            if (statusElement) statusElement.style.display = 'none';
            return;
        }

        // Check global Module if Module.instance missing
        if (typeof Module._opus_decoder_get_size === 'function') {
            window.ModuleInstance = Module;
            log('Opus library loaded using global Module', 'success');

            // Hide status after three seconds
            const statusElement = document.getElementById('scriptStatus');
            if (statusElement) statusElement.style.display = 'none';
            return;
        }

        throw new Error('Opus decoder function missing; check Module structure');
    } catch (err) {
        log(`Opus library failed to load; verify libopus.js exists and is valid: ${err.message}`, 'error');
    }
}


// Create an Opus encoder
let opusEncoder = null;
export function initOpusEncoder() {
    try {
        if (opusEncoder) {
            return opusEncoder; // Already initialized
        }

        if (!window.ModuleInstance) {
            log('Unable to create Opus encoder: ModuleInstance unavailable', 'error');
            return;
        }

        // Initialize an Opus encoder
        const mod = window.ModuleInstance;
        const sampleRate = 16000; // 16 kHz sample rate
        const channels = 1;       // Mono audio
        const application = 2048; // OPUS_APPLICATION_VOIP = 2048

        // Create encoder
        opusEncoder = {
            channels: channels,
            sampleRate: sampleRate,
            frameSize: 960, // 60ms @ 16kHz = 60 * 16 = 960 samples
            maxPacketSize: 4000, // Maximum packet size
            module: mod,

            // Initialize encoder
            init: function () {
                try {
                    // Get encoder size
                    const encoderSize = mod._opus_encoder_get_size(this.channels);
                    log(`Opus encoder size: ${encoderSize}bytes`, 'info');

                    // Allocate memory
                    this.encoderPtr = mod._malloc(encoderSize);
                    if (!this.encoderPtr) {
                        throw new Error("Unable to allocate encoder memory");
                    }

                    // Initialize encoder
                    const err = mod._opus_encoder_init(
                        this.encoderPtr,
                        this.sampleRate,
                        this.channels,
                        application
                    );

                    if (err < 0) {
                        throw new Error(`Opus encoder initialization failed: ${err}`);
                    }

                    // Set bitrate (16 kbps)
                    mod._opus_encoder_ctl(this.encoderPtr, 4002, 16000); // OPUS_SET_BITRATE

                    // Set complexity 0–10 (higher quality uses more CPU)
                    mod._opus_encoder_ctl(this.encoderPtr, 4010, 5);     // OPUS_SET_COMPLEXITY

                    // Enable DTX (omit silent frames)
                    mod._opus_encoder_ctl(this.encoderPtr, 4016, 1);     // OPUS_SET_DTX

                    log("Opus encoder initialized", 'success');
                    return true;
                } catch (error) {
                    if (this.encoderPtr) {
                        mod._free(this.encoderPtr);
                        this.encoderPtr = null;
                    }
                    log(`Opus encoder initialization failed: ${error.message}`, 'error');
                    return false;
                }
            },

            // Encode PCM as Opus
            encode: function (pcmData) {
                if (!this.encoderPtr) {
                    if (!this.init()) {
                        return null;
                    }
                }

                try {
                    const mod = this.module;

                    // Allocate memory for PCM data
                    const pcmPtr = mod._malloc(pcmData.length * 2); // 2 bytes/int16

                    // Copy PCM to heap
                    for (let i = 0; i < pcmData.length; i++) {
                        mod.HEAP16[(pcmPtr >> 1) + i] = pcmData[i];
                    }

                    // Allocate output memory
                    const outPtr = mod._malloc(this.maxPacketSize);

                    // Perform encoding
                    const encodedLen = mod._opus_encode(
                        this.encoderPtr,
                        pcmPtr,
                        this.frameSize,
                        outPtr,
                        this.maxPacketSize
                    );

                    if (encodedLen < 0) {
                        throw new Error(`Opus encoding failed: ${encodedLen}`);
                    }

                    // Copy encoded data
                    const opusData = new Uint8Array(encodedLen);
                    for (let i = 0; i < encodedLen; i++) {
                        opusData[i] = mod.HEAPU8[outPtr + i];
                    }

                    // Free memory
                    mod._free(pcmPtr);
                    mod._free(outPtr);

                    return opusData;
                } catch (error) {
                    log(`Opus encoding error: ${error.message}`, 'error');
                    return null;
                }
            },

            // Destroy encoder
            destroy: function () {
                if (this.encoderPtr) {
                    this.module._free(this.encoderPtr);
                    this.encoderPtr = null;
                }
            }
        };

        opusEncoder.init();
        return opusEncoder;
    } catch (error) {
        log(`Failed to create Opus encoder: ${error.message}`, 'error');
        return false;
    }
}