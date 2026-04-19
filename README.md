# Deep Learning Based Technique for Animal Detection on Railway Track

## Structure

Project folders/files after cleanup:

```text
.
|-- backend/
|   `-- detection_backend.py
|-- frontend/
|   |-- run.py
|   `-- ui_frontend.py
|-- input_images/        (local only, not uploaded)
|-- input_video/         (local only, not uploaded)
|-- output_images/       (local generated, not uploaded)
|-- output_videos/       (local generated, not uploaded)
|-- yolov8x.pt           (local model file, not uploaded)
|-- .env                 (local secrets, not uploaded)
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## Upload Scope (GitHub)

Upload only required project files:

- `frontend/`
- `backend/`
- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`

Do NOT upload:

- `main/`
- `input_images/`
- `input_video/`
- `output_images/`
- `output_videos/`
- `yolov8x.pt`
- `backend/yolov8x.pt`
- `.env`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create environment file:

```bash
copy .env.example .env
```

4. Keep local folders ready for runtime data:

```bash
mkdir input_images input_video output_images output_videos
```

## Run

Run the app from project root:

```bash
python frontend/run.py
```
