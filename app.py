import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

# página
st.set_page_config(layout="wide", page_title="CACI - Análise de Violência Indígena")

# carregamento
@st.cache_data
def get_data_from_db(_conn):
    """
    Carrega e processa os dados do banco de dados SQLite.
    """
    try:
        query_incidentes = """
            SELECT
                i.id_incidente, i.data_incidente, strftime('%Y', i.data_incidente) as ano,
                i.descricao, i.dia_imputado, i.mes_imputado, m.nome_municipio,
                m.sigla_uf, ti.nome_terra_indigena, f.nome_fonte
            FROM Incidentes i
            LEFT JOIN Municipios m ON i.cod_ibge = m.cod_ibge
            LEFT JOIN Terras_Indigenas ti ON i.cod_funai = ti.cod_funai
            LEFT JOIN Fontes f ON i.id_fonte = f.id_fonte
        """
        df_incidentes = pd.read_sql_query(query_incidentes, _conn)
        df_incidentes['data_incidente'] = pd.to_datetime(df_incidentes['data_incidente'])

        query_vitimas = """
            SELECT
                v.id_vitima, v.id_incidente, v.nome, v.apelido,
                v.idade, v.aldeia, p.nome_povo
            FROM Vitimas v
            LEFT JOIN Povos p ON v.id_povo = p.id_povo
        """
        df_vitimas = pd.read_sql_query(query_vitimas, _conn)

        query_violencia = """
            SELECT itv.id_incidente, tv.nome_violencia
            FROM Incidentes_Tipos_Violencia itv
            LEFT JOIN Tipos_Violencia tv ON itv.id_tipo_violencia = tv.id_tipo_violencia
        """
        df_violencia = pd.read_sql_query(query_violencia, _conn)

        tabelas_dimensao = {}
        nomes_tabelas = ["Municipios", "Terras_Indigenas", "Povos", "Fontes", "Tipos_Violencia"]
        for nome in nomes_tabelas:
            tabelas_dimensao[nome] = pd.read_sql_query(f"SELECT * FROM {nome}", _conn)

        return df_incidentes, df_vitimas, df_violencia, tabelas_dimensao
    except Exception as e:
        st.error(f"Erro ao ler os dados do banco de dados: {e}")
        return None, None, None, None

# lógica da app
DB_FILENAME = "violencia_indigena.db"
if not os.path.exists(DB_FILENAME):
    st.error(f"Erro: O arquivo do banco de dados '{DB_FILENAME}' não foi encontrado.")
    st.info("Por favor, certifique.")
