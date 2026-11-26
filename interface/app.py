from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='Escola de Artes Marciais | Análise', page_icon='🥋', layout='wide')
ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / 'entrega-final'
@st.cache_data
def ler(path):
    return pd.read_csv(path, encoding='utf-8-sig', keep_default_na=False, dtype={'id_aluno': str})
try:
    base = ler(ROOT / 'Base_Escola.csv')
    tabelas = {n: ler(FINAL / f'{n}_final.csv') for n in ['dados_tratados','correcoes','rejeitados','alunos','turmas','planos','pagamentos','frequencias','graduacoes']}
    baixa = ler(FINAL / 'baixa_manual_exemplo.csv')
except (OSError, ValueError) as e:
    st.error(f'Não foi possível carregar os arquivos: {e}. Coloque a pasta interface dentro do repositório completo.')
    st.stop()
d = tabelas['dados_tratados']; c = tabelas['correcoes']; r = tabelas['rejeitados']
a = tabelas['alunos']; p = tabelas['pagamentos'].merge(a[['id_aluno','modalidade','nome']], on='id_aluno', validate='one_to_one')
f = tabelas['graduacoes'].merge(a[['id_aluno','modalidade','nome']], on='id_aluno', validate='one_to_one')

def inteiro(n): return f'{n:,.0f}'.replace(',', '.')
def decimal(n): return f'{n:,.1f}'.replace(',', '_').replace('.', ',').replace('_', '.')
def reais(n): return 'R$ '+f'{n:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
def pct(n,total): return decimal(100*n/total) if total else '0,0'
def metricas(items):
    for col,(label,value) in zip(st.columns(len(items)),items): col.metric(label,value)
def barras(s, titulo, horizontal=False):
    df=s.rename('Quantidade').rename_axis('Categoria').reset_index()
    fig=px.bar(df,x='Quantidade' if horizontal else 'Categoria',y='Categoria' if horizontal else 'Quantidade',orientation='h' if horizontal else 'v',text_auto=True,title=titulo,color_discrete_sequence=['#087F8C'])
    fig.update_layout(showlegend=False,margin=dict(l=10,r=15,t=55,b=10),height=360)
    if horizontal: fig.update_yaxes(autorange='reversed')
    st.plotly_chart(fig,use_container_width=True)
def tabela(df,nome):
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button('Baixar CSV',df.to_csv(index=False).encode('utf-8-sig'),nome+'.csv','text/csv',key=nome)
def nota(txt):
    st.markdown('**Leitura dos resultados**')
    st.write(txt)

st.sidebar.title('🥋 Escola de Artes Marciais')
st.sidebar.caption('Projeto de tratamento de dados')
pagina=st.sidebar.radio('Navegação',['Visão geral','Qualidade dos dados','Alunos e modalidades','Pagamentos','Frequência e graduação','Explorar arquivos','Validação e conclusão'])
st.sidebar.divider()
st.sidebar.caption('Base fictícia • Referência: 02/11/2026')
st.sidebar.caption('Os resultados não representam a escola real.')
st.title(pagina)
st.caption('Tratamento de dados com Python e Pandas | Entrega final')

if pagina=='Visão geral':
    metricas([('Registros lidos',inteiro(len(base))),('Aproveitados',inteiro(len(d))),('Rejeitados',inteiro(len(r))),('Registros corrigidos',inteiro(c.linha.nunique()))])
    st.progress(len(d)/len(base) if len(base) else 0,text=f'{pct(len(d),len(base))}% da base aproveitada')
    x,y=st.columns(2)
    with x: barras(pd.Series({'Sem correção':len(d)-c.linha.nunique(),'Com correção':c.linha.nunique(),'Rejeitados':len(r)}),'Resultado do tratamento')
    with y: barras(d.modalidade.value_counts(),'Distribuição por modalidade')
    nota(f'Dos {inteiro(len(base))} registros de entrada, {inteiro(len(d))} foram aproveitados. O algoritmo registrou {inteiro(len(c))} alterações de campos. Registros corrigidos fazem parte dos aproveitados, não são uma categoria adicional.')
    st.subheader('Etapas do projeto')
    st.write('Leitura da base → Padronização → Validação → Separação dos registros → Classificação → Exportação e análise.')
    st.info('A entrega parcial gerou uma tabela consolidada. A final separou as informações em tabelas e acrescentou verificações e uma demonstração de baixa manual.')
