import io
import contextlib
import matplotlib.pyplot as plt
import plotly.io as pio
import os
import uuid
import math

from ..utils import random_6_digit_id

def execute_code(code):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        try:
            # Bug fixed: https://stackoverflow.com/questions/29979313/python-weird-nameerror-name-is-not-defined-in-an-exec-environment
            exec(code, globals())
        except Exception as e:
            print(f"Error: {e}")
    output = buffer.getvalue()
    buffer.close()
    return output

class CodeExecutor:
    def __init__(self, output_dir='output'):
        self.output = None
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def execute_code(self, code):
        self.output = execute_code(code)
        return self

    def get_output(self):
        return self.output

    def save_matplotlib_plot(self, code):
        file_path = os.path.join(self.output_dir, f'{random_6_digit_id()}.png')
        exec(code)
        plt.savefig(file_path)
        plt.close()
        return file_path

    def save_plotly_plot(self, code):
        file_path = os.path.join(self.output_dir, f'{random_6_digit_id()}.html')
        fig = exec(code)
        pio.write_html(fig, file_path)
        return file_path