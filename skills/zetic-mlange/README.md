# ZETIC Melange (MLange) SDK Skill for Claude Code

![Status](https://img.shields.io/badge/status-untested-yellow)

A skill that enables Claude Code to integrate the ZETIC Melange on-device AI SDK into Android (Kotlin/Java) and iOS (Swift) mobile applications with correct concurrency, lifecycle management, and hardware-optimized inference.

## Overview

This skill provides Claude with comprehensive knowledge of the ZETIC Melange SDK, including:

- **General Model Inference** with `ZeticMLangeModel` for vision, audio, and custom models
- **LLM Inference** with `ZeticMLangeLLMModel` for streaming token generation on-device
- **HuggingFace Model Loading** with `ZeticMLangeHFModel` for public and private repos
- **Threading & Concurrency** rules — all SDK calls are synchronous/blocking and require background dispatch
- **Hardware Targets** — NPU, GPU, and CPU backends across Qualcomm, Apple, MediaTek, Samsung, and more
- **Real-time Patterns** — zero-allocation hot loops, drop-frame strategies, pipeline and encoder-decoder architectures

## Installation

1. Copy the skill to your Claude Code skills directory:
   ```bash
   cp -r skills/zetic-mlange ~/.claude/skills/
   ```

2. Claude Code will automatically detect and load the skill in your next session.

## Usage

The skill automatically activates when you mention ZETIC, MLange, Melange, or related SDK classes. Simply ask Claude to:

- "Integrate ZeticMLangeModel for on-device object detection"
- "Add LLM chat with streaming tokens using ZeticMLangeLLMModel"
- "Load a HuggingFace model on-device with ZeticMLangeHFModel"
- "Set up a real-time camera inference pipeline with NPU acceleration"
- "Deploy a Whisper encoder-decoder model to mobile"

Claude will follow the SDK's threading rules, lifecycle patterns, and platform-specific best practices.

## Project Structure

```
zetic-mlange/
├── SKILL.md        # Main skill definition with API reference and patterns
└── README.md       # This file
```

## Key Concepts

### Threading Rules

All MLange SDK calls are **synchronous and blocking** — they interface directly with native hardware (NPU/GPU/CPU). The skill enforces six critical rules:

1. **Never call on the main/UI thread** — use `Dispatchers.IO` (Android) or actors (iOS)
2. **Single-consumer access** — serialize with `Mutex` (Android) or actors (iOS)
3. **Lifecycle-aware cleanup** — close models in `onCleared()` / `.onDisappear`
4. **Zero-allocation in hot loops** — pre-allocate buffers for real-time inference
5. **Drop-frame strategy** — skip frames when the model is busy
6. **Reset state between sessions** — call `cleanUp()` before new LLM conversations

### Supported Model Types

| Type | Class | Use Case |
|------|-------|----------|
| General | `ZeticMLangeModel` | Vision, audio, custom models |
| LLM | `ZeticMLangeLLMModel` | On-device text generation with GGUF quantization |
| HuggingFace | `ZeticMLangeHFModel` | Load models directly from HuggingFace repos |

### Hardware Targets

Supports automatic target selection (`ModelMode.RUN_AUTO`) and explicit targets including TFLite, ONNX Runtime, Qualcomm QNN, Apple CoreML, MediaTek NeuroPilot, Samsung Exynos, Huawei Kirin, and Google LiteRT.

## Resources

- [ZETIC Melange Dashboard](https://melange.zetic.ai)
- [ZETIC Documentation](https://docs.zetic.ai)
- [ZETIC GitHub](https://github.com/zetic-ai)
- Contact: contact@zetic.ai

## License

This project is licensed under the MIT License - see the LICENSE file for details.
