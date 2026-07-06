import gc

import torch

from modules.script_callbacks import on_ui_settings, on_ui_tabs, on_after_component
from modules.shared import opts, OptionInfo
from modules import scripts

import gradio as gr
from modules.ui_components import ToolButton

# Tool buttons (one per generation tab) are injected next to the paste / clear
# / apply-styles icons in the row below the Generate button.
_TOOLS_ANCHORS = ("txt2img_style_apply", "img2img_style_apply")

# Neo Forge exposes its memory helpers under backend.memory_management.
# Fall back to the classic Forge path and finally to a bare torch cleanup so
# the extension keeps working regardless of the WebUI flavor.
try:
    from backend.memory_management import (
        soft_empty_cache,
        unload_all_models,
        get_torch_device,
        get_free_memory,
    )
except ImportError:
    try:
        from ldm_patched.modules.model_management import (
            soft_empty_cache,
            unload_all_models,
            get_torch_device,
            get_free_memory,
        )
    except ImportError:

        def soft_empty_cache(force=False):
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

        def unload_all_models():
            # No model registry available on this backend; the caller will
            # still run gc + empty_cache which is the best we can do here.
            pass

        def get_torch_device():
            return None

        def get_free_memory(dev=None, torch_free_too=False):
            return 0


def _debug(*args):
    if getattr(opts, "memre_debug", False):
        print("[Memory Release]", *args)


def _free_mb(dev):
    """Free VRAM on `dev` in MB (best-effort, 0 on failure)."""
    try:
        return get_free_memory(dev) / (1024 * 1024)
    except Exception:
        return 0.0


class MemRel(scripts.Script):

    def title(self):
        return "Memory Release"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def postprocess(self, *args, **kwargs):
        MemRel.mem_release()

    @staticmethod
    def mem_release():
        """Light cleanup after every generation.

        Runs a Python garbage collection and empties the CUDA cache without
        unloading models, so the next generation does not pay a reload cost.
        """
        if not getattr(opts, "memre_auto", True):
            return
        try:
            gc.collect()
            soft_empty_cache()
        except Exception as e:
            _display(e)
        else:
            _debug("Cache emptied")


def _free_vram():
    """Unload every model from VRAM, collect garbage, empty the CUDA cache, and
    report how much was freed. This actually frees VRAM (at the cost of a model
    reload on the next generation) so you can switch to another GPU app without
    closing the WebUI.

    Shows a toast and returns the status string (used by the tab's status box).
    """
    try:
        dev = get_torch_device()
        before = _free_mb(dev)

        unload_all_models()
        gc.collect()
        try:
            soft_empty_cache(force=True)
        except TypeError:
            # Older backends have no `force` argument.
            soft_empty_cache()

        after = _free_mb(dev)
    except Exception as e:
        _display(e)
        msg = "❌ Memory Release failed - see console"
    else:
        freed = after - before
        msg = f"✅ VRAM freed: {freed:.0f} MB (now {after:.0f} MB free)"
        _debug(msg)

    gr.Info(msg)
    return msg


def _vram_status():
    """Current free VRAM as a status string."""
    try:
        free = _free_mb(get_torch_device())
        return f"Free VRAM: {free:.0f} MB"
    except Exception:
        return "Free VRAM: unknown"


def on_mem_tab():
    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown("## 🧹 Memory Release")
        gr.Markdown(
            "Unload all models from VRAM on demand — so you can use other GPU "
            "apps (LM Studio, games, ...) **without closing the WebUI**. "
            "Models reload automatically on your next generation."
        )
        status = gr.Textbox(
            label="Status",
            value=_vram_status,
            interactive=False,
            elem_id="memre_tab_status",
        )
        with gr.Row():
            free_button = gr.Button(
                value="🧹 Unload Models (Free VRAM)",
                variant="primary",
                elem_id="memre_tab_btn",
            )
            refresh_button = gr.Button(
                value="🔄 Refresh",
                elem_id="memre_tab_refresh",
            )
        free_button.click(fn=_free_vram, outputs=[status], queue=False)
        refresh_button.click(fn=_vram_status, outputs=[status], queue=False)

    return [(tab, "Memory Release", "memre_tab")]


def _display(e):
    if getattr(opts, "memre_debug", False):
        from modules.errors import display

        display(e, "Memory Release")


def on_mem_settings():
    opts.add_option(
        "memre_auto",
        OptionInfo(
            True,
            "Memory Release - Auto cleanup after each generation",
            section=("system", "System"),
            category_id="system",
        ),
    )
    opts.add_option(
        "memre_debug",
        OptionInfo(
            False,
            "Memory Release - Debug",
            section=("system", "System"),
            category_id="system",
        ),
    )


def on_mem_after_component(component, **kwargs):
    """Inject a 🧹 tool button into the row below the Generate button."""
    elem_id = kwargs.get("elem_id")
    if elem_id not in _TOOLS_ANCHORS:
        return

    tab = elem_id.split("_", 1)[0]  # "txt2img" / "img2img"
    btn = ToolButton(
        value="🧹",
        elem_id=f"{tab}_memre_toolbtn",
        tooltip="Unload all models from VRAM (free it for other apps). "
        "Models reload on the next generation.",
    )
    btn.click(fn=_free_vram, queue=False)


on_ui_settings(on_mem_settings)
on_ui_tabs(on_mem_tab)
on_after_component(on_mem_after_component)
