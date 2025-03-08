from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Criar uma instância do declarative base
Base = declarative_base()

# Definir as classes que representam as tabelas
class Refeicoes(Base):
    __tablename__ = 'refeicoes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    refeicao = Column(String)
    alimento = Column(String)
    quantidade = Column(Float)
    calorias = Column(Float)
    proteinas = Column(Float)
    carboidratos = Column(Float)
    gorduras = Column(Float)

class Medidas(Base):
    __tablename__ = 'medidas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    peso = Column(Float)
    imc = Column(Float)
    cintura = Column(Float)
    quadril = Column(Float)
    gordura_corporal = Column(Float)

class Metas(Base):
    __tablename__ = 'metas'
    id = Column(Integer, primary_key=True)
    calorias_diarias = Column(Float)
    proteinas_diarias = Column(Float)
    carboidratos_diarios = Column(Float)
    gorduras_diarias = Column(Float)
    peso_meta = Column(Float)
    gordura_corporal_meta = Column(Float)

class AlimentosTaco(Base):
    __tablename__ = 'alimentos_taco'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)
    energia_kcal = Column(Float)
    proteina_g = Column(Float)
    lipideos_g = Column(Float)
    carboidrato_g = Column(Float)
    fibra_g = Column(Float)
    calcio_mg = Column(Float)
    ferro_mg = Column(Float)

# Função para criar e conectar ao banco de dados SQLite usando SQLAlchemy
def conectar_bd():
    engine = create_engine('sqlite:///nutricao.db')
    return engine

# Função para inicializar o banco de dados
def inicializar_bd():
    engine = conectar_bd()
    Base.metadata.create_all(engine)

# Função para obter informações nutricionais usando SQLAlchemy
def obter_info_nutricional(nome_exato):
    engine = conectar_bd()
    Session = sessionmaker(bind=engine)
    session = Session()

    resultado = session.query(AlimentosTaco).filter(AlimentosTaco.nome == nome_exato).first()
    session.close()

    if not resultado:
        return None

    return {
        'calorias': resultado.energia_kcal,
        'proteinas': resultado.proteina_g,
        'gorduras': resultado.lipideos_g,
        'carboidratos': resultado.carboidrato_g
    }

# Função para obter metas do banco de dados usando SQLAlchemy
def obter_metas():
    engine = conectar_bd()
    Session = sessionmaker(bind=engine)
    session = Session()

    resultado = session.query(Metas).filter(Metas.id == 1).first()

    session.close()

    if resultado:
        return {
            'calorias_diarias': resultado.calorias_diarias,
            'proteinas_diarias': resultado.proteinas_diarias,
            'carboidratos_diarios': resultado.carboidratos_diarios,
            'gorduras_diarias': resultado.gorduras_diarias,
            'peso_meta': resultado.peso_meta,
            'gordura_corporal_meta': resultado.gordura_corporal_meta
        }
    else:
        return {
            'calorias_diarias': 2000.0,
            'proteinas_diarias': 150.0,
            'carboidratos_diarios': 225.0,
            'gorduras_diarias': 65.0,
            'peso_meta': 70.0,
            'gordura_corporal_meta': 15.0
        }