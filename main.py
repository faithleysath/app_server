from fastapi import FastAPI, Depends, Request, HTTPException, Security
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, Event, Authorization
from utils import check_version, check_ip
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from jose import jwt
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# JWT配置
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # 小时

# 用户认证信息
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = FastAPI()
security = HTTPBearer()

def create_jwt_token(username: str) -> str:
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
    return jwt.encode(
        {"username": username, "exp": expiration},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="无效的Token")

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    return decode_jwt_token(credentials.credentials)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(request: LoginRequest):
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        token = create_jwt_token(request.username)
        return {"code": 200, "data": {"token": token}}
    raise HTTPException(status_code=401, detail="用户名或密码错误")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据模型
class AuthorizationCreate(BaseModel):
    app: str
    version_rule: str
    ip_rule: str
    detail_info: str

class AuthorizationUpdate(AuthorizationCreate):
    id: int

# API接口
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/auth/list")
async def list_auth(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    auth_rules = db.query(Authorization).all()
    return {
        "code": 200,
        "data": [
            {
                "id": rule.id,
                "app": rule.app,
                "version_rule": rule.version_rule,
                "ip_rule": rule.ip_rule,
                "detail_info": rule.detail_info,
                "created_at": rule.created_at
            }
            for rule in auth_rules
        ]
    }

@app.post("/api/auth/create")
async def create_auth(auth: AuthorizationCreate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    db_auth = Authorization(**auth.dict())
    db.add(db_auth)
    db.commit()
    db.refresh(db_auth)
    return {"code": 200, "data": db_auth}

@app.post("/api/auth/update")
async def update_auth(auth: AuthorizationUpdate, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    db_auth = db.query(Authorization).filter(Authorization.id == auth.id).first()
    if not db_auth:
        raise HTTPException(status_code=404, detail="授权规则不存在")
    
    for key, value in auth.dict().items():
        setattr(db_auth, key, value)
    
    db.commit()
    db.refresh(db_auth)
    return {"code": 200, "data": db_auth}

@app.delete("/api/auth/delete/{auth_id}")
async def delete_auth(auth_id: int, db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    db_auth = db.query(Authorization).filter(Authorization.id == auth_id).first()
    if not db_auth:
        raise HTTPException(status_code=404, detail="授权规则不存在")
    
    db.delete(db_auth)
    db.commit()
    return {"code": 200}

@app.get("/api/events")
async def list_events(
    app: Optional[str] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    query = db.query(Event)
    if app:
        query = query.filter(Event.app == app)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    events = query.order_by(Event.created_at.desc()).all()
    return {
        "code": 200,
        "data": [
            {
                "id": event.id,
                "app": event.app,
                "version": event.version,
                "event_type": event.event_type,
                "client_ip": event.client_ip,
                "created_at": event.created_at
            }
            for event in events
        ]
    }

@app.get("/api/stats")
async def get_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)
):
    query = db.query(
        Event.app,
        func.count(Event.id).filter(Event.event_type == 'start').label('start_count'),
        func.count(Event.id).filter(Event.event_type == 'stop').label('stop_count'),
        func.count(func.distinct(Event.client_ip)).label('unique_ips')
    ).group_by(Event.app)

    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(Event.created_at >= start)
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(Event.created_at <= end)

    stats = query.all()
    return {
        "code": 200,
        "data": [
            {
                "app": app,
                "start_count": start_count,
                "stop_count": stop_count,
                "unique_ips": unique_ips
            }
            for app, start_count, stop_count, unique_ips in stats
        ]
    }

def get_client_ip(request: Request) -> str:
    """获取客户端真实IP
    
    优先级:
    1. CF-Connecting-IP (Cloudflare)
    2. True-Client-IP
    3. X-Real-IP
    4. X-Client-IP
    5. X-Forwarded-For的第一个IP
    6. request.client.host
    """
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return cf_ip
        
    # Akamai and others
    if true_ip := request.headers.get("True-Client-IP"):
        return true_ip
        
    # Nginx
    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip
        
    # General
    if client_ip := request.headers.get("X-Client-IP"):
        return client_ip
        
    # X-Forwarded-For contains proxy chain, get the first IP
    if forwarded_for := request.headers.get("X-Forwarded-For"):
        return forwarded_for.split(",")[0].strip()
        
    # Fallback to direct client IP
    return request.client.host

@app.get("/api/event/start")
async def start_event(
    app: str,
    version: str,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)
    
    # 查找匹配的授权规则
    auth = db.query(Authorization).filter(
        Authorization.app == app
    ).all()
    
    # 检查是否有匹配的授权规则
    for rule in auth:
        if check_version(version, rule.version_rule) and check_ip(client_ip, rule.ip_rule):
            # 记录启动事件
            event = Event(
                app=app,
                version=version,
                event_type="start",
                client_ip=client_ip
            )
            db.add(event)
            db.commit()
            
            # 返回授权信息
            return {
                "code": 200,
                "data": {
                    "detail_info": rule.detail_info
                }
            }
    
    # 未找到匹配的授权规则
    raise HTTPException(
        status_code=403,
        detail={
            "code": 403,
            "message": "未授权访问"
        }
    )

@app.get("/api/event/stop")
async def stop_event(
    app: str,
    version: str,
    request: Request,
    db: Session = Depends(get_db)
):
    # 记录停止事件
    event = Event(
        app=app,
        version=version,
        event_type="stop",
        client_ip=get_client_ip(request)
    )
    db.add(event)
    db.commit()
    
    return {
        "code": 200,
        "data": {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7389)
