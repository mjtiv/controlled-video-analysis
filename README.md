# controlled-video-analysis

Deterministic video analysis pipeline using frame extraction + structured AI classification.

Designed for **auditability, reproducibility, and real-world workflows** such as legal review, forensic analysis, and large-scale video inspection.

---

## 🚀 Overview

This project demonstrates a **controlled, inspectable AI pipeline** for analyzing video content.

Instead of treating AI as a black box, this system:
- breaks video into **timestamped frames**
- analyzes each frame independently using a **strict schema**
- produces **structured, auditable outputs**
- tracks **token usage and cost**

The result is a pipeline that is:
- reproducible
- debuggable
- suitable for environments where **traceability matters**

---

## 🧠 Core Idea

Most AI video analysis tools:
- provide high-level summaries
- lack transparency
- cannot be easily verified

This pipeline takes the opposite approach:

> Every decision is tied to a specific frame, timestamp, and structured output.

---

## 🔄 Pipeline Architecture

Video Input (.mp4)  
↓  
Frame Extraction (timestamped)  
↓  
Per-Frame AI Classification  
↓  
Structured JSON Output  
↓  
CSV Conversion (human-readable)

---

## ⚙️ Features

- 🎥 Controlled frame sampling (`sample_fps`)
- 🧾 Timestamp-linked metadata
- 🤖 Schema-enforced AI responses (strict JSON)
- 🔁 Deterministic processing loop
- 💰 Token usage + cost tracking
- 📊 CSV export for Excel workflows

---

## 📸 Sample Frames

(See `sample_outputs/frames/` for examples)

---

## 📊 Sample Outputs

- JSON: `sample_outputs/analysis_results.json`
- CSV: `sample_outputs/analysis_results_table.csv`

---

## 🧪 Use Case

Detect whether a **bright green sedan** appears in each frame.

Adaptable to:
- object detection
- event detection
- forensic review
- medical or industrial imaging

---

## ⚖️ Why This Matters

Supports:
- auditability
- reproducibility
- explainable AI outputs

---

## 🛠️ Setup

Install dependencies:

```bash
pip install opencv-python python-dotenv openai
```

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_key_here
```

> The script loads environment variables using `python-dotenv`, so the `.env` file must be in the working directory.

---

## ▶️ Run

```bash
python Agent_Video_Processor_1.4.py
```

---

## 🔐 Alternative: Environment Variable

If you prefer not to use a `.env` file, you can set the API key directly:

```bash
# macOS / Linux
export OPENAI_API_KEY=your_key_here

# Windows (PowerShell)
setx OPENAI_API_KEY "your_key_here"
```
---

## 📁 Structure

controlled-video-analysis/
├── Agent_Video_Processor_1.4.py
├── README.md
├── sample_outputs/
│   ├── analysis_results.json
│   ├── analysis_results_table.csv
│   └── frames/
│       ├── frame_000_t0.00.jpg
│       ├── frame_001_t1.00.jpg
│       ├── frame_002_t2.00.jpg
│       ├── frame_003_t3.00.jpg
│       ├── frame_004_t4.00.jpg
│       ├── frame_005_t5.00.jpg
│       ├── frame_006_t6.00.jpg
│       ├── frame_007_t7.00.jpg
│       ├── frame_008_t8.00.jpg
│       ├── frame_009_t9.00.jpg
│       └── frame_010_t10.00.jpg
├── green_car_video_clip.mp4

---

## 🧠 Design Philosophy

AI should be **controlled, inspectable, and accountable** — not a black box.

---

## 📄 License

MIT License
