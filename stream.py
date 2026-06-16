import subprocess, os

def start_stream():
    if not os.path.exists("video.mp4"):
        print("حط video.mp4 في المشروع")
        return

    STREAM_KEY = os.environ.get("STREAM_KEY")
    if not STREAM_KEY:
        print("STREAM_KEY ناقص في Secrets")
        return

    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", "video.mp4",
        "-c:v", "libx264", "-preset", "ultrafast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k", "-pix_fmt", "yuv420p",
        "-g", "60", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
    ]

    while True:
        try:
            subprocess.run(cmd, check=True)
        except: pass