elif pagina=='Qualidade dos dados':
    metricas([('Rejeitados',inteiro(len(r))),('Taxa de rejeição',pct(len(r),len(base))+'%'),('Campos corrigidos',inteiro(len(c)))])
    barras(r.motivo.value_counts(),'Motivo principal das rejeições',True)
    barras(c.campo.value_counts(),'Campos alterados',True)
    nota('Cada linha rejeitada recebe um motivo principal, conforme a ordem das validações. As correções padronizam texto, valores e datas sem inventar informações obrigatórias.')
    t1,t2=st.tabs(['Antes e depois','Registros rejeitados'])
    with t1:
        campos=st.multiselect('Campos corrigidos',sorted(c.campo.unique()),default=sorted(c.campo.unique()))
        tabela(c[c.campo.isin(campos)],'correcoes_filtradas')
    with t2:
        motivos=st.multiselect('Motivos',sorted(r.motivo.unique()),default=sorted(r.motivo.unique()))
        tabela(r[r.motivo.isin(motivos)],'rejeitados_filtrados')
        linha=st.selectbox('Consultar linha original',r.linha.tolist())
        st.dataframe(base.iloc[[int(linha)-2]],hide_index=True,use_container_width=True)
elif pagina=='Alunos e modalidades':
    modos=st.multiselect('Modalidades',sorted(d.modalidade.unique()),default=sorted(d.modalidade.unique()))
    z=d[d.modalidade.isin(modos)]
    metricas([('Alunos',inteiro(len(z))),('Combinações de turma',inteiro(len(z[['modalidade','turma']].drop_duplicates()))),('Valores de mensalidade',inteiro(z.valor_mensalidade.nunique()))])
    x,y=st.columns(2)
    with x: barras(z.modalidade.value_counts(),'Alunos por modalidade')
    with y: barras(z.faixa_atual.value_counts(),'Distribuição de faixas')
    nota('Turmas e planos são categorias identificadas na base fictícia, não uma confirmação da estrutura da escola real.')
    busca=st.text_input('Buscar nome ou ID')
    tabela(z[z.nome.str.contains(busca,case=False,regex=False)|z.id_aluno.str.contains(busca,regex=False)],'alunos_filtrados')
elif pagina=='Pagamentos':
    modos=st.multiselect('Modalidades',sorted(p.modalidade.unique()),default=sorted(p.modalidade.unique()))
    meses=st.multiselect('Mês de referência',sorted(p.mes_referencia.unique()),default=sorted(p.mes_referencia.unique()))
    z=p[p.modalidade.isin(modos)&p.mes_referencia.isin(meses)]
    atras=z[z.situacao_pagamento.eq('Atrasado')]; pagos=z[z.situacao_pagamento.eq('Pago')]
    metricas([('Pagos',inteiro(len(pagos))),('Em aberto',inteiro(z.situacao_pagamento.eq('Em aberto').sum())),('Atrasados',inteiro(len(atras)))])
    metricas([('Principal atrasado',reais(atras.valor_mensalidade.sum())),('Multa simulada',reais(atras.multa_estimada.sum())),('Pagos após vencimento',inteiro(pagos.pago_apos_vencimento.eq('Sim').sum()))])
    barras(z.situacao_pagamento.value_counts(),'Situação das cobranças')
    nota(f'No recorte selecionado, {pct(len(atras),len(z))}% das cobranças estão atrasadas. A classificação usa 02/11/2026 e a multa de 2% é apenas uma regra de teste.')
    status=st.multiselect('Filtrar situação na tabela',['Pago','Em aberto','Atrasado'],default=['Pago','Em aberto','Atrasado'])
    tabela(z[z.situacao_pagamento.isin(status)],'pagamentos_filtrados')
    with st.expander('Demonstração de baixa manual realizada no notebook'):
        st.write('Antes da confirmação:'); st.dataframe(p[p.id_pagamento.isin(baixa.id_pagamento)],hide_index=True)
        st.write('Depois da confirmação:'); st.dataframe(baixa,hide_index=True)
        st.caption('Exemplo salvo separadamente; não altera a base original.')
