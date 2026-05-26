"""把剪贴板图片保存到文件，然后用 vision skill 分析"""
import sys
from PIL import ImageGrab

OUTPUT = "d:/软件设计/clipboard.png"

img = ImageGrab.grabclipboard()
if img is None:
    print("剪贴板里没有图片！先截图 (Win+Shift+S 或 PrintScreen)")
    sys.exit(1)

img.save(OUTPUT)
print(f"图片已保存: {OUTPUT}")

# 如果有传入 prompt，直接调 vision 分析
if len(sys.argv) > 1:
    import subprocess
    prompt = " ".join(sys.argv[1:])
    subprocess.run([
        "python", "C:/Users/baimixiaofan/.claude/skills/vision/vision.py",
        OUTPUT, prompt
    ])
