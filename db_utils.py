import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, 
    DateTime, Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Configuração do banco de dados
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelos
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="user", cascade="all, delete-orphan")
    
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    level = Column(String(20))  # Iniciante, Moderado, Experiente
    preferred_distance = Column(Integer)  # em km
    preferred_time = Column(String(20))  # Manhã, Tarde, Noite
    visual_style = Column(String(20))  # Aventura, Urbano, Família
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", back_populates="preferences")

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    starting_point = Column(String(200))
    distance = Column(Float)  # em km
    steps = Column(JSON)  # Lista de passos da rota
    guide = Column(Text)  # Guia gerado pelo OpenAI
    weather_data = Column(JSON)  # Dados climáticos no momento da criação
    elevation_data = Column(JSON)  # Dados de elevação da rota
    created_at = Column(DateTime, default=datetime.now)
    is_favorite = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="routes")
    
class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    temperatura = Column(Float)
    umidade = Column(Float)
    pressao = Column(Float)
    luminosidade = Column(Float)
    
class GeneratedImage(Base):
    __tablename__ = "generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), index=True)  # Identificador para tipo de imagem (weather, guide, cycling)
    prompt = Column(Text)  # Prompt usado para gerar a imagem
    url = Column(String(255))  # URL da imagem gerada
    created_at = Column(DateTime, default=datetime.now)

# Funções para manipulação do banco de dados
def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    Base.metadata.create_all(bind=engine)

def save_sensor_data(data):
    """Salva dados dos sensores no banco de dados"""
    db = get_db()
    try:
        sensor_data = SensorData(
            temperatura=data.get("temperatura"),
            umidade=data.get("umidade"),
            pressao=data.get("pressao"),
            luminosidade=data.get("luminosidade")
        )
        db.add(sensor_data)
        db.commit()
        return sensor_data
    except Exception as e:
        db.rollback()
        raise e

def save_route(user_id, title, starting_point, distance, steps, guide, weather_data, elevation_data):
    """Salva uma nova rota no banco de dados"""
    db = get_db()
    try:
        route = Route(
            user_id=user_id,
            title=title,
            starting_point=starting_point,
            distance=distance,
            steps=steps,
            guide=guide,
            weather_data=weather_data,
            elevation_data=elevation_data
        )
        db.add(route)
        db.commit()
        return route
    except Exception as e:
        db.rollback()
        raise e

def save_generated_image(key, prompt, url):
    """Salva informações de uma imagem gerada no banco de dados"""
    db = get_db()
    try:
        image = GeneratedImage(
            key=key,
            prompt=prompt,
            url=url
        )
        db.add(image)
        db.commit()
        return image
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar imagem no banco: {str(e)}")
        return None

def get_or_create_user(name, email):
    """Obtém um usuário pelo e-mail ou cria um novo se não existir"""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name, email=email)
            db.add(user)
            db.commit()
        return user
    except Exception as e:
        db.rollback()
        raise e

def update_user_preferences(user_id, level, preferred_distance, preferred_time, visual_style):
    """Atualiza ou cria as preferências de um usuário"""
    db = get_db()
    try:
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not pref:
            pref = UserPreference(
                user_id=user_id,
                level=level,
                preferred_distance=preferred_distance,
                preferred_time=preferred_time,
                visual_style=visual_style
            )
            db.add(pref)
        else:
            pref.level = level
            pref.preferred_distance = preferred_distance
            pref.preferred_time = preferred_time
            pref.visual_style = visual_style
            pref.updated_at = datetime.now()
        db.commit()
        return pref
    except Exception as e:
        db.rollback()
        raise e

def get_user_routes(user_id, limit=10):
    """Obtém as rotas recentes de um usuário"""
    db = get_db()
    return db.query(Route).filter(Route.user_id == user_id).order_by(Route.created_at.desc()).limit(limit).all()

def get_historical_sensor_data(limit=24):
    """Obtém dados históricos dos sensores"""
    try:
        db = get_db()
        return db.query(SensorData).order_by(SensorData.timestamp.desc()).limit(limit).all()
    except Exception as e:
        print(f"Erro ao consultar dados históricos: {str(e)}")
        return []

def get_cached_image(key):
    """Obtém uma imagem gerada anteriormente pelo key"""
    try:
        db = get_db()
        return db.query(GeneratedImage).filter(GeneratedImage.key == key).order_by(GeneratedImage.created_at.desc()).first()
    except Exception as e:
        print(f"Erro ao consultar imagem em cache: {str(e)}")
        return None