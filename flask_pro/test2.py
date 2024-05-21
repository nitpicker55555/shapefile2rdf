from datetime import datetime

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sys
import io
import base64
import matplotlib.pyplot as plt

code = """
import matplotlib.pyplot as plt

x = [1, 2, 3, 4]
y = [10, 20, 25, 30]

plt.plot(x, y)
plt.title("Sample Plot")
plt.xlabel("x-axis")
plt.ylabel("y-axis")
plt.show()
"""
old_stdout = sys.stdout
sys.stdout = mystdout = io.StringIO()
plt.figure()  # Ensure a new figure is created for each execution
image_path = None
try:
    exec(code)
except Exception as e:
    result = str(e)
else:
    result = mystdout.getvalue()
    if plt.get_fignums():  # Check if a figure has been created
        image_filename = 'plot.png'
        filename = f"plot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
finally:
    sys.stdout = old_stdout