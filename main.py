import sys

from flask import Flask
import qform

app = qform.app

if __name__ == "__main__":
    try:
        app.run()
    finally:
        if 'upload_dir' in app.config:
            app.config['upload_dir'].cleanup()

    #app.run(host="0.0.0.0", debug=True, port=80)