elif pagina=='Frequência e graduação':
    modos=st.multiselect('Modalidades',sorted(f.modalidade.unique()),default=sorted(f.modalidade.unique()))
    z=f[f.modalidade.isin(modos)]; atingiu=z.atingiu_frequencia_minima.eq('Sim').sum()
    metricas([('Frequência média',decimal(z.frequencia_percentual.mean())+'%' if len(z) else '—'),('Mediana',decimal(z.frequencia_percentual.median())+'%' if len(z) else '—'),('Atingiram 75%',inteiro(atingiu)),('Abaixo de 75%',inteiro(len(z)-atingiu))])
    faixas=pd.cut(z.frequencia_percentual,[-1,50,75,90,101],right=False,labels=['Abaixo de 50%','50% a <75%','75% a <90%','90% a 100%'])
    barras(faixas.value_counts(sort=False),'Distribuição da frequência')
    nota('O percentual é calculado a partir de presenças e quantidade de aulas. Atingir 75% permite indicar uma possível avaliação pelo professor, mas não aprova automaticamente uma graduação.')
    situacao=st.selectbox('Indicador',['Todos','Sim','Não'])
    tabela(z if situacao=='Todos' else z[z.atingiu_frequencia_minima.eq(situacao)],'graduacoes_filtradas')
elif pagina=='Explorar arquivos':
    opcoes={'Base original':base,**tabelas,'baixa_manual_exemplo':baixa}
    nome=st.selectbox('Escolha uma tabela',list(opcoes)); z=opcoes[nome]
    st.caption(f'{inteiro(len(z))} linhas • {len(z.columns)} colunas')
    busca=st.text_input('Buscar em qualquer coluna')
    if busca: z=z[z.astype(str).apply(lambda s:s.str.contains(busca,case=False,regex=False)).any(axis=1)]
    tabela(z,'consulta_'+nome.replace(' ','_'))
    doc=ROOT/'DICIONARIO_DADOS.md'
    if doc.exists():
        with st.expander('Dicionário de dados'): st.markdown(doc.read_text(encoding='utf-8-sig'))
else:
    st.subheader('Conferência dos arquivos publicados')
    checks={'Entrada = aproveitados + rejeitados':len(base)==len(d)+len(r),'IDs tratados únicos':d.id_aluno.is_unique,'Tabelas individuais com mesma quantidade':len(a)==len(p)==len(f)==len(tabelas['frequencias']),'IDs de turma válidos':a.id_turma.isin(tabelas['turmas'].id_turma).all(),'IDs de plano válidos':a.id_plano.isin(tabelas['planos'].id_plano).all(),'Frequência entre 0 e 100':f.frequencia_percentual.between(0,100).all(),'Situações de pagamento válidas':p.situacao_pagamento.isin(['Pago','Em aberto','Atrasado']).all()}
    for nome,ok in checks.items():
        if ok: st.success(nome)
        else: st.error(nome)
    st.caption('Estas conferências são feitas pelo painel sobre os CSVs; são diferentes das 12 verificações do notebook.')
    resumo=FINAL/'resumo_final.txt'
    if resumo.exists():
        with st.expander('Resumo original do notebook'): st.code(resumo.read_text(encoding='utf-8-sig'),language=None)
    st.subheader('Análise final e limitações')
    doc=ROOT/'ANALISE_FINAL.md'
    if doc.exists(): st.markdown(doc.read_text(encoding='utf-8-sig'))
    else: st.write('A base é fictícia e as regras de multa e frequência precisam ser validadas antes de uso real.')
