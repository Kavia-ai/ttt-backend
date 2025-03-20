from app import create_app
from app.config import config

app = create_app('development')  # Using development config by default

if __name__ == '__main__':
    app.run(
        host=config['development'].HOST,
        port=5010,  # Fixed port as per requirements
        debug=config['development'].DEBUG
    )
