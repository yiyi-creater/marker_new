from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for, Response
import csv
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

def render_with_files(message):
    history_files = [f.name for f in SAVE_DIR.glob("daily_log_*.csv")]
    return render_template_string(HTML_PAGE, message=message, history_files=history_files)

SAVE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 总记录文件（不分日期，始终追加）
CSV_FILE = SAVE_DIR / "mark_log.csv"
# 每日记录文件（按天存）

ERROR_FILE = SAVE_DIR / "error_log.txt"

from datetime import timedelta

# 初始化文件头
now_dt = datetime.utcnow() + timedelta(hours=8)
today_file = SAVE_DIR / f"daily_log_{now_dt.strftime('%Y-%m-%d')}.csv"

for file in [CSV_FILE, today_file]:
    if not file.exists():
        with open(file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["mark_id", "timestamp", "is_simulated"])

current_id = 1

# 简单的用户名密码保护
USERNAME = "zjbci"
PASSWORD = "20250704"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        '需要登录才能访问此页面', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

HTML_PAGE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>打标 Web 客户端</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f8f9fa;
    }
    .container {
      max-width: 800px;
      margin: auto;
      padding: 2em 1em;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 1em;
    }
    h1 {
      text-align: center;
      font-size: 2em;
      margin-bottom: 1em;
    }
    form {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1em;
      background: white;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      width: 280px;
    }
    button {
      font-size: 1.2em;
      padding: 0.6em 1em;
      border-radius: 10px;
      border: none;
      margin-top: 0.5em;
      background-color: #007bff;
      color: white;
      cursor: pointer;
    }
    button:hover {
      background-color: #0056b3;
    }
    input[type="number"] {
      font-size: 1em;
      padding: 0.4em;
      margin: 0.5em 0;
      border-radius: 6px;
      border: 1px solid #ccc;
      width: 100%;
    }
    a {
      display: inline-block;
      text-align: center;
      margin-top: 0.5em;
      font-size: 1em;
      color: #007bff;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
    .log {
      text-align: center;
      font-size: 1.1em;
      color: #28a745;
      margin-top: 1em;
      width: 100%;
    }
    select {
      width: 100%;
      padding: 0.4em;
      margin-top: 0.5em;
      border-radius: 6px;
      border: 1px solid #ccc;
    }
  </style>
</head>
<body>
  <h1 style="text-align:center; font-size: 2em; padding-top: 1em;">打标 Web 客户端</h1>
  <div class="container" style="flex-wrap: wrap; justify-content: center; gap: 2em;">
  <h1>打标 Web 客户端</h1>
  <form action="/mark" method="post">
    <button type="submit" style="font-size: 2em; padding: 1em 2em; background-color: #28a745;">📍 打标</button>
</form>
<form action="/set_id" method="post">
    <input type="number" name="new_id" placeholder="设置起始 ID" required>
    <button type="submit">设置 ID</button>
</form>

  

  <form action="/clear_today" method="post">
    <button type="submit" style="background-color:#fd7e14;">🧹 清空今日记录</button>
</form>
<form action="/clear" method="post">
    <input type="password" name="confirm_password" placeholder="请输入密码确认" required style="margin-bottom:0.5em; padding:0.4em; width: 90%;">
    <button type="submit" style="background-color:#dc3545;">🗑 清空总记录</button>
</form>
<form action="/delete_last" method="post">
    <button type="submit" style="background-color:#ff8800;">撤销今日最后一条</button>
</form>
<form action="/download" method="get">
    <button type="submit" style="background-color:#007bff;">⬇ 下载总记录</button>
</form>
<form action="/download_today" method="get">
    <button type="submit" style="background-color:#17a2b8;">⬇ 下载今日记录</button>
</form>
  </div>
  <div class=\"log\">{{ message }}</div>

  
</body>
  </div>
<div class="container">
  <form action="/download_selected" method="post">
    <label style="margin-top: 1em; font-size: 1em;">选择要下载的日期（可多选）</label>
    <select name="dates" multiple size="5">
      {% for file in history_files %}
        <option value="{{ file }}">{{ file }}</option>
      {% endfor %}
    </select>
    <button type="submit" style="margin-top: 0.5em; background-color: #555;">⬇ 批量下载选中记录</button>
</form>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
@requires_auth
def index():
    history_files = [f.name for f in SAVE_DIR.glob("daily_log_*.csv")]
    return render_with_files("")

@app.route("/mark", methods=["POST"])
@requires_auth
def mark():
    global current_id
    from datetime import timedelta
    now_dt = datetime.utcnow() + timedelta(hours=8)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    daily_file = SAVE_DIR / f"daily_log_{now_dt.strftime('%Y-%m-%d')}.csv"

    try:
        for file in [CSV_FILE, daily_file]:
            if not file.exists():
                with open(file, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["mark_id", "timestamp", "is_simulated"])
            with open(file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([current_id, now, 0])

        msg = f"打标成功 | ID: {current_id} | 时间: {now}"
        current_id += 1
        return render_with_files(msg)
    except Exception as e:
        with open(ERROR_FILE, "a", encoding="utf-8") as ef:
            ef.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 打标失败: {e}
")
        return render_with_files(f"打标失败: {e}")

@app.route("/set_id", methods=["POST"])
@requires_auth
def set_id():
    global current_id
    try:
        new_id = int(request.form.get("new_id"))
        current_id = new_id
        msg = f"起始 ID 已设置为 {current_id}"
        return render_with_files(msg)
    except Exception as e:
        return render_with_files(f"设置 ID 失败: {e}")

@app.route("/download", methods=["GET"])
def download():
    if CSV_FILE.exists():
        return send_file(CSV_FILE, as_attachment=True)
    return "文件不存在", 404

@app.route("/download_today", methods=["GET"])
def download_today():
    from datetime import timedelta
    daily_file = SAVE_DIR / f"daily_log_{(datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d')}.csv"
    if daily_file.exists():
        return send_file(daily_file, as_attachment=True)
    return "今日记录不存在", 404
    return "文件不存在", 404

@app.route("/clear", methods=["POST"])
@requires_auth
def clear_log():
    password = request.form.get("confirm_password")
    if password != "wyq345760":
        msg = "❌ 清空失败：密码错误"
        return render_with_files(msg)
    try:
        with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["mark_id", "timestamp", "is_simulated"])
        msg = "✅ 总记录已清空"
    except Exception as e:
        msg = f"清空失败: {e}"
    return render_with_files(msg)


@app.route("/clear_today", methods=["POST"])
@requires_auth
def clear_today():
    try:
        from datetime import timedelta
        today_file = SAVE_DIR / f"daily_log_{(datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d')}.csv"
        with open(today_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["mark_id", "timestamp", "is_simulated"])
        msg = "✅ 今日记录已清空"
    except Exception as e:
        msg = f"清空失败: {e}"
    return render_with_files(msg)

@app.route("/delete_last", methods=["POST"])
@requires_auth
def delete_last():
    try:
        from datetime import timedelta
        today_file = SAVE_DIR / f"daily_log_{(datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d')}.csv"
        with open(today_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1:
            msg = "没有可删除的记录"
        else:
            with open(today_file, "w", encoding="utf-8") as f:
                f.writelines(lines[:-1])
            msg = "✅ 已删除今日最后一条记录"
    except Exception as e:
        msg = f"删除失败: {e}"
    return render_with_files(msg)

@app.route("/download_selected", methods=["POST"])
@requires_auth
def download_selected():
    from flask import make_response
    import zipfile
    from io import BytesIO
    selected = request.form.getlist("dates")
    if not selected:
        return render_with_files("请选择至少一个文件")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in selected:
            file_path = SAVE_DIR / filename
            if file_path.exists():
                zip_file.write(file_path, arcname=filename)
    zip_buffer.seek(0)
    response = make_response(zip_buffer.read())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=selected_logs.zip'
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