else:
    conn = None
    try:
        conn = sqlite3.connect(DB_FILENAME)
        df_incidentes, df_vitimas, df_violencia, tabelas_dimensao = get_data_from_db(conn)

        if df_incidentes is not None:
            # interface
            st.title("🏹 CACI: Painel de Análise de Violência Contra Povos Indígenas")
            st.markdown("Esta aplicação permite explorar de forma interativa os dados de violência contra povos indígenas no Brasil, a partir de um banco de dados SQLite.")
            
            # sidebar
            st.sidebar.header("Filtros")
            
            # filtros
            anos = sorted(df_incidentes['ano'].dropna().unique(), reverse=True)
            ano_selecionado = st.sidebar.multiselect("Ano do Incidente", options=anos, default=anos)
            ufs = sorted(df_incidentes['sigla_uf'].dropna().unique())
            uf_selecionada = st.sidebar.multiselect("Estado (UF)", options=ufs, default=ufs)
            tipos_violencia = sorted(df_violencia['nome_violencia'].dropna().unique())
            violencia_selecionada = st.sidebar.multiselect("Tipo de Violência", options=tipos_violencia, default=tipos_violencia)

            # seções/ações sidebar
            st.sidebar.markdown("---")
            st.sidebar.header("Sobre o Painel")
            st.sidebar.info(
                """
                Este painel foi criado para dar visibilidade aos dados sobre violência
                contra povos indígenas. A análise de dados é uma ferramenta poderosa para
                compreender a dimensão dos conflitos e violações de direitos.
                
                **Cada número representa uma vida, uma história e uma comunidade.**
                """
            )

            st.sidebar.header("Links Úteis e de Apoio")
            st.sidebar.markdown(
                """
                - [APIB - Articulação dos Povos Indígenas do Brasil](https://apiboficial.org/)
                - [CIMI - Conselho Indigenista Missionário](https://cimi.org.br/)
                - [ISA - Instituto Socioambiental](https://www.socioambiental.org/)
                - [FUNAI - Fundação Nacional do Índio](https://www.gov.br/funai/pt-br)
                """
            )

            # filtragem
            df_incidentes_filtrado = df_incidentes[
                (df_incidentes['ano'].isin(ano_selecionado)) &
                (df_incidentes['sigla_uf'].isin(uf_selecionada))
            ]
            if violencia_selecionada:
                ids_filtrados = df_violencia[df_violencia['nome_violencia'].isin(violencia_selecionada)]['id_incidente'].unique()
                df_incidentes_filtrado = df_incidentes_filtrado[df_incidentes_filtrado['id_incidente'].isin(ids_filtrados)]
            
            df_vitimas_filtrado = df_vitimas[df_vitimas['id_incidente'].isin(df_incidentes_filtrado['id_incidente'])]
            df_violencia_filtrado = df_violencia[df_violencia['id_incidente'].isin(df_incidentes_filtrado['id_incidente'])]

            # tabs
            tab1, tab2, tab3 = st.tabs(["Painel Principal", "Análises Detalhadas", " Explorar Dados"])

            with tab1:
                st.header("Visão Geral do Cenário")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Incidentes Registrados", f"{df_incidentes_filtrado.shape[0]:,}")
                col2.metric("Total de Vítimas Envolvidas", f"{df_vitimas_filtrado.shape[0]:,}")
                col3.metric("Municípios Afetados", f"{df_incidentes_filtrado['nome_municipio'].nunique():,}")

                st.markdown("---")

                # relatos
                st.subheader("Vozes das Vítimas: Relatos em Destaque")
                with st.expander("Clique aqui para ler relatos de incidentes", expanded=True):
                    relatos_disponiveis = df_incidentes_filtrado['descricao'].dropna()
                    if not relatos_disponiveis.empty:
                        if 'relato_atual' not in st.session_state or st.session_state.relato_atual not in relatos_disponiveis.values:
                             st.session_state.relato_atual = relatos_disponiveis.sample(1).iloc[0]
                        def obter_novo_relato():
                            st.session_state.relato_atual = relatos_disponiveis.sample(1).iloc[0]
                        st.info(f'"{st.session_state.relato_atual}"')
                        st.button("Mostrar outro relato", on_click=obter_novo_relato, use_container_width=True)
                    else:
                        st.warning("Não há relatos disponíveis para os filtros selecionados.")
                
                st.markdown("---")
                
                # nuvem de palavras
                st.subheader("Nuvem de Palavras das Descrições")
                text = ' '.join(df_incidentes_filtrado['descricao'].dropna())
                if text:
                    stopwords = set(STOPWORDS)
                    stopwords.update(["de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "no", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "à", "seu", "sua", 
                                      "ou", "quando", "foi", "eles", "foram", "era", "se", "pelo", "pela","depois","pelos", "chegou", "há", "teve", "havía", "cerca", "disse","após", "durante", "próximo", "tinha", "ser", "já", "às margens", "estava", "sobre", "dele", "dela", 
                                      "encaminhado", "mesma", "ocasião", "ano", "dia", "onde", "até", "sem", "também", "ainda", "ela", "é", "havia", "anos"])
                    wordcloud = WordCloud(width=1200, height=600, background_color='white', stopwords=stopwords, min_font_size=10, colormap='inferno').generate(text)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.info("Não há dados de descrição suficientes para gerar a nuvem de palavras com os filtros atuais.")

            with tab2:
                st.header("Análises Quantitativas Detalhadas")
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1:
                    st.subheader("Incidentes ao Longo do Tempo")
                    incidentes_por_ano = df_incidentes_filtrado.groupby('ano').size().reset_index(name='contagem')
                    fig_ano = px.bar(incidentes_por_ano, x='ano', y='contagem', labels={'ano': 'Ano', 'contagem': 'Número de Incidentes'}, template='plotly_white')
                    st.plotly_chart(fig_ano, use_container_width=True)

                    st.subheader("Distribuição por Fonte da Informação")
                    fontes_contagem = df_incidentes_filtrado['nome_fonte'].dropna().value_counts()
                    if not fontes_contagem.empty:
                        fig_fontes = px.pie(values=fontes_contagem.values, names=fontes_contagem.index, hole=.3)
                        st.plotly_chart(fig_fontes, use_container_width=True)
                    else:
                        st.info("Não há dados sobre as fontes para os filtros selecionados.")

                    st.subheader("Top 10 Povos Afetados")
                    povos_contagem = df_vitimas_filtrado['nome_povo'].value_counts().nlargest(10).sort_values()
                    fig_povos = px.bar(povos_contagem, y=povos_contagem.index, x=povos_contagem.values, orientation='h', labels={'y': '', 'x': 'Número de Vítimas'}, template='plotly_white')
                    st.plotly_chart(fig_povos, use_container_width=True)

                with col_graf2:
                    st.subheader("Distribuição de Idade das Vítimas")
                    idades_validas = df_vitimas_filtrado['idade'].dropna()
                    if not idades_validas.empty:
                        fig_idade = px.histogram(idades_validas, x='idade', nbins=20, labels={'idade': 'Idade da Vítima'}, template='plotly_white')
                        st.plotly_chart(fig_idade, use_container_width=True)
                    else:
                        st.info("Não há dados de idade suficientes para os filtros selecionados.")

                    st.subheader("Top 10 Estados com mais Incidentes")
                    uf_contagem = df_incidentes_filtrado['sigla_uf'].value_counts().nlargest(10).sort_values()
                    fig_uf = px.bar(uf_contagem, y=uf_contagem.index, x=uf_contagem.values, orientation='h', labels={'y': '', 'x': 'Número de Incidentes'}, template='plotly_white')
                    st.plotly_chart(fig_uf, use_container_width=True)

            with tab3:
                st.header("Explore os Dados Completos")
                st.info("Nesta seção, você pode visualizar as tabelas individuais do banco de dados.")
                nome_tabela_selecionada = st.selectbox("Selecione uma tabela para explorar", options=list(tabelas_dimensao.keys()))
                if nome_tabela_selecionada:
                    st.dataframe(tabelas_dimensao[nome_tabela_selecionada], use_container_width=True)
    finally:
        if conn:
            conn.close()
