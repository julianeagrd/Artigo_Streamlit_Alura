import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# Função para plotar o gráfico (PRECISAVA SER CRIADA)
def plot_estoque(dataframe, categoria):
    # Filtra os dados para a categoria selecionada
    dados_grafico = dataframe[dataframe['Categoria'] == categoria]
    
    # Cria a figura
    fig, ax = plt.subplots()
    sns.barplot(x='Produto', y='Quantidade', data=dados_grafico, ax=ax)
    plt.xticks(rotation=45, ha='right') # Rotaciona os nomes dos produtos
    plt.title(f'Estoque de Produtos na Categoria: {categoria}')
    plt.tight_layout() # Ajusta o layout para evitar sobreposição
    
    return fig

# Função para mostrar a tabela (MOVIDA PARA ANTES DA CHAMADA)
def mostra_qntd_linhas(dataframe):
    qntd_linhas = st.sidebar.slider('Selecione a quantidade de linhas', min_value=1, max_value=len(dataframe), step=1)
    # Mostra a tabela formatada
    st.write(dataframe.head(qntd_linhas).style.format(subset=['Valor'], formatter="R$ {:.2f}"))

# --- Configuração da Página do Streamlit ---

# Título principal
st.title('Análise de Estoque de Supermercado')
st.write('Nesse projeto vamos analisar a quantidade de produtos em estoque, por categoria.')

# Carregando os dados (use um try-except para lidar com erros de arquivo)
try:
    dados = pd.read_csv('estoque.csv')
except FileNotFoundError:
    st.error("Arquivo 'estoque.csv' não encontrado. Verifique se o arquivo está na pasta correta.")
    st.stop() # Interrompe a execução se o arquivo não for encontrado

# --- Barra Lateral (Sidebar) com Filtros ---

st.sidebar.title('Filtros')

# Filtros para a tabela
if st.sidebar.checkbox('Mostrar tabela de dados'):
    st.sidebar.markdown('## Filtro para a Tabela')
    
    # Lista de categorias (CORRIGIDO: indentação)
    categorias = list(dados['Categoria'].unique())
    categorias.append('Todas')
    
    categoria_tabela = st.sidebar.selectbox('Selecione a categoria para a tabela', options=categorias)
    
    # Lógica para exibir a tabela (CORRIGIDO: indentação)
    if categoria_tabela != 'Todas':
        df_filtrado = dados[dados['Categoria'] == categoria_tabela]
        mostra_qntd_linhas(df_filtrado)
    else:
        mostra_qntd_linhas(dados)

# Filtro para o gráfico
st.sidebar.markdown('## Filtro para o Gráfico')

# Seleciona a categoria para o gráfico
categoria_grafico = st.sidebar.selectbox(
    'Selecione a categoria para o gráfico', 
    options=dados['Categoria'].unique()
)

# Exibe o gráfico na página principal
if categoria_grafico:
    st.subheader(f'Gráfico de Estoque para a Categoria: {categoria_grafico}')
    figura = plot_estoque(dados, categoria_grafico)
    st.pyplot(figura)