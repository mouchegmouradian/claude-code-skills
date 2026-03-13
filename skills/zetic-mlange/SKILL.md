---
name: zetic-mlange
description: "Help users integrate the ZETIC Melange (MLange) on-device AI SDK into Android (Kotlin/Java) and iOS (Swift) mobile apps. Use this skill whenever the user mentions Zetic, MLange, Melange, ZeticMLangeModel, ZeticMLangeLLMModel, ZeticMLangeHFModel, on-device NPU inference for mobile, or deploying ML models to Android/iOS with NPU acceleration. Also trigger when users ask about running LLMs on-device with GGUF quantization, mobile NPU model deployment, or converting PyTorch/ONNX models for mobile inference. Covers general model inference, LLM inference (streaming token generation), and HuggingFace model loading."
---

# ZETIC Melange (MLange) SDK Integration Skill

This skill helps users integrate the ZETIC Melange on-device AI SDK into mobile applications.

**Naming**: The product is called **Melange** but source code uses `MLange` (e.g., `ZeticMLangeModel`).

## Key Resources

- Dashboard: https://melange.zetic.ai
- Docs: https://docs.zetic.ai
- GitHub: https://github.com/zetic-ai
- Contact: contact@zetic.ai

## Prerequisites

Users need two things from the Melange Dashboard:
1. **Personal Key** — authentication credential
2. **Model Name** — in `account_name/project_name` format (e.g., `"Steve/YOLOv11_comparison"`)

Supported upload formats: PyTorch `.pt2`, ONNX `.onnx`, TorchScript `.pt`

### SDK Setup

**Android (Gradle):**
```kotlin
// app/build.gradle.kts
dependencies {
    implementation("com.zeticai.mlange:mlange:+")
}

android {
    packaging { jniLibs.useLegacyPackaging = true }
}
```
Add `<uses-permission android:name="android.permission.INTERNET" />` to AndroidManifest.xml (SDK downloads model weights on first run).

**iOS (CocoaPods):**
```ruby
pod 'ZeticMLange'
```

**iOS (SPM):** Add `https://github.com/zetic-ai/ZeticMLangeiOS` as a Swift Package dependency.

---

## CRITICAL: Threading & Concurrency Rules

All MLange SDK calls are **synchronous and blocking**. They directly interface with native hardware (NPU/GPU/CPU) using fixed memory buffers. Every code example you generate MUST follow these rules:

### Rule 1: Never Call on the Main/UI Thread
`model.run()`, `model.waitForNextToken()`, and even model construction can block for significant time. Always dispatch to a background thread.

**Android (Kotlin):**
```kotlin
// Always use Dispatchers.IO for blocking SDK calls (large thread pool designed for blocking work).
// Do NOT use Dispatchers.Default — it's sized to CPU cores and blocking calls would starve other coroutines.
withContext(Dispatchers.IO) {
    val outputs = model.run(inputs)
}
```

**iOS (Swift):**
```swift
// Use an actor or Task to move off @MainActor
func infer() async throws -> [Tensor] {
    try await Task.detached {
        try self.model.run(inputs: inputs)  // Runs on cooperative thread pool
    }.value
}
```

### Rule 2: Single-Consumer Access
Model instances use fixed native memory buffers. Concurrent `run()` calls will overwrite inputs or crash the native driver. Guarantee serial access via `Mutex` + `Dispatchers.IO` (Android) or actors (iOS).

**Android (Kotlin):**
```kotlin
// Mutex serializes access; Dispatchers.IO borrows a thread from the shared pool only when needed.
private val modelMutex = Mutex()

suspend fun infer(inputs: Array<Tensor>): Array<Tensor> = modelMutex.withLock {
    withContext(Dispatchers.IO) {
        model.run(inputs)  // Only one call at a time, guaranteed by mutex
    }
}
```

**iOS (Swift):**
```swift
// Use a dedicated actor to serialize access
actor ModelInferenceActor {
    private let model: ZeticMLangeModel

    init(model: ZeticMLangeModel) {
        self.model = model
    }

    func infer(inputs: [Tensor]) throws -> [Tensor] {
        try model.run(inputs: inputs)  // Actor guarantees serial access
    }
}

// Usage — safe from any async context
let outputs = try await inferenceActor.infer(inputs: inputs)
```

### Rule 3: Lifecycle-Aware Cleanup
Models hold significant native memory and hardware handles. Always close/deinit in lifecycle callbacks.

**Android:** Call `model.close()` in `ViewModel.onCleared()` or `Activity.onDestroy()`.
**iOS:** Call cleanup from `.onDisappear` or an explicit `teardown()` method. Do NOT put cleanup in `deinit` via `Task { }` — `deinit` is synchronous and the Task is fire-and-forget with no guarantee it runs before the process suspends.

