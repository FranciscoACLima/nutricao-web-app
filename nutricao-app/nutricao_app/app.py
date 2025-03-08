import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import requests
import io
import os

from nutricao_app.models import obter_metas

# Configuração da página
st.set_page_config(
    page_title="Acompanhamento Nutricional",
    page_icon="🥗",
    layout="wide"
)

# Função para criar e conectar ao banco de dados SQLite
def conectar_bd():
    conn = sqlite3.connect('nutricao.db')
    return conn

# Função para inicializar o banco de dados
def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()

    # Criar tabela de refeições
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS refeicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        refeicao TEXT,
        alimento TEXT,
        quantidade REAL,
        calorias REAL,
        proteinas REAL,
        carboidratos REAL,
        gorduras REAL
    )
    ''')

    # Criar tabela de medidas corporais
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        peso REAL,
        imc REAL,
        cintura REAL,
        quadril REAL,
        gordura_corporal REAL
    )
    ''')

    # Criar tabela para metas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        calorias_diarias REAL,
        proteinas_diarias REAL,
        carboidratos_diarios REAL,
        gorduras_diarias REAL,
        peso_meta REAL,
        gordura_corporal_meta REAL
    )
    ''')

    # Criar tabela para alimentos TACO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alimentos_taco (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        energia_kcal REAL,
        proteina_g REAL,
        lipideos_g REAL,
        carboidrato_g REAL,
        fibra_g REAL,
        calcio_mg REAL,
        ferro_mg REAL
    )
    ''')

    conn.commit()
    conn.commit()
    conn.close()

