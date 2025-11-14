from flask import Flask, jsonify, send_file, request
import os
import re
import logging
import hashlib
import hmac
import time
from functools import wraps
from logging.handlers import RotatingFileHandler
import asyncio

app = Flask(__name__)

# 版本文件路径
VERSION_FILE = 'latest_version.txt'

# 默认版本号
default_version = "1.0.3"

# 加密密钥（生产环境应该从环境变量或配置文件中读取）
SECRET_KEY = "version_control_secret_key_2025"

# 请求超时时间（秒）
REQUEST_TIMEOUT = 300

# 设置日志系统
def setup_logging():
    """设置日志配置"""
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（按文件大小轮转）
    file_handler = RotatingFileHandler(
        'logs/version_control.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

# 加密校验装饰器
def require_auth(f):
    """接口加密校验装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取请求参数
            timestamp = request.headers.get('X-Timestamp')
            signature = request.headers.get('X-Signature')
            
            # 检查必要参数
            if not timestamp or not signature:
                logger.warning(f"接口 {request.path} 缺少认证参数")
                return jsonify({"error": "认证参数缺失"}), 401
            
            # 检查时间戳有效性
            current_time = int(time.time())
            request_time = int(timestamp)
            
            if abs(current_time - request_time) > REQUEST_TIMEOUT:
                logger.warning(f"接口 {request.path} 请求超时，当前时间: {current_time}, 请求时间: {request_time}")
                return jsonify({"error": "请求超时"}), 401
            
            # 验证签名
            # 构建签名字符串：方法 + 路径 + 时间戳 + 查询参数
            path = request.path
            query_string = request.query_string.decode('utf-8') if request.query_string else ""
            sign_data = f"{request.method}:{path}:{timestamp}:{query_string}"
            
            # 计算HMAC签名
            expected_signature = hmac.new(
                SECRET_KEY.encode('utf-8'),
                sign_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 验证签名
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning(f"接口 {request.path} 签名验证失败")
                return jsonify({"error": "签名验证失败"}), 401
            
            logger.info(f"接口 {request.path} 认证成功")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"接口认证异常: {str(e)}")
            return jsonify({"error": "认证异常"}), 500
    
    return decorated_function

# 生成签名的工具函数
def generate_signature(method, path, timestamp, query_string=""):
    """生成接口签名"""
    sign_data = f"{method}:{path}:{timestamp}:{query_string}"
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        sign_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def get_latest_version():
    """从文件获取最新版本号"""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            pass
    
    # 如果文件不存在或读取失败，创建默认版本文件
    save_latest_version(default_version)
    return default_version

def save_latest_version(version):
    """保存最新版本号到文件"""
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(version)

def compare_version_strings(version1, version2):
    """比较两个版本号字符串
    返回: 0 - 版本相同，1 - version1 > version2，-1 - version1 < version2
    """
    # 将版本号分割为数字列表
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))
    
    # 补齐长度
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
    # 逐位比较
    for i in range(max_len):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1
    
    return 0

@app.route('/api/version/compare', methods=['GET'])
@require_auth
async def compare_versions():
    """
    版本比较接口
    参数：version - 需要比较的版本号
    """
    try:
        input_version = request.args.get('version')
        
        logger.info(f"版本比较请求: version={input_version}")
        
        if not input_version:
            logger.warning("版本比较接口缺少version参数")
            return jsonify({"error": "缺少version参数"}), 400
        
        # 验证版本号格式
        if not re.match(r'^\d+(\.\d+)*$', input_version):
            logger.warning(f"版本号格式错误: {input_version}")
            return jsonify({"error": "版本号格式错误，请使用x.y.z格式"}), 400
        
        # 异步获取本地最新版本号
        latest_version = await asyncio.to_thread(get_latest_version)
        
        # 异步比较版本号
        result = await asyncio.to_thread(compare_version_strings, latest_version, input_version)
        
        # 根据比较结果返回不同的响应
        if result == 0:
            # 版本相同
            logger.info(f"版本比较结果: 版本相同, input={input_version}, latest={latest_version}")
            return jsonify({
                "code": 0,
                "message": "当前版本是最新版本",
                "input_version": input_version,
                "latest_version": latest_version
            })
        elif result == -1:
            # 本地版本比传参版本低，更新为传参版本
            await asyncio.to_thread(save_latest_version, input_version)
            logger.info(f"版本比较结果: 本地版本较低, 已更新, old={latest_version}, new={input_version}")
            return jsonify({
                "code": 0,
                "message": "当前版本是最新版本",
                "input_version": input_version,
                "latest_version": input_version,
                "updated": True
            })
        else:
            # 本地版本比传参版本高
            logger.info(f"版本比较结果: 本地版本较高, input={input_version}, latest={latest_version}")
            return jsonify({
                "code": 1,
                "message": f"当前最新版本是{latest_version}，请更新最新版本",
                "input_version": input_version,
                "latest_version": latest_version
            })
    
    except Exception as e:
        logger.error(f"版本比较接口异常: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

@app.route('/api/download/latest', methods=['GET'])
@require_auth
async def download_latest():
    """
    下载最新版本接口
    直接返回本地存储的安装包
    """
    # 本地存储包路径（固定文件名）
    local_package_path = "packages/latest_package.exe"
    
    try:
        logger.info("下载安装包请求")
        
        # 异步检查本地包是否存在
        exists = await asyncio.to_thread(os.path.exists, local_package_path)
        if not exists:
            logger.warning("安装包不存在")
            return jsonify({
                "error": "本地安装包不存在，请先上传安装包",
                "upload_endpoint": "/api/upload/package"
            }), 404
        
        # 异步获取文件信息
        file_size = await asyncio.to_thread(os.path.getsize, local_package_path)
        logger.info(f"开始下载安装包，文件大小: {file_size} 字节")
        
        # 返回本地存储的包
        return send_file(
            local_package_path,
            as_attachment=True,
            download_name="DwtAI-Hub-Install-X64.exe"
        )
    
    except Exception as e:
        logger.error(f"下载安装包异常: {str(e)}")
        return jsonify({"error": "服务器错误: {str(e)}"}), 500

@app.route('/api/upload/package', methods=['POST'])
@require_auth
async def upload_package():
    """
    上传安装包接口
    上传最新的安装包，替换本地存储的包
    """
    # 本地存储包路径（固定文件名）
    local_package_path = "packages/latest_package.exe"
    
    try:
        logger.info("上传安装包请求")
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            logger.warning("上传接口没有文件")
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        
        # 检查文件是否选择
        if file.filename == '':
            logger.warning("上传接口没有选择文件")
            return jsonify({"error": "没有选择文件"}), 400
        
        # 检查文件类型
        if not file.filename.endswith('.exe'):
            logger.warning(f"上传文件类型不支持: {file.filename}")
            return jsonify({"error": "只支持.exe文件上传"}), 400
        
        # 异步确保包目录存在
        if not await asyncio.to_thread(os.path.exists, 'packages'):
            await asyncio.to_thread(os.makedirs, 'packages')
            logger.info("创建packages目录")
        
        # 异步删除旧的安装包（如果存在）
        if await asyncio.to_thread(os.path.exists, local_package_path):
            await asyncio.to_thread(os.remove, local_package_path)
            logger.info("已删除旧安装包")
        
        # 异步保存新安装包
        await asyncio.to_thread(file.save, local_package_path)
        
        # 异步获取文件大小
        file_size = await asyncio.to_thread(os.path.getsize, local_package_path)
        
        logger.info(f"新安装包上传成功，大小: {file_size} 字节")
        
        return jsonify({
            "status": "success",
            "message": "安装包上传成功",
            "file_size": file_size,
            "file_path": local_package_path
        })
    
    except Exception as e:
        logger.error(f"上传安装包异常: {str(e)}")
        return jsonify({"error": f"上传失败: {str(e)}"}), 500

@app.route('/')
def index():
    """首页"""
    latest_version = get_latest_version()
    return f"""
    <h1>版本管理服务</h1>
    <p><strong>当前最新版本:</strong> {latest_version}</p>
    
    <h2>可用接口</h2>
    <ul>
        <li><a href="/api/version/compare?version=1.0.0">版本比较</a> - GET /api/version/compare?version=1.0.0</li>
        <li><a href="/api/download/latest">下载最新版本</a> - GET /api/download/latest</li>
    </ul>
    
    <h3>接口说明</h3>
    <p><strong>版本比较接口:</strong> 传入版本号与本地最新版本进行比较</p>
    <p><strong>下载接口:</strong> 从外部链接下载最新安装包</p>
    """

# 生产环境WSGI应用入口
app.wsgi_app = app.wsgi_app

if __name__ == '__main__':
    # 确保版本文件存在
    get_latest_version()

    # 创建包目录
    if not os.path.exists('packages'):
        os.makedirs('packages')
    
    # 检查是否在生产环境
    import os
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    if is_production:
        # 生产环境使用Waitress服务器
        try:
            from waitress import serve
            logger.info("启动生产环境服务器 (Waitress)")
            serve(app, host='0.0.0.0', port=10250, threads=4)
        except ImportError:
            logger.warning("Waitress未安装，使用Flask开发服务器")
            logger.warning("建议安装: pip install waitress")
            app.run(host='0.0.0.0', port=10250, debug=False)
    else:
        # 开发环境
        logger.info("启动开发环境服务器")
        app.run(host='0.0.0.0', port=10250, debug=True)