Failing to close a model can leak memory and prevent other apps from accessing the NPU.

### Rule 4: Zero-Allocation in Hot Loops
For real-time inference (camera feed, audio stream), pre-allocate buffers once and reuse them every frame. Creating new `Tensor`/`FloatArray`/`ByteBuffer` objects per frame triggers GC pauses.

```kotlin
// GOOD: Pre-allocate once
val inputBuffers = model.getInputBuffers()
// Reuse in every frame
fun onFrame(frameData: ByteArray) {
    inputBuffers[0].copy(frameData)
    val outputs = model.run()
}

// BAD: Allocating per frame
fun onFrame(frameData: ByteArray) {
    val tensor = Tensor(frameData) // GC pressure!
    val outputs = model.run(arrayOf(tensor))
}
```

### Rule 5: Drop-Frame Strategy for Real-Time Data
If the model is busy when a new frame arrives, skip it rather than queueing. This keeps the app responsive.

```kotlin
private val isRunning = AtomicBoolean(false)

fun onCameraFrame(frame: ByteArray) {
    if (!isRunning.compareAndSet(false, true)) return // Model busy — drop frame
    scope.launch(Dispatchers.IO) {
        try {
            inputBuffers[0].copy(frame)
            val outputs = model.run()
            withContext(Dispatchers.Main) { updateUI(outputs) }
        } finally {
            isRunning.set(false)
        }
    }
}
```

### Rule 6: Reset State Between Sessions (LLM)
LLM models maintain internal KV cache state. Always call `cleanUp()` before starting a new conversation or prompt session to avoid stale context contamination.

```kotlin
// Before each new conversation
model.cleanUp()
model.run("New conversation prompt...")
```

---

## General Model Inference (ZeticMLangeModel)

### Android (Kotlin)

```kotlin
import com.zeticai.mlange.core.model.ZeticMLangeModel
import com.zeticai.mlange.core.tensor.Tensor
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

// --- In a Repository or ViewModel ---

private val modelMutex = Mutex()
private var model: ZeticMLangeModel? = null

// Initialize off main thread. Mutex prevents double-init races.
suspend fun initModel(context: Context) = modelMutex.withLock {
    if (model == null) {
        withContext(Dispatchers.IO) {
            model = ZeticMLangeModel(context, "PERSONAL_KEY", "account/model_name")
        }
    }
}

// Thread-safe inference — mutex serializes, IO provides background thread.
suspend fun infer(inputs: Array<Tensor>): Array<Tensor> = modelMutex.withLock {
    val m = model ?: throw IllegalStateException("Model not initialized — call initModel() first")
    withContext(Dispatchers.IO) {
        m.run(inputs)
    }
}

// Lifecycle cleanup (e.g., in ViewModel.onCleared or Repository.close)
fun close() {
    model?.close()
    model = null
}
```

**Why `Mutex` + `Dispatchers.IO`:** The mutex guarantees only one call touches the model at a time. `Dispatchers.IO` borrows a thread from the shared pool only during the blocking call — no dedicated thread sits idle between inferences. This is lightweight and scales to multiple model instances (pipelines, encoder-decoder pairs). For the simplest single-model case, `newSingleThreadContext("Model")` is an alternative that avoids the mutex entirely via thread confinement.

**Constructor variants (all blocking — always wrap in background dispatcher):**
- `(context, personalKey, name)` — auto mode
- `(context, personalKey, name, modelMode=)` — specify inference mode
- `(context, personalKey, name, target=)` — specify hardware target (Pro tier)
- `(context, personalKey, name, target=, apType=)` — target + processor (Pro tier)

All constructors accept optional: `version: Int?`, `onProgress: ((Float) -> Unit)?`, `onStatusChanged: ((ModelLoadingStatus) -> Unit)?`

### iOS (Swift)

```swift
import ZeticMLange

// --- Use a dedicated actor for thread-safe serial access ---

actor MLangeModelActor {
    private var model: ZeticMLangeModel?

    func initialize(personalKey: String, name: String) throws {
        model = try ZeticMLangeModel(personalKey: personalKey, name: name)
    }

    func infer(inputs: [Tensor]) throws -> [Tensor] {
        guard let model else { throw ZeticMLangeError("ModelNotInitialized", "Call initialize() before using the model") }
        return try model.run(inputs: inputs)
    }

    func cleanup() {
        model = nil  // releases native resources
    }
}

// --- In a ViewModel (@MainActor) ---

@Observable
@MainActor
final class InferenceViewModel {
    private let modelActor = MLangeModelActor()

    func setup() async throws {
        try await modelActor.initialize(
            personalKey: "PERSONAL_KEY", name: "account/model_name")
    }

    func runInference(inputs: [Tensor]) async throws -> [Tensor] {
        try await modelActor.infer(inputs: inputs)
    }

    // Call explicitly from .onDisappear or when done — do NOT rely on deinit.
    func teardown() async {
        await modelActor.cleanup()
    }
}
```

**Constructor variants (all blocking — always call from actor or detached Task):**

---

## LLM Inference (ZeticMLangeLLMModel)

### Android (Kotlin)

```kotlin
import com.zeticai.mlange.core.model.llm.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

private val llmMutex = Mutex()
private var llmModel: ZeticMLangeLLMModel? = null

// Initialize off main thread — model downloads weights on first run (~700MB for LLMs).
// Always show download progress to the user.
suspend fun initLLM(context: Context, onProgress: (Float) -> Unit) = llmMutex.withLock {
    if (llmModel == null) {
        withContext(Dispatchers.IO) {
            llmModel = ZeticMLangeLLMModel(context, "PERSONAL_KEY", "account/model_name",
                target = LLMTarget.LLAMA_CPP,
                quantType = LLMQuantType.GGUF_QUANT_Q4_K_M,
                onProgress = onProgress)
        }
    }
}

// Stream tokens as a Flow — idiomatic Kotlin, supports cancellation between emissions.
// Mutex prevents concurrent generate() calls (e.g., from screen rotation re-collecting).
fun generate(prompt: String): Flow<String> = flow {
    llmMutex.withLock {
        val model = llmModel ?: throw IllegalStateException("Model not initialized")
        model.cleanUp() // Reset KV cache for new conversation
        model.run(prompt)

        while (currentCoroutineContext().isActive) {
            val result: LLMNextTokenResult = model.waitForNextToken()
            if (result.status != 0) break
            emit(result.token)
        }
    }
}.flowOn(Dispatchers.IO)

// Cleanup
fun close() {
    llmModel?.deinit()
    llmModel = null
}
```

**Cancellation note:** `waitForNextToken()` is a blocking JNI call — `Job.cancel()` cannot interrupt it mid-block. Cancellation takes effect after the current token returns, when `flow {}` checks `isActive` before the next `emit()`. For instant stop, check if the SDK's model exposes a `cancel()` or `stop()` method.

**LLM Quantization Types:** `GGUF_QUANT_ORG`, `GGUF_QUANT_F16`, `GGUF_QUANT_BF16`, `GGUF_QUANT_Q8_0`, `GGUF_QUANT_Q6_K`, `GGUF_QUANT_Q4_K_M`, `GGUF_QUANT_Q3_K_M`, `GGUF_QUANT_Q2_K`

**LLM KV Cache Policies:** `CLEAN_UP_ON_FULL` (default), `DO_NOT_CLEAN_UP`

### iOS (Swift)

```swift
import ZeticMLange

actor LLMModelActor {
    private var model: ZeticMLangeLLMModel?

    // Model downloads weights on first run (~700MB for LLMs).
    // Pass onDownload to show progress to the user.
    func initialize(personalKey: String, name: String,
                    onDownload: ((Float) -> Void)? = nil) throws {
        model = try ZeticMLangeLLMModel(personalKey: personalKey, name: name,
            target: .LLAMA_CPP, quantType: .GGUF_QUANT_Q4_K_M,
            onDownload: onDownload)
    }

    /// Returns an AsyncStream of tokens. Call from any async context.
    /// Note: waitForNextToken() blocks its thread — cancellation takes effect
    /// after the current token returns, not mid-block.
    func chat(prompt: String) throws -> AsyncStream<String> {
        guard let model else { throw ZeticMLangeError("ModelNotInitialized", "Call initialize() before using the model") }
        try model.cleanUp()
        let _ = try model.run(prompt)

        return AsyncStream { continuation in
            while true {
                let result = model.waitForNextToken()
                if result.isFinished || Task.isCancelled {
                    continuation.finish()
                    break
                }
                continuation.yield(result.token)
            }
        }
    }

    func cleanup() {
        model?.forceDeinit()
        model = nil
    }
}

// --- Usage in a @MainActor ViewModel ---

@Observable
@MainActor
final class ChatViewModel {
    private(set) var response = ""
    private let llmActor = LLMModelActor()
    private var generateTask: Task<Void, Error>?

    func send(prompt: String) async throws {
        response = ""
        let stream = try await llmActor.chat(prompt: prompt)
        for await token in stream {
            response += token  // @MainActor — safe to update UI
        }
    }

    // Call explicitly from .onDisappear — do NOT rely on deinit for cleanup.
    // deinit is synchronous; Task {} inside it is fire-and-forget with no guarantee of execution.
    func teardown() async {
        generateTask?.cancel()
        await llmActor.cleanup()
    }
}
```

---

## HuggingFace Model Loading (ZeticMLangeHFModel)

### Android (Kotlin)

```kotlin
import com.zeticai.mlange.core.model.ZeticMLangeHFModel

// Load from HuggingFace repo (public)
val model = ZeticMLangeHFModel(context, "username/repo-name")

// With access token (private repos)
val model = ZeticMLangeHFModel(context, "username/repo-name",
    userAccessToken = "hf_your_token")

val outputs = model.run(inputTensors)
model.close()
```

### iOS (Swift)

```swift
import ZeticMLange

let model = try await ZeticMLangeHFModel("username/repo-name",
    userAccessToken: "hf_your_token")
let outputs = try model.run(inputs: inputTensors)
```

Note: iOS HF model loading is `async` — use `await`.

---

## Common Patterns

### Pipeline (e.g., Face Detection → Emotion Recognition)

```kotlin
// Both models serialized by running on Dispatchers.IO within a single coroutine
suspend fun detectEmotion(bitmap: Bitmap): EmotionResult = withContext(Dispatchers.IO) {
    // Step 1: Detect faces
    val detectionOutputs = detectionModel.run(preprocessedImage)

    // Step 2: Extract face region
    val faceRegion = extractFaceRegion(bitmap, detectionOutputs)

    // Step 3: Classify emotion
    val emotionOutputs = emotionModel.run(faceRegion)
    parseEmotionResult(emotionOutputs)
}
```

### Encoder-Decoder (e.g., Whisper)

```kotlin
val encoder = ZeticMLangeModel(context, personalKey, "OpenAI/whisper-tiny-encoder")
val decoder = ZeticMLangeModel(context, personalKey, "OpenAI/whisper-tiny-decoder")

val encoderOutputs = encoder.run(melSpectrogramInputs)
// Feed encoder outputs into decoder
val decoderOutputs = decoder.run(arrayOf(decoderInputIds, encoderOutputs[0], attentionMask))
```

---

## Hardware Targets (General Models)

| Target | Description |
|--------|-------------|
| TFLITE_FP32/FP16/QUANT | TensorFlow Lite backends |
| ORT / ORT_NNAPI | ONNX Runtime (with optional NNAPI) |
| QNN / QNN_FP16 / QNN_QUANT | Qualcomm Neural Network |
| COREML / COREML_FP32 / COREML_QUANT | Apple CoreML |
| NEUROPILOT / NEUROPILOT_QUANT | MediaTek NeuroPilot |
| EXYNOS / EXYNOS_QUANT | Samsung Exynos |
| KIRIN / KIRIN_QUANT | Huawei Kirin |
| LITERT_FP32/FP16/QUANT | Google LiteRT |

`ModelMode.RUN_AUTO` automatically selects the best target for the device.

---

## Platform Notes

- **Progress callback naming:** Android uses `onProgress: ((Float) -> Unit)?`, iOS uses `onDownload: ((Float) -> Void)?`. Same behavior, different parameter names.
- **Error handling:** `model.run()` throws `ZeticMLangeException` (Android) or is marked `throws` (iOS) on input size mismatch and other failures. Wrap in try/catch in production code.
- **Actor blocking (iOS):** `waitForNextToken()` blocks the actor's serial executor. This is fine for a dedicated model actor, but don't add unrelated methods to the same actor — they'll be blocked until token generation finishes.

---

## Troubleshooting

- **ANR / App Not Responding**: You called `model.run()` or constructor on the main thread. All SDK calls are blocking — always use a background dispatcher.
- **Native crash / SIGSEGV**: Likely concurrent `run()` calls on the same model. Use a `Mutex` + `Dispatchers.IO` (Android) or an actor (iOS) to serialize access — one inference at a time per model instance.
- **Memory leak / NPU unavailable**: Forgot to call `model.close()` / `deinit()` / `forceDeinit()` in lifecycle callbacks.
- **Micro-stutters in real-time apps**: Allocating new Tensor/ByteBuffer objects per frame. Pre-allocate with `getInputBuffers()` and reuse.
- **Wrong input size error**: Ensure `inputs.size` matches the model's expected input count.
- **Target not supported**: Some targets require specific hardware (e.g., QNN = Qualcomm SoC, CoreML = Apple).
- **NPU access on Free tier**: NPU is only available on Samsung S25/S25 Ultra in Free tier; Pro tier unlocks all.
- **Model name format**: Must be `"account_name/project_name"` — throws `ZeticMLangeException` otherwise.
- **LLM produces stale/mixed output**: Forgot to call `cleanUp()` before starting a new conversation. Always reset KV cache between sessions.

## Demo Model Keys (for testing)

- `"face_detection"` — Face detection
- `"face_landmark"` — Face landmark
- `"deepseek-r1-distill-qwen-1.5b-f16"` — LLM demo
- `"Steve/YOLOv11_comparison"` — Object detection
- `"OpenAI/whisper-tiny-encoder"` / `"OpenAI/whisper-tiny-decoder"` — Speech recognition