# Função para carregar a tabela TACO da internet e salvar no banco de dados
def carregar_tabela_taco():
    conn = conectar_bd()
    cursor = conn.cursor()

    # Verificar se a tabela já contém dados
    cursor.execute("SELECT COUNT(*) FROM alimentos_taco")
    count = cursor.fetchone()[0]

    if count == 0:
        try:
            # URL da tabela TACO em formato CSV (pode ser necessário ajustar conforme disponibilidade)
            url = "https://www.nepa.unicamp.br/taco/tabela/taco_4_edicao_2011.csv"

            # Tentar fazer o download dos dados
            st.info("Baixando tabela TACO. Aguarde...")

            try:
                # Tentar baixar diretamente
                response = requests.get(url)
                response.raise_for_status()
                df_taco = pd.read_csv(io.StringIO(response.content.decode('utf-8')), sep=';')
            except:
                # Caso a URL direta não funcione, usar uma versão simplificada para exemplo
                st.warning("Não foi possível baixar a tabela TACO original. Usando dados de exemplo.")

                # Criar dados de exemplo da tabela TACO
                dados_taco = {
                    'nome': [
                        'Arroz, tipo 1, cozido',
                        'Feijão, carioca, cozido',
                        'Frango, peito, sem pele, cozido',
                        'Pão, francês',
                        'Maçã, com casca',
                        'Banana prata',
                        'Leite, integral',
                        'Ovo, galinha, inteiro, cozido',
                        'Alface, lisa, crua',
                        'Cenoura, crua',
                        'Batata, inglesa, cozida',
                        'Carne, bovina, patinho, sem gordura, cozido',
                        'Azeite, de oliva',
                        'Manteiga, com sal',
                        'Aveia, flocos'
                    ],
                    'energia_kcal': [128, 76, 159, 300, 56, 98, 62, 146, 14, 34, 52, 219, 884, 726, 394],
                    'proteina_g': [2.5, 4.8, 32, 8, 0.3, 1.3, 3.2, 13.3, 1.7, 1.3, 1.2, 35.9, 0, 0.9, 13.9],
                    'lipideos_g': [0.2, 0.5, 3.2, 3.1, 0.2, 0.1, 3.4, 9.5, 0.2, 0.2, 0, 8.5, 100, 82.4, 8.5],
                    'carboidrato_g': [28.1, 13.6, 0, 58.6, 15, 26, 4.7, 0.6, 2.4, 7.7, 11.9, 0, 0, 0.1, 67.0],
                    'fibra_g': [1.6, 8.5, 0, 2.3, 2.4, 2.0, 0, 0, 1.8, 3.2, 1.3, 0, 0, 0, 9.0],
                    'calcio_mg': [4, 27, 7, 16, 4, 8, 123, 42, 38, 23, 4, 4, 0, 15, 52],
                    'ferro_mg': [0.1, 1.3, 0.4, 1.0, 0.1, 0.3, 0.1, 1.5, 0.4, 0.1, 0.2, 3.4, 0.4, 0, 4.4]
                }
                df_taco = pd.DataFrame(dados_taco)

            # Inserir dados na tabela
            for _, row in df_taco.iterrows():
                cursor.execute('''
                INSERT INTO alimentos_taco
                (nome, energia_kcal, proteina_g, lipideos_g, carboidrato_g, fibra_g, calcio_mg, ferro_mg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['nome'],
                    row['energia_kcal'],
                    row['proteina_g'],
                    row['lipideos_g'],
                    row['carboidrato_g'],
                    row['fibra_g'],
                    row['calcio_mg'],
                    row['ferro_mg']
                ))

            conn.commit()
            st.success("Tabela TACO carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar tabela TACO: {str(e)}")

    conn.close()

# Função para buscar alimento na tabela TACO
def buscar_alimento_taco(nome_alimento):
    conn = conectar_bd()
    cursor = conn.cursor()

    # Buscar alimento pelo nome (usando LIKE para busca parcial)
    cursor.execute('''
    SELECT nome, energia_kcal, proteina_g, lipideos_g, carboidrato_g
    FROM alimentos_taco
    WHERE nome LIKE ?
    ORDER BY nome
    ''', (f'%{nome_alimento}%',))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return None

    # Converter para DataFrame para facilitar a exibição
    df_resultados = pd.DataFrame(resultados, columns=['Nome', 'Calorias (kcal)', 'Proteínas (g)', 'Gorduras (g)', 'Carboidratos (g)'])
    return df_resultados

# Função para obter informações nutricionais de um alimento específico
# def obter_info_nutricional(nome_exato):
#     conn = conectar_bd()
#     cursor = conn.cursor()

#     cursor.execute('''
#     SELECT energia_kcal, proteina_g, lipideos_g, carboidrato_g
#     FROM alimentos_taco
#     WHERE nome = ?
#     ''', (nome_exato,))

#     resultado = cursor.fetchone()
#     conn.close()

#     if not resultado:
#         return None

#     return {
#         'calorias': resultado[0],
#         'proteinas': resultado[1],
#         'gorduras': resultado[2],
#         'carboidratos': resultado[3]
#     }

# Função para criar dados de exemplo no banco de dados
def criar_dados_exemplo():
    conn = conectar_bd()
    cursor = conn.cursor()

    # Verificar se já existem refeições
    cursor.execute("SELECT COUNT(*) FROM refeicoes")
    count_refeicoes = cursor.fetchone()[0]

    if count_refeicoes == 0:
        # Dados de exemplo para refeições
        refeicoes_exemplo = [
            ((datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras)
            for i, (refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras) in enumerate([
                ('Café da Manhã', 'Pão Integral', 100, 240, 8, 45, 2),
                ('Almoço', 'Arroz', 150, 195, 4, 40, 0),
                ('Jantar', 'Frango', 200, 330, 40, 0, 10),
                ('Lanche', 'Maçã', 150, 80, 0, 21, 0),
                ('Café da Manhã', 'Aveia', 80, 300, 12, 54, 5),
                ('Almoço', 'Feijão', 100, 120, 7, 22, 0),
                ('Jantar', 'Salmão', 180, 280, 25, 0, 15),
                ('Café da Manhã', 'Tapioca', 120, 220, 3, 30, 7),
                ('Almoço', 'Salada', 200, 90, 2, 10, 2),
                ('Jantar', 'Sopa', 300, 200, 15, 25, 4)
            ])
        ]

        cursor.executemany('''
        INSERT INTO refeicoes (data, refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', refeicoes_exemplo)

    # Verificar se já existem medidas
    cursor.execute("SELECT COUNT(*) FROM medidas")
    count_medidas = cursor.fetchone()[0]

    if count_medidas == 0:
        # Dados de exemplo para medidas corporais
        medidas_exemplo = [
            ((datetime.now() - timedelta(days=i*5)).strftime('%Y-%m-%d'), peso, imc, cintura, quadril, gordura)
            for i, (peso, imc, cintura, quadril, gordura) in enumerate([
                (78.5, 26.8, 92, 100, 22),
                (78.0, 26.6, 91, 99, 21.5),
                (77.2, 26.3, 90, 98, 21),
                (76.8, 26.2, 89, 98, 20.5),
                (76.0, 25.9, 88, 97, 20),
                (75.5, 25.7, 87, 96, 19.5)
            ])
        ]

        cursor.executemany('''
        INSERT INTO medidas (data, peso, imc, cintura, quadril, gordura_corporal)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', medidas_exemplo)

    # Verificar se já existem metas
    cursor.execute("SELECT COUNT(*) FROM metas")
    count_metas = cursor.fetchone()[0]

    if count_metas == 0:
        # Dados de exemplo para metas
        cursor.execute('''
        INSERT INTO metas (id, calorias_diarias, proteinas_diarias, carboidratos_diarios, gorduras_diarias, peso_meta, gordura_corporal_meta)
        VALUES (1, 2000, 150, 225, 65, 70.0, 15.0)
        ''')

    conn.commit()
    conn.close()

# Função para obter metas do banco de dados
# def obter_metas():
#     conn = conectar_bd()
#     cursor = conn.cursor()

#     cursor.execute("SELECT * FROM metas WHERE id = 1")
#     resultado = cursor.fetchone()

#     conn.close()

#     if resultado:
#         return {
#             'calorias_diarias': resultado[1],
#             'proteinas_diarias': resultado[2],
#             'carboidratos_diarios': resultado[3],
#             'gorduras_diarias': resultado[4],
#             'peso_meta': resultado[5],
#             'gordura_corporal_meta': resultado[6]
#         }
#     else:
#         return {
#             'calorias_diarias': 2000.0,
#             'proteinas_diarias': 150.0,
#             'carboidratos_diarios': 225.0,
#             'gorduras_diarias': 65.0,
#             'peso_meta': 70.0,
#             'gordura_corporal_meta': 15.0
#         }

# Aplicar estilo
def aplicar_estilo():
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #e9ecef;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    h1, h2, h3 {
        color: #2E7D32;
    }
    .metric-card {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2E7D32;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para adicionar refeição
def adicionar_refeicao(data, tipo_refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO refeicoes (data, refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data, tipo_refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras))

    conn.commit()
    conn.close()

# Função para adicionar medida
def adicionar_medida(data, peso, altura, cintura, quadril, gordura_corporal):
    imc = peso / ((altura/100) ** 2)

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO medidas (data, peso, imc, cintura, quadril, gordura_corporal)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (data, peso, imc, cintura, quadril, gordura_corporal))

    conn.commit()
    conn.close()

# Função para atualizar metas
def atualizar_metas(metas_dict):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE metas
    SET calorias_diarias = ?,
        proteinas_diarias = ?,
        carboidratos_diarios = ?,
        gorduras_diarias = ?,
        peso_meta = ?,
        gordura_corporal_meta = ?
    WHERE id = 1
    ''', (
        metas_dict['calorias_diarias'],
        metas_dict['proteinas_diarias'],
        metas_dict['carboidratos_diarios'],
        metas_dict['gorduras_diarias'],
        metas_dict['peso_meta'],
        metas_dict['gordura_corporal_meta']
    ))

    conn.commit()
    conn.close()

# Função para obter refeições por data
def obter_refeicoes_por_data(data):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT data, refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras
    FROM refeicoes
    WHERE data = ?
    ''', (data,))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return pd.DataFrame(columns=['data', 'refeicao', 'alimento', 'quantidade', 'calorias', 'proteinas', 'carboidratos', 'gorduras'])

    df = pd.DataFrame(resultados, columns=['data', 'refeicao', 'alimento', 'quantidade', 'calorias', 'proteinas', 'carboidratos', 'gorduras'])
    return df

# Função para obter refeições por período
def obter_refeicoes_por_periodo(data_inicio):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT data, refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras
    FROM refeicoes
    WHERE data >= ?
    ORDER BY data
    ''', (data_inicio,))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return pd.DataFrame(columns=['data', 'refeicao', 'alimento', 'quantidade', 'calorias', 'proteinas', 'carboidratos', 'gorduras'])

    df = pd.DataFrame(resultados, columns=['data', 'refeicao', 'alimento', 'quantidade', 'calorias', 'proteinas', 'carboidratos', 'gorduras'])
    return df

# Função para obter todas as medidas
def obter_todas_medidas():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT data, peso, imc, cintura, quadril, gordura_corporal
    FROM medidas
    ORDER BY data
    ''')

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return pd.DataFrame(columns=['data', 'peso', 'imc', 'cintura', 'quadril', 'gordura_corporal'])

    df = pd.DataFrame(resultados, columns=['data', 'peso', 'imc', 'cintura', 'quadril', 'gordura_corporal'])
    return df

