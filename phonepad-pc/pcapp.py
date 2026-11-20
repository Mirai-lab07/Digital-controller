import asyncio, json, os, socket, sys, threading
import tkinter as tk
from aiohttp import web
import vgamepad as vg

PORT = 8080
state = {"clients": 0, "error": ""}

def res(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def server_thread():
    try:
        pad = vg.VX360Gamepad()
    except Exception as e:
        state["error"] = "Driver ViGEmBus belum install"
        return

    B = vg.XUSB_BUTTON
    BTN = {
        "A": B.XUSB_GAMEPAD_A, "B": B.XUSB_GAMEPAD_B,
        "X": B.XUSB_GAMEPAD_X, "Y": B.XUSB_GAMEPAD_Y,
        "LB": B.XUSB_GAMEPAD_LEFT_SHOULDER, "RB": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "START": B.XUSB_GAMEPAD_START, "BACK": B.XUSB_GAMEPAD_BACK,
        "UP": B.XUSB_GAMEPAD_DPAD_UP, "DOWN": B.XUSB_GAMEPAD_DPAD_DOWN,
        "LEFT": B.XUSB_GAMEPAD_DPAD_LEFT, "RIGHT": B.XUSB_GAMEPAD_DPAD_RIGHT,
    }

    async def index(request):
        return web.FileResponse(res("index.html"))

    async def ws_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        state["clients"] += 1
        try:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                try:
                    d = json.loads(msg.data)
                    t = d["t"]
                    if t == "btn":
                        (pad.press_button if d["down"] else pad.release_button)(BTN[d["b"]])
                    elif t == "stick":
                        if d["s"] == "L": pad.left_joystick_float(d["x"], d["y"])
                        else: pad.right_joystick_float(d["x"], d["y"])
                    elif t == "trig":
                        if d["s"] == "L": pad.left_trigger_float(d["v"])
                        else: pad.right_trigger_float(d["v"])
                    pad.update()
                except Exception:
                    pass
        finally:
            state["clients"] -= 1
            pad.reset()
            pad.update()
        return ws

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    loop.run_until_complete(web.TCPSite(runner, "0.0.0.0", PORT).start())
    loop.run_forever()

threading.Thread(target=server_thread, daemon=True).start()

root = tk.Tk()
root.title("PhonePad")
root.geometry("360x210")
root.resizable(False, False)
tk.Label(root, text="Masukkan IP ni kat app phone:", font=("Segoe UI", 11)).pack(pady=(18, 0))
tk.Label(root, text=local_ip(), font=("Segoe UI", 28, "bold")).pack()
status = tk.Label(root, font=("Segoe UI", 12))
status.pack(pady=8)
tk.Label(root, text=f"Port {PORT}  •  Phone & PC kena sama WiFi", fg="gray").pack()

def refresh():
    if state["error"]:
        status.config(text=state["error"], fg="red")
    elif state["clients"] > 0:
        status.config(text="● Phone connected", fg="green")
    else:
        status.config(text="○ Tunggu phone connect...", fg="gray")
    root.after(500, refresh)

refresh()
root.mainloop()