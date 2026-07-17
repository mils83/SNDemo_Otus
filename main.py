from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Union
from jose import JWTError
from database import get_db_connection
from auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM

app = FastAPI(title="Social Network Skeleton")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic модели для валидации
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    birth_date: str # Формат: YYYY-MM-DD
    gender: str
    interests: Optional[str] = None
    city: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    interests: Optional[str] = None
    city: Optional[str] = None

# Зависимость для проверки токена
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

@app.post("/user/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверка существования пользователя
    cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    
    # Параметризованный запрос для защиты от SQL-инъекций
    query = """
        INSERT INTO users (username, password_hash, first_name, last_name, birth_date, gender, interests, city)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """
    cursor.execute(query, (
        user.username, hashed_password, user.first_name, user.last_name,
        user.birth_date, user.gender, user.interests, user.city
    ))
    
    user_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": user_id, "message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Параметризованный запрос
    cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (form_data.username,))
    db_user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not db_user or not verify_password(form_data.password, db_user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user/get/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Параметризованный запрос, не возвращаем пароль
    query = """
        SELECT id, first_name, last_name, birth_date::text, gender, interests, city 
        FROM users WHERE id = %s
    """
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)