# Função para gerar gráfico de consumo diário por macronutriente
def gerar_grafico_consumo_diario(df_filtrado):
    df_agrupado = df_filtrado.groupby('data').agg({
        'calorias': 'sum',
        'proteinas': 'sum',
        'carboidratos': 'sum',
        'gorduras': 'sum'
    }).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_agrupado['data'],
        y=df_agrupado['calorias'],
        mode='lines+markers',
        name='Calorias',
        line=dict(color='#FFA500', width=2),
        marker=dict(size=8)
    ))

    metas = obter_metas()

    fig.update_layout(
        title='Consumo Calórico Diário',
        xaxis_title='Data',
        yaxis_title='Calorias (kcal)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    # Adicionar linha de meta calórica
    fig.add_shape(
        type="line",
        x0=df_agrupado['data'].min(),
        y0=metas['calorias_diarias'],
        x1=df_agrupado['data'].max(),
        y1=metas['calorias_diarias'],
        line=dict(color="red", width=2, dash="dash"),
    )

    fig.add_annotation(
        x=df_agrupado['data'].max(),
        y=metas['calorias_diarias'],
        text="Meta",
        showarrow=False,
        yshift=10,
        font=dict(color="red")
    )

    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de macronutrientes
    fig_macro = go.Figure()

    fig_macro.add_trace(go.Scatter(
        x=df_agrupado['data'],
        y=df_agrupado['proteinas'],
        mode='lines+markers',
        name='Proteínas (g)',
        line=dict(color='#007BFF', width=2),
        marker=dict(size=8)
    ))

    fig_macro.add_trace(go.Scatter(
        x=df_agrupado['data'],
        y=df_agrupado['carboidratos'],
        mode='lines+markers',
        name='Carboidratos (g)',
        line=dict(color='#28A745', width=2),
        marker=dict(size=8)
    ))

    fig_macro.add_trace(go.Scatter(
        x=df_agrupado['data'],
        y=df_agrupado['gorduras'],
        mode='lines+markers',
        name='Gorduras (g)',
        line=dict(color='#DC3545', width=2),
        marker=dict(size=8)
    ))

    fig_macro.update_layout(
        title='Consumo Diário de Macronutrientes',
        xaxis_title='Data',
        yaxis_title='Quantidade (g)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig_macro, use_container_width=True)

# Função para gerar gráfico de progresso corporal
def gerar_grafico_progresso_corporal():
    df_medidas = obter_todas_medidas()
    df_medidas['data'] = pd.to_datetime(df_medidas['data'])
    df_medidas = df_medidas.sort_values('data')

    metas = obter_metas()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_medidas['data'],
        y=df_medidas['peso'],
        mode='lines+markers',
        name='Peso (kg)',
        line=dict(color='#007BFF', width=2),
        marker=dict(size=8)
    ))

    # Adicionar linha de meta de peso
    fig.add_shape(
        type="line",
        x0=df_medidas['data'].min(),
        y0=metas['peso_meta'],
        x1=df_medidas['data'].max(),
        y1=metas['peso_meta'],
        line=dict(color="red", width=2, dash="dash"),
    )

    fig.add_annotation(
        x=df_medidas['data'].max(),
        y=metas['peso_meta'],
        text="Meta",
        showarrow=False,
        yshift=10,
        font=dict(color="red")
    )

    fig.update_layout(
        title='Progresso de Peso Corporal',
        xaxis_title='Data',
        yaxis_title='Peso (kg)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de composição corporal
    fig_comp = go.Figure()

    fig_comp.add_trace(go.Scatter(
        x=df_medidas['data'],
        y=df_medidas['gordura_corporal'],
        mode='lines+markers',
        name='Gordura Corporal (%)',
        line=dict(color='#FFC107', width=2),
        marker=dict(size=8)
    ))

    # Adicionar linha de meta de gordura corporal
    fig_comp.add_shape(
        type="line",
        x0=df_medidas['data'].min(),
        y0=metas['gordura_corporal_meta'],
        x1=df_medidas['data'].max(),
        y1=metas['gordura_corporal_meta'],
        line=dict(color="red", width=2, dash="dash"),
    )

    fig_comp.add_annotation(
        x=df_medidas['data'].max(),
        y=metas['gordura_corporal_meta'],
        text="Meta",
        showarrow=False,
        yshift=10,
        font=dict(color="red")
    )

    fig_comp.update_layout(
        title='Progresso de Gordura Corporal',
        xaxis_title='Data',
        yaxis_title='Gordura Corporal (%)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig_comp, use_container_width=True)

    # Gráfico de medidas
    fig_medidas = go.Figure()

    fig_medidas.add_trace(go.Scatter(
        x=df_medidas['data'],
        y=df_medidas['cintura'],
        mode='lines+markers',
        name='Cintura (cm)',
        line=dict(color='#6610F2', width=2),
        marker=dict(size=8)
    ))

    fig_medidas.add_trace(go.Scatter(
        x=df_medidas['data'],
        y=df_medidas['quadril'],
        mode='lines+markers',
        name='Quadril (cm)',
        line=dict(color='#E83E8C', width=2),
        marker=dict(size=8)
    ))

    fig_medidas.update_layout(
        title='Progresso de Medidas Corporais',
        xaxis_title='Data',
        yaxis_title='Medida (cm)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig_medidas, use_container_width=True)

# Inicializar a aplicação
inicializar_bd()
carregar_tabela_taco()
criar_dados_exemplo()
aplicar_estilo()

# carregar dados na sessão
st.session_state.refeicoes = obter_refeicoes_por_periodo('202-01-01')
st.session_state.metas = obter_metas()
st.session_state.medidas = obter_todas_medidas()

# Cabeçalho da aplicação
st.title("🥗 Acompanhamento Nutricional")
st.markdown("### 📊 Monitore sua alimentação e progresso corporal")
st.markdown("---")

# Menu de navegação
tabs = st.tabs(["📈 Dashboard", "🍽️ Registro Alimentar", "📏 Medidas Corporais", "🎯 Metas"])

# Tab 1: Dashboard
with tabs[0]:
    st.header("Dashboard de Acompanhamento")

    data_hoje = datetime.now().strftime('%Y-%m-%d')

    dados_iniciados = True
    try:
        df_hoje = st.session_state.refeicoes[st.session_state.refeicoes['data'] == data_hoje]
    except:
        dados_iniciados = False
    if dados_iniciados:
        # Métricas de hoje
        st.subheader("Resumo do Dia")

        # Calcular métricas do dia
        calorias_hoje = df_hoje['calorias'].sum() if not df_hoje.empty else 0
        proteinas_hoje = df_hoje['proteinas'].sum() if not df_hoje.empty else 0
        carboidratos_hoje = df_hoje['carboidratos'].sum() if not df_hoje.empty else 0
        gorduras_hoje = df_hoje['gorduras'].sum() if not df_hoje.empty else 0

        # Mostrar métricas em colunas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p>Calorias</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{calorias_hoje} kcal</p>', unsafe_allow_html=True)
            st.markdown(f'<p>Meta: {st.session_state.metas["calorias_diarias"]} kcal</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p>Proteínas</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{proteinas_hoje}g</p>', unsafe_allow_html=True)
            st.markdown(f'<p>Meta: {st.session_state.metas["proteinas_diarias"]}g</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p>Carboidratos</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{carboidratos_hoje}g</p>', unsafe_allow_html=True)
            st.markdown(f'<p>Meta: {st.session_state.metas["carboidratos_diarios"]}g</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p>Gorduras</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{gorduras_hoje}g</p>', unsafe_allow_html=True)
            st.markdown(f'<p>Meta: {st.session_state.metas["gorduras_diarias"]}g</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Gráficos de consumo
        st.subheader("Histórico de Consumo")

        # Filtro de período para os gráficos
        col_period1, col_period2 = st.columns(2)
        with col_period1:
            dias_atras = st.slider("Selecione o período de análise (dias)", 1, 30, 7)

        data_inicio = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
        df_periodo = st.session_state.refeicoes[st.session_state.refeicoes['data'] >= data_inicio]

        if not df_periodo.empty:
            gerar_grafico_consumo_diario(df_periodo)
        else:
            st.info("Sem dados de consumo no período selecionado")

        st.markdown("---")

        # Mostrar progresso corporal
        st.subheader("Progresso Corporal")

        if not st.session_state.medidas.empty:
            gerar_grafico_progresso_corporal()
        else:
            st.info("Sem dados de medidas corporais registrados")

# Tab 2: Registro Alimentar
with tabs[1]:
    st.header("Registro Alimentar")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Adicionar Nova Refeição")

        # Formulário de adição de refeição
        data_refeicao = st.date_input("Data", datetime.now()).strftime('%Y-%m-%d')
        tipo_refeicao = st.selectbox("Refeição", ["Café da Manhã", "Lanche da Manhã", "Almoço", "Lanche da Tarde", "Jantar", "Ceia"])
        alimento = st.text_input("Alimento")
        quantidade = st.number_input("Quantidade (g)", min_value=0, step=10)
        calorias = st.number_input("Calorias", min_value=0, step=10)
        proteinas = st.number_input("Proteínas (g)", min_value=0.0, step=0.1)
        carboidratos = st.number_input("Carboidratos (g)", min_value=0.0, step=0.1)
        gorduras = st.number_input("Gorduras (g)", min_value=0.0, step=0.1)

        if st.button("Adicionar Refeição"):
            adicionar_refeicao(data_refeicao, tipo_refeicao, alimento, quantidade, calorias, proteinas, carboidratos, gorduras)

    with col2:
        st.subheader("Histórico de Refeições")
        if dados_iniciados:
            # Filtro de data
            data_filtro = st.date_input("Filtrar por data", datetime.now())
            data_filtro_str = data_filtro.strftime('%Y-%m-%d')

            # Mostrar refeições filtradas
            df_filtrado = st.session_state.refeicoes[st.session_state.refeicoes['data'] == data_filtro_str]

            if not df_filtrado.empty:
                st.dataframe(df_filtrado, hide_index=True)

                # Totais do dia
                st.subheader("Totais do Dia")
                totais = df_filtrado.agg({
                    'calorias': 'sum',
                    'proteinas': 'sum',
                    'carboidratos': 'sum',
                    'gorduras': 'sum'
                }).to_frame().T

                st.dataframe(totais, hide_index=True)

                # Gráfico de distribuição de macronutrientes
                st.subheader("Distribuição de Macronutrientes")

                macros = {
                    'Nutriente': ['Proteínas', 'Carboidratos', 'Gorduras'],
                    'Quantidade (g)': [totais['proteinas'].iloc[0], totais['carboidratos'].iloc[0], totais['gorduras'].iloc[0]]
                }

                df_macros = pd.DataFrame(macros)

                fig = px.pie(df_macros, values='Quantidade (g)', names='Nutriente',
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.4)

                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Nenhuma refeição encontrada para {data_filtro_str}")

# Tab 3: Medidas Corporais
with tabs[2]:
    st.header("Registro de Medidas Corporais")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Adicionar Novas Medidas")

        # Formulário de adição de medidas
        data_medida = st.date_input("Data da Medição", datetime.now()).strftime('%Y-%m-%d')
        peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
        altura = st.number_input("Altura (cm)", min_value=0.0, step=0.5, value=170.0)
        cintura = st.number_input("Circunferência da Cintura (cm)", min_value=0.0, step=0.5)
        quadril = st.number_input("Circunferência do Quadril (cm)", min_value=0.0, step=0.5)
        gordura_corporal = st.number_input("Gordura Corporal (%)", min_value=0.0, max_value=100.0, step=0.1)

        if st.button("Salvar Medidas"):
            adicionar_medida(data_medida, peso, altura, cintura, quadril, gordura_corporal)

    with col2:
        st.subheader("Histórico de Medidas")
        if dados_iniciados:
            if not st.session_state.medidas.empty:
                st.dataframe(st.session_state.medidas.sort_values('data', ascending=False), hide_index=True)

                # Progresso
                st.subheader("Progresso")
                if len(st.session_state.medidas) >= 2:
                    primeira_medida = st.session_state.medidas.sort_values('data').iloc[0]
                    ultima_medida = st.session_state.medidas.sort_values('data').iloc[-1]

                    delta_peso = ultima_medida['peso'] - primeira_medida['peso']
                    delta_gordura = ultima_medida['gordura_corporal'] - primeira_medida['gordura_corporal']

                    col_delta1, col_delta2 = st.columns(2)

                    with col_delta1:
                        st.metric("Variação de Peso", f"{ultima_medida['peso']:.1f} kg", f"{delta_peso:.1f} kg")

                    with col_delta2:
                        st.metric("Variação de Gordura Corporal", f"{ultima_medida['gordura_corporal']:.1f}%", f"{delta_gordura:.1f}%")

            else:
                st.info("Nenhuma medida corporal registrada ainda")

# Tab 4: Metas
with tabs[3]:
    st.header("Definição de Metas")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Metas Nutricionais")
        # breakpoint()
        calorias_meta = st.number_input("Meta de Calorias Diárias (kcal)", min_value=0.0, step=50.0, value=st.session_state.metas['calorias_diarias'])
        proteinas_meta = st.number_input("Meta de Proteínas Diárias (g)", min_value=0.0, step=5.0, value=st.session_state.metas['proteinas_diarias'])
        carboidratos_meta = st.number_input("Meta de Carboidratos Diários (g)", min_value=0.0, step=5.0, value=st.session_state.metas['carboidratos_diarios'])
        gorduras_meta = st.number_input("Meta de Gorduras Diárias (g)", min_value=0.0, step=5.0, value=st.session_state.metas['gorduras_diarias'])

    with col2:
        st.subheader("Metas Corporais")

        # Corrigido: usando float para o value para corresponder ao tipo do step
        peso_meta = st.number_input("Meta de Peso (kg)", min_value=0.0, step=0.5, value=float(st.session_state.metas['peso_meta']))
        gordura_corporal_meta = st.number_input("Meta de Gordura Corporal (%)", min_value=0.0, max_value=100.0, step=0.5, value=float(st.session_state.metas['gordura_corporal_meta']))

    if st.button("Salvar Metas"):
        st.session_state.metas = {
            'calorias_diarias': calorias_meta,
            'proteinas_diarias': proteinas_meta,
            'carboidratos_diarios': carboidratos_meta,
            'gorduras_diarias': gorduras_meta,
            'peso_meta': peso_meta,
            'gordura_corporal_meta': gordura_corporal_meta
        }
        st.success("Metas atualizadas com sucesso!")

    # Exportar dados
    st.markdown("---")
    st.subheader("Exportar Dados")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        if st.button("Exportar Refeições para CSV"):
            csv = st.session_state.refeicoes.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="refeicoes.csv",
                mime="text/csv",
            )

    with col_exp2:
        if st.button("Exportar Medidas para CSV"):
            csv = st.session_state.medidas.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="medidas.csv",
                mime="text/csv",
            )