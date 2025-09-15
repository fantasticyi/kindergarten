from app import create_app, db
from flask_cors import CORS

app = create_app("develop")

# 用CORS（跨域资源共享）支持，允许跨域请求
CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)


@app.route('/')
def home():
    return "Hello, World!"  # 确保有返回值


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
