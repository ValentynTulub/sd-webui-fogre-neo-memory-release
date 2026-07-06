# SD WebUI Forge Neo — Memory Release

An extension for **Stable Diffusion WebUI Forge (Neo)** that frees VRAM on demand — so you can unload models and switch to another GPU app (LM Studio, a game, ...) **without closing the WebUI**.

> **Fork note:** This is a fork of [Haoming02/sd-webui-memory-release](https://github.com/Haoming02/sd-webui-memory-release), which was written for the [Automatic1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui). It has been rewritten to target Forge Neo's `backend.memory_management` API and to actually unload models from VRAM (not just empty the CUDA cache).

### But Why?
- CUDA holds on to cached memory and loaded models, keeping VRAM occupied after a generation. This extension frees it back up whenever you want.

### Features
- **`🧹` tool button** in the row below **Generate** (next to the paste / clear / apply-styles icons), in both txt2img and img2img. One click unloads every model from VRAM. A toast reports how much was freed; models reload automatically on your next generation.
- **Dedicated `Memory Release` tab** (in the top tab bar) with the same action plus a live free-VRAM readout and a refresh button.
- **Automatic** light cleanup after every generation: `gc.collect()` + `soft_empty_cache()` (empties the CUDA cache without unloading models, so the next generation isn't slowed down).

### Typical workflow
1. Finish your generations in Forge Neo.
2. Click the **`🧹`** button below **Generate** (or use the **Memory Release** tab).
3. A toast shows how much VRAM was freed — go run LM Studio, a game, etc.
4. Come back and generate as usual; Forge reloads the model on the next run.

### Settings
Under **Settings → System**:
- `Memory Release - Auto cleanup after each generation` — toggle the automatic light cleanup (on by default).
- `Memory Release - Debug` — print/report cleanup status and errors.

### Installation
1. Go to the **Extensions → Install from URL** tab in Forge Neo and paste:
   ```
   https://github.com/ValentynTulub/sd-webui-fogre-neo-memory-release
   ```
   ...or clone it manually into your `extensions` folder:
   ```
   git clone https://github.com/ValentynTulub/sd-webui-fogre-neo-memory-release extensions/sd-webui-memory-release
   ```
2. Restart the WebUI.

### Credits
- Original extension by [Haoming02](https://github.com/Haoming02/sd-webui-memory-release) (MIT).
- <sup>Shout out to [@kgmkm_mkgm](https://twitter.com/kgmkm_mkgm/status/1658760768958140418) for sharing the original extension with tens of thousands of people.</sup>
- <sup>Apparently, this indeed does help in [certain situations](https://github.com/Haoming02/sd-webui-memory-release/issues/3).</sup>
