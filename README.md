# Studio Lighting & Turntable Rig for Blender

> An AI-assisted viewport utility that measures arbitrary 3D mesh bounds and automatically builds a production-ready studio backdrop, balanced 3-point light rig, 100mm product camera, and turntable loop.

<!-- DRAG AND DROP YOUR GIF HERE -->
![Studio Setup Demo](https://via.placeholder.com/800x450.png?text=Drag+and+Drop+Your+Demo+GIF+Here)

---

## 📌 Project Overview & Purpose

In product design and 3D look-development, setting up presentation stages is repetitive and time-consuming. An artist repeatedly scales cycloramas, adjusts key/fill/rim light balance, aligns camera focal lengths, and keyframes linear turntables across dozens of asset iterations.

This project was built to automate that staging pipeline down to a single click, developed as a case study in **Technical Art Direction and LLM-Assisted Tool Development**.

---

## ✨ Key Features

* **Dynamic Bounding-Box Math:** Reads the active mesh's world-space transformation matrix and dimensions (`bound_box`) to dynamically scale lighting distance, backdrop sweep, and camera framing for any model regardless of scale.
* **Balanced 3-Point Light Rig:** Automatically spawns Key (warm, key angle), Fill (cool, soft diffusion), and Rim (hair/accent) area lights linked to a central tracking empty.
* **100mm Telephoto Camera:** Spawns a 100mm front-facing camera with automatic Depth of Field (DoF) focused cleanly on the target object.
* **Live Sidebar Controls (N-Panel):** Includes real-time update callbacks for backdrop color, surface roughness, and master light intensity—allowing artists to tweak look-dev interactively without rebuilding the scene.
* **1-Click 360° Turntable Loop:** Generates a seamless 120-frame linear rotation loop, automatically configuring timeline bounds and interpolation.

---

## 🧠 AI / LLM Implementation & Technical Problem Solving

This add-on was developed by translating production requirements into targeted architectural prompts for Large Language Models, followed by iterative visual QA and runtime debugging:

1. **Pipeline Architecture & Constraint Scoping:**
   * Defined strict technical constraints for the LLM: non-destructive scene generation, undo-stack preservation (`bl_options = {'REGISTER', 'UNDO'}`), and dedicated scene collection organization.
2. **Visual QA & Iterative Refinement:**
   * Viewport testing revealed lighting overexposure and geometric clipping between the curved cyclorama wall and the rim light.
   * Directed targeted prompt revisions to recalibrate the wattage falloff formula and extend cyclorama depth clearance proportionally.
3. **Cross-Version API Debugging:**
   * When implementing the turntable loop, Blender's updated animation system threw an unhandled runtime error:
     ```
     AttributeError: 'Action' object has no attribute 'fcurves'
     ```
   * Diagnosed the root cause: Blender’s transition toward **Slotted / Layered Actions**.
   * Guided the LLM to design a defensive traversal loop checking both legacy `action.fcurves` and modern `action.layers[].strips[].channelbags[].fcurves`, alongside temporary preference overrides (`LINEAR` keyframe defaults) to guarantee cross-version compatibility.

---

## 🛠️ Installation

1. Download the [`studio_lighting_kit.py`](./studio_lighting_kit.py) file from this repository.
2. Open Blender (v4.0 or newer).
3. Go to **Edit > Preferences > Add-ons**.
4. Click the dropdown arrow / **Install from Disk...** in the top right.
5. Select `studio_lighting_kit.py` and ensure the checkbox next to **Studio Backdrop & Light Rig** is enabled.
6. In any 3D Viewport, press **`N`** on your keyboard and find the **Studio Setup** tab.

---

## 💻 Tech Stack & Compatibility

* **Language:** Python (`bpy`, `mathutils`)
* **Software:** Blender 4.0+
* **License:** GNU General Public License v3.0
