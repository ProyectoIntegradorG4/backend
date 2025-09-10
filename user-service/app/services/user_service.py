from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User, UserRegister

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    async def create_user(self, user: UserRegister) -> User:
        # Verificar si el email ya existe
        existing_user = self.db.query(User).filter(User.email == user.email).first()
        
        if existing_user:
            raise ValueError("El email ya está registrado")

        # Crear el usuario
        password_hash = self.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            passwordHash=password_hash,
            pais=user.pais,
            rol=user.rol
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user