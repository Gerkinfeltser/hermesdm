# SPEC: Image System Fix + Fallback Chain

## Problem Statement
The image generation system has 5 critical issues:
1. **Bug**: `image_result.provider_used` does not exist (should be `provider`)
2. **Split architecture**: `cmd_imagen` uses subprocess + script, auto-gen uses `ImageEventHandler` — they don't share code or provider config
3. **No fallback**: If Pollinations fails/times out, no alternative provider is tried
4. **Settings ignored**: `_maybe_send_scene_image` bypasses `settings.image_generation`
5. **No retry**: Single attempt with 60s timeout, no recovery

## Goals
- Single unified image generation pipeline
- Automatic fallback chain: Pollinations → fal.ai → MiniMax
- Respect `settings.image_generation` toggle
- Retry with shorter timeout per provider
- Keep working if 0-2 providers are available

## Non-Goals
- Adding new providers (use existing 5)
- Changing image quality/prompt logic
- UI changes beyond bug fixes

## Architecture

```
FallbackImageProvider(primary, fallbacks[])
  ├─ try primary.generate() with retry=2, timeout=15s
  ├─ on fail: try fallback[0].generate() with retry=2, timeout=15s
  ├─ on fail: try fallback[1].generate() with retry=2, timeout=15s
  └─ return first success or raise ImageGenerationError

cmd_imagen()
  └─ uses _get_image_handler() → same pipeline as auto-gen

_maybe_send_scene_image()
  └─ checks settings.image_generation first
  └─ uses _get_image_handler() with FallbackImageProvider
```

## Implementation Plan

### 1. dm/image_provider.py — Add FallbackProvider
- New class `FallbackImageProvider(ImageProvider)`
- Accepts `primary: ImageProvider` + `fallbacks: list[ImageProvider]`
- Implements `async generate()` with retry loop
- Per-provider timeout: 15s (was 60s)
- Retry count: 2 per provider

### 2. bot/telegram_handler.py — Fix cmd_imagen
- Remove subprocess call to `image_from_scene.py`
- Use `_get_image_handler().provider.generate(prompt, scene_type)`
- Build prompt from narrative/location same as before
- Use `ImageEventHandler` for consistent prompt building

### 3. bot/telegram_handler.py — Fix _maybe_send_scene_image
- Check `settings.image_generation` before generating
- Fix `provider_used` → `provider`
- Use same `_get_image_handler()` singleton

### 4. bot/telegram_handler.py — Fix _get_image_handler
- Build `FallbackImageProvider`:
  - Primary: Pollinations (free, fast when works)
  - Fallback 1: fal.ai (if FAL_KEY env var present)
  - Fallback 2: MiniMax (if MINIMAX_API_KEY present)
- Environment var `IMAGE_PROVIDER` still works for single-provider mode

## Files Modified
- `dm/image_provider.py` — Add FallbackProvider
- `bot/telegram_handler.py` — Fix cmd_imagen, _maybe_send_scene_image, _get_image_handler

## Verification
- [ ] `cmd_imagen` generates image via unified pipeline
- [ ] Auto-generation after `/j` nat20 generates image
- [ ] If Pollinations fails, falls back to next available provider
- [ ] `settings.image_generation=false` blocks all generation
- [ ] No subprocess calls remain in image path

## Rollback
- Revert two files, restart bot
- Previous subprocess-based `cmd_imagen` would be restored
