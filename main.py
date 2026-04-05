from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session,sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel
from typing import Optional, List


app = FastAPI(title="My FastAPI App")


#Database setup
engine = create_engine("sqlite:///user.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, bind=engine, autoflush=False)
Base = declarative_base()

#modeles
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True,index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100),unique=True, nullable=False)
    role = Column(String(100),nullable=False)

#relier le modèle à notre moteur engine (base de données)
Base.metadata.create_all(engine)


#pydantic pour validation
class UserCreate(BaseModel):
    name: str
    email: str
    role: str

#la classe userresponse protège les données, sert de filet pour que les données fuient via les requetes http
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str



#la fonction get_db interagit avec la bd, fermeture et ouverture de session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
get_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}

#obtenir l'utilisateur
@app.get("/items/{item_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


#créer l'utilisateur
@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=404, detail="Cette adresse e-mail est déja utilisée")
    #creation d'un utilisateur
    #new_user = User(name=user.name, email=user.email, role=user.role)
    #db.add(new_user)
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


#mise à jour de l'utilisateur
@app.put("/user/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="L'utilisateur est introuvable")

    for field, value in user.dict().items():
        setattr(db_user, field, value)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

#suppresion d'un utilisateur
@app.delete("/user/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="L'utilisateur est introuvable")
    db.delete(db_user)
    db.commit()
    db.refresh(db_user)
    return {"Le profil a bien été supprimé"}


#recupérer tous les utilisateurs
@app.get("/users/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()


