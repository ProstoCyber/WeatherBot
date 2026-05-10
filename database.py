from sqlalchemy import BigInteger, String, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column 

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    userID: Mapped[str] = mapped_column(BigInteger, primary_key=True)
    city: Mapped[str] = mapped_column(String(50), default='Moscow')

class Database:
    # Создание моста для связи с БД
    def __init__(self, url):
        self.engine = create_async_engine(url) # Сам движок для общения с БД
        self.session_pool = async_sessionmaker(self.engine, expire_on_commit=False) # Для созданий сессий для каждого запроса

    # Автоматическое создание таблицы при запуске бота
    async def create_tables(self):
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    # Добавление пользователя в БД, если его там нет    
    async def add_user(self, userID: int):
        async with self.session_pool() as session: # Создание сессии(запроса)
            user = await session.get(User, userID) # Получение данных пользователя
            if not user: # Проверка на существование пользователя в БД 
                session.add(User(userID=userID)) # Добавление пользователя в БД
                await session.commit() # Сохранение изменений
    
    # Смена города
    async def update_city(self, userID: int, city: str):
        async with self.session_pool() as session:
            user = await session.get(User, userID)
            if user:
                user.city = city # Смена региона
                await session.commit()
                return True
            return False
    
    # Получение всех пользователей для рассылки
    async def get_all_users(self):
        async with self.session_pool() as session:
            allList = await session.execute(select(User)) # SELECT всех пользователей из БД
            return allList.scalars().all() # Возвращение сырых строкх, преобразованных в объекты класса User

    # Получение конкретного пользователя
    async def get_user(self, userID: int) -> User | None: # Возвращение класса, либо None
        async with self.session_pool() as session:
            return await session.get(User, userID) # Возвращение данных пользователя по его ID