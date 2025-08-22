import pandas as pd
import json
import os
import time
from unidecode import unidecode
from flask import Flask, jsonify, render_template, request, url_for, redirect
from datetime import datetime 
import traceback
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Inicialização da aplicação Flask
app = Flask(__name__)

# --- CONFIGURAÇÃO DO CLOUDINARY ---
cloudinary.config(
    cloud_name = os.getenv('CLOUD_NAME'),
    api_key = os.getenv('API_KEY'),
    api_secret = os.getenv('API_SECRET')
)

# --- CONFIGURAÇÕES E CONSTANTES GLOBAIS ---
ARQUIVO_COLABORADORES = 'Colaboradores.xlsx'
ARQUIVO_AVALIACOES = 'avaliacoes.json'
ARQUIVO_INSIGNIAS = 'insignias_colaboradores.json'
ARQUIVO_PDI = 'pdi_colaboradores.json'
ARQUIVO_HISTORICO = 'historico_avaliacoes.json'

# Estrutura de Atributos e Sub-atributos
ESTRUTURA_ATRIBUTOS = {
    'Tecnica': ['Uso do Sistema', 'Ferramentas', 'Maestria no setor', 'Conhecimento do processo', 'Somos Inquietos'],
    'Agilidade': ['Velocidade de entrega', 'Ritmo de Execução', 'Somos apaixonados pela execução', 'Pró-atividade'],
    'Comportamento': ['Engajamento', 'Relacionamento-interpessoal', 'Influencia no time', 'nutrimos nossas relações'],
    'Adaptabilidade': ['apoio', 'Resolução de problemas', 'Resiliencia', 'Flexibilidade'],
    'Qualidade': ['buscamos o sucesso responsável', 'fazemos os olhos dos nossos clientes brilharem', 'Qualidade', 'Segurança', 'Foco'],
    'Regularidade': ['Absenteísmo', 'Regularidade']
}

# Mapeamento de Ícones
ICON_MAP = {
    'Tecnica': 'fa-solid fa-gears', 'Agilidade': 'fa-solid fa-bolt-lightning', 'Comportamento': 'fa-solid fa-handshake-angle',
    'Adaptabilidade': 'fa-solid fa-shuffle', 'Qualidade': 'fa-solid fa-gem', 'Regularidade': 'fa-solid fa-calendar-check'
}

# Pesos para o cálculo do Overall
PESOS = {
    'Picking':       {'Tecnica': 3, 'Agilidade': 5, 'Comportamento': 4, 'Adaptabilidade': 3, 'Qualidade': 3, 'Regularidade': 4},
    'Checkout':      {'Tecnica': 3, 'Agilidade': 5, 'Comportamento': 4, 'Adaptabilidade': 3, 'Qualidade': 5, 'Regularidade': 4},
    'Expedicao':     {'Tecnica': 2, 'Agilidade': 4, 'Comportamento': 4, 'Adaptabilidade': 2, 'Qualidade': 4, 'Regularidade': 4},
    'Loja':          {'Tecnica': 3, 'Agilidade': 3, 'Comportamento': 4, 'Adaptabilidade': 3, 'Qualidade': 4, 'Regularidade': 4},
    'Reabastecimento':{'Tecnica': 4, 'Agilidade': 4, 'Comportamento': 4, 'Adaptabilidade': 4, 'Qualidade': 5, 'Regularidade': 4},
    'Controle de Estoque':{'Tecnica': 5, 'Agilidade': 2, 'Comportamento': 4, 'Adaptabilidade': 5, 'Qualidade': 5, 'Regularidade': 4},
    'Recebimento':   {'Tecnica': 4, 'Agilidade': 3, 'Comportamento': 4, 'Adaptabilidade': 4, 'Qualidade': 5, 'Regularidade': 4},
    'DEFAULT':       {'Tecnica': 1, 'Agilidade': 1, 'Comportamento': 1, 'Adaptabilidade': 1, 'Qualidade': 1, 'Regularidade': 1}
}

# Insígnias
INSIGNIAS_DISPONIVEIS = {
    "precisao": {"icone": "fa-solid fa-crosshairs", "titulo": "Precisão", "descricao": "Executa tarefas com altíssimo nível de acerto, minimizando erros."},
    "velocista": {"icone": "fa-solid fa-person-running", "titulo": "Velocista", "descricao": "Possui um ritmo de execução consistentemente acima da média."},
    "guardiao": {"icone": "fa-solid fa-shield-halved", "titulo": "Guardião da Qualidade", "descricao": "Zela pelos padrões de qualidade, garantindo a excelência na entrega."},
    "organizador": {"icone": "fa-solid fa-sitemap", "titulo": "Organizador", "descricao": "Mantém o ambiente de trabalho e os processos sempre organizados."},
    "resolvedor": {"icone": "fa-solid fa-check-to-slot", "titulo": "Resolvedor", "descricao": "Encontra soluções criativas e eficazes para problemas complexos."},
    "mentor": {"icone": "fa-solid fa-chalkboard-user", "titulo": "Mentor", "descricao": "Ajuda ativamente no desenvolvimento e no suporte de outros colegas."},
    "autodidata": {"icone": "fa-solid fa-robot", "titulo": "Autodidata", "descricao": "Busca constantemente aprender e se aprimorar de forma independente."},
    "comunicador": {"icone": "fa-solid fa-comments", "titulo": "Comunicador", "descricao": "Possui habilidades excepcionais de comunicação e relacionamento."},
    "inovador": {"icone": "fa-solid fa-lightbulb", "titulo": "Inovador", "descricao": "Propõe novas ideias e melhorias para os processos existentes."},
    "polivalente": {"icone": "fa-solid fa-star", "titulo": "Polivalente", "descricao": "Adapta-se com facilidade a diferentes funções e desafios."},
    "consistencia": {"icone": "fa-solid fa-calendar-check", "titulo": "Consistência", "descricao": "Exemplo de regularidade, presença e pontualidade."}
}

# --- FUNÇÕES AUXILIARES ---
def carregar_dados_json(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}

def salvar_dados_json(data, arquivo):
    with open(arquivo, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

def calcular_overall_com_notas(notas_sub_atributos, processo_colaborador):
    medias_principais = {}
    for attr_principal, sub_attrs in ESTRUTURA_ATRIBUTOS.items():
        soma_sub = sum(notas_sub_atributos.get(sub, 50) for sub in sub_attrs)
        media = round(soma_sub / len(sub_attrs)) if sub_attrs else 50
        medias_principais[attr_principal] = media
    setor = str(processo_colaborador).upper() if isinstance(processo_colaborador, str) and processo_colaborador.strip() else 'DEFAULT'
    pesos_upper = {k.upper(): v for k, v in PESOS.items()}
    pesos_setor = pesos_upper.get(setor, pesos_upper.get('DEFAULT'))
    numerador = sum(medias_principais.get(k, 50) * v for k, v in pesos_setor.items())
    denominador = sum(pesos_setor.values())
    return round(numerador / denominador) if denominador > 0 else 50

def calcular_overall_individual(colaborador, pesos_gerais):
    medias_principais = {item['nome_principal']: item['valor_principal'] for item in colaborador['atributos_detalhados']}
    processo_colaborador = colaborador.get('Processo')
    setor_atual = str(processo_colaborador).upper() if isinstance(processo_colaborador, str) and processo_colaborador.strip() else 'DEFAULT'
    pesos_upper = {k.upper(): v for k, v in pesos_gerais.items()}
    pesos_setor = pesos_upper.get(setor_atual, pesos_upper.get('DEFAULT'))
    numerador = sum(medias_principais.get(k, 50) * v for k, v in pesos_setor.items())
    denominador = sum(pesos_setor.values())
    return round(numerador / denominador) if denominador > 0 else 50

def get_cor_por_pontuacao(pontuacao):
    if pontuacao >= 80: return '#28a745'
    if pontuacao >= 60: return '#ffc107'
    return '#dc3545'
    
def converter_score_para_estrelas(score):
    if score >= 90: return 5
    if score >= 80: return 4
    if score >= 70: return 3
    if score >= 60: return 2
    if score > 0: return 1
    return 0

# --- FUNÇÃO PRINCIPAL DE PROCESSAMENTO DE DADOS ---
def get_dados_completos():
    try:
        df = pd.read_excel(ARQUIVO_COLABORADORES)
    except FileNotFoundError:
        return []
        
    if 'Processo' in df.columns: df = df[df['Processo'] != 'Desligado']
    if 'Cargo' not in df.columns or 'Nome_completo' not in df.columns: return [] 
    
    df['Cargo'] = df['Cargo'].fillna('').astype(str).str.strip()
    df['Nome_completo'] = df['Nome_completo'].fillna('').astype(str).str.strip()
    df = df[df['Nome_completo'] != '']
    df_filtrado = df[df['Cargo'].isin(['Operacional', 'Op Empilhadeira'])].copy()
    
    df_filtrado['id'] = range(1, len(df_filtrado) + 1)
    df_filtrado['Turno_Num'] = pd.to_numeric(df_filtrado['Turno'].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
    
    avaliacoes_atuais = carregar_dados_json(ARQUIVO_AVALIACOES)
    insignias_atribuidas = carregar_dados_json(ARQUIVO_INSIGNIAS)
    pdi_colaboradores = carregar_dados_json(ARQUIVO_PDI)
    colaboradores = df_filtrado.to_dict('records')

    for c in colaboradores:
        if 'Foto_URL' in c and isinstance(c['Foto_URL'], str) and c['Foto_URL'].strip():
            c['foto'] = c['Foto_URL']
        else:
            c['foto'] = f"https://ui-avatars.com/api/?name={c['Nome_completo'].replace(' ', '+')}&background=cccccc&color=000000&size=150"
        
        notas_sub_atributos = avaliacoes_atuais.get(c['Nome_completo'], {})
        c['atributos_detalhados'] = []
        for attr_principal, sub_attrs in ESTRUTURA_ATRIBUTOS.items():
            soma_sub = sum(notas_sub_atributos.get(sub, 50) for sub in sub_attrs)
            media = round(soma_sub / len(sub_attrs)) if sub_attrs else 50
            c['atributos_detalhados'].append({
                'nome_principal': attr_principal, 'valor_principal': media, 'cor': get_cor_por_pontuacao(media),
                'icone': ICON_MAP.get(attr_principal, ''), 'sub_atributos': [{'nome': sub, 'valor': notas_sub_atributos.get(sub, 50)} for sub in sub_attrs]
            })
        c['insignias'] = insignias_atribuidas.get(c['Nome_completo'], [])
        c['pdi'] = pdi_colaboradores.get(c['Nome_completo'], [])
    
    return colaboradores

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def dashboard_setores():
    colaboradores = get_dados_completos()
    setores_info = {}
    config_setores = {
        'Picking': {'icone': 'fa-solid fa-cart-shopping', 'cor': '#007bff'}, 'Checkout': {'icone': 'fa-solid fa-cash-register', 'cor': '#011E38'},
        'Expedicao': {'icone': 'fa-solid fa-truck-fast', 'cor': '#ff5ec9'}, 'Recebimento': {'icone': 'fa-solid fa-boxes-packing', 'cor': '#011E38'},
        'Reabastecimento': {'icone': 'fa-solid fa-warehouse', 'cor': '#264FEC'}, 'Controle de Estoque': {'icone': 'fa-solid fa-clipboard-list', 'cor': '#011E38'},
        'Loja': {'icone': 'fa-solid fa-store', 'cor': '#264FEC'}, 'DEFAULT': {'icone': 'fa-solid fa-question-circle', 'cor': '#6c757d'}
    }
    for c in colaboradores:
        setor = c.get('Processo', 'Sem Setor')
        if setor not in setores_info:
            setores_info[setor] = {"nome": setor, "contagem": 0, **config_setores.get(setor, config_setores['DEFAULT'])}
        setores_info[setor]["contagem"] += 1
    return render_template('dashboard.html', setores=list(setores_info.values()))

@app.route('/setor/<nome_setor>')
def selecao_turno(nome_setor):
    return render_template('selecao_turno.html', nome_setor=nome_setor)

@app.route('/setor/<nome_setor>/turno/<int:num_turno>')
def grid_colaboradores(nome_setor, num_turno):
    colaboradores = get_dados_completos()
    equipe_filtrada = [c for c in colaboradores if c.get('Processo') == nome_setor and c.get('Turno_Num') == num_turno]
    role = request.args.get('role', 'visualizador')
    return render_template('setor_grid.html', equipe=equipe_filtrada, nome_setor=nome_setor, num_turno=num_turno, role=role)

# Em app.py, substitua a função detalhe_colaborador

@app.route('/colaborador/<int:colaborador_id>')
def detalhe_colaborador(colaborador_id):
    colaboradores = get_dados_completos()
    colaborador = next((c for c in colaboradores if c['id'] == colaborador_id), None)
    if not colaborador: return "Colaborador não encontrado", 404
    
    overall = calcular_overall_individual(colaborador, PESOS)
    if isinstance(colaborador.get('Turno'), str):
        colaborador['Turno_Num'] = int(colaborador['Turno'].split('º')[0])
    else:
        colaborador['Turno_Num'] = 0
    
    overall_cor = get_cor_por_pontuacao(overall)
    role = request.args.get('role', 'visualizador')

    # --- INÍCIO DA NOVA LÓGICA DE SIMULAÇÃO ---
    overalls_preview = []
    medias_principais = {item['nome_principal']: item['valor_principal'] for item in colaborador['atributos_detalhados']}
    
    for setor, pesos_setor in PESOS.items():
        if setor != 'DEFAULT' and setor != colaborador.get('Processo'):
            numerador = sum(medias_principais.get(k, 50) * v for k, v in pesos_setor.items())
            denominador = sum(pesos_setor.values())
            overall_simulado = round(numerador / denominador) if denominador > 0 else 50
            
            overalls_preview.append({
                'setor': setor,
                'overall': overall_simulado
            })
    # Ordena a lista pelo maior overall simulado
    overalls_preview = sorted(overalls_preview, key=lambda x: x['overall'], reverse=True)
    # --- FIM DA NOVA LÓGICA ---

    return render_template(
        'colaborador_detalhe.html', 
        colaborador=colaborador, 
        overall=overall, 
        overall_cor=overall_cor, 
        role=role,
        insignias_disponiveis=INSIGNIAS_DISPONIVEIS,
        overalls_preview=overalls_preview, # Passa os dados da simulação para o template
        get_cor_por_pontuacao=get_cor_por_pontuacao # Passa a função de cor para o template
    )

@app.route('/adicionar_colaborador', methods=['GET', 'POST'])
def adicionar_colaborador():
    if request.method == 'POST':
        try:
            nome_completo = request.form.get('nome_completo').strip()
            dados_formulario = {
                'Nome_completo': nome_completo, 'Cargo': request.form.get('cargo'),
                'Processo': request.form.get('processo'), 'Turno': request.form.get('turno'),
                'Lider': request.form.get('lider')
            }
            foto = request.files.get('foto')
            foto_url_para_salvar = None
            if foto and foto.filename != '':
                nome_base = unidecode(nome_completo.lower().replace(' ', '-'))
                upload_result = cloudinary.uploader.upload(
                    foto, public_id=nome_base, overwrite=True, unique_filename=False
                )
                foto_url_para_salvar = upload_result.get('secure_url')
            
            df = pd.read_excel(ARQUIVO_COLABORADORES)
            if foto_url_para_salvar:
                dados_formulario['Foto_URL'] = foto_url_para_salvar

            if nome_completo in df['Nome_completo'].values:
                for key, value in dados_formulario.items():
                    df.loc[df['Nome_completo'] == nome_completo, key] = value
            else:
                novo_df = pd.DataFrame([dados_formulario])
                df = pd.concat([df, novo_df], ignore_index=True)
            
            df.to_excel(ARQUIVO_COLABORADORES, index=False)
            return redirect(url_for('dashboard_setores'))
        except Exception as e:
            print(f"ERRO AO ADICIONAR/ATUALIZAR COLABORADOR: {e}")
            traceback.print_exc()
            return "Ocorreu um erro.", 500
    setores = [setor for setor in PESOS.keys() if setor != 'DEFAULT']
    return render_template('adicionar_colaborador.html', setores=setores)

@app.route('/colaborador/<int:colaborador_id>/mudar_setor', methods=['GET', 'POST'])
def mudar_setor(colaborador_id):
    df_completo = pd.read_excel(ARQUIVO_COLABORADORES)
    # A lógica para encontrar o colaborador precisa buscar na planilha completa
    colaborador_linha = df_completo.loc[df_completo.index[df_completo['Nome_completo'] == request.args.get('nome_completo')]] if 'nome_completo' in request.args else df_completo.iloc[colaborador_id-1] # Fallback por ID se nome não for passado
    if colaborador_linha.empty:
        return "Colaborador não encontrado", 404
    colaborador = colaborador_linha.to_dict('records')[0]
    
    todos_setores = [setor for setor in PESOS.keys() if setor != 'DEFAULT']
    todos_setores.append("Desligado")
    
    if request.method == 'POST':
        novo_setor = request.form.get('novo_setor')
        try:
            df_completo.loc[df_completo['Nome_completo'] == colaborador['Nome_completo'], 'Processo'] = novo_setor
            df_completo.to_excel(ARQUIVO_COLABORADORES, index=False)
            return redirect(url_for('dashboard_setores'))
        except Exception as e:
            print(f"ERRO AO ATUALIZAR A PLANILHA: {e}")
            return "Ocorreu um erro ao salvar a alteração.", 500
            
    return render_template('mudar_setor.html', colaborador=colaborador, todos_setores=todos_setores)

@app.route('/detalhamento')
def detalhamento_geral():
    colaboradores = get_dados_completos()
    for c in colaboradores:
        c['overall'] = calcular_overall_individual(c, PESOS)
    dados_agrupados = {}
    for c in colaboradores:
        turno = c.get('Turno', 'N/A')
        processo = c.get('Processo', 'N/A')
        if turno not in dados_agrupados: dados_agrupados[turno] = {}
        if processo not in dados_agrupados[turno]: dados_agrupados[turno][processo] = []
        dados_agrupados[turno][processo].append(c)
    stats_times = {}
    for turno, processos in dados_agrupados.items():
        if turno not in stats_times: stats_times[turno] = []
        for processo, membros in processos.items():
            membros_ordenados = sorted(membros, key=lambda x: x['overall'], reverse=True)
            dados_agrupados[turno][processo] = membros_ordenados
            media_overall_time = sum(m['overall'] for m in membros) / len(membros) if membros else 0
            estrelas_time = converter_score_para_estrelas(media_overall_time)
            stats_times[turno].append({'nome_setor': processo, 'media_overall': round(media_overall_time), 'estrelas': estrelas_time})
        stats_times[turno] = sorted(stats_times[turno], key=lambda x: x['media_overall'], reverse=True)
    return render_template('detalhamento_geral.html', dados_agrupados=dados_agrupados, stats_times=stats_times)

@app.route('/matriz_talentos/<nome_setor>/<int:num_turno>')
def matriz_talentos(nome_setor, num_turno):
    colaboradores = get_dados_completos()
    equipe_filtrada = [c for c in colaboradores if c.get('Processo') == nome_setor and c.get('Turno_Num') == num_turno]
    matriz = [[[], [], []], [[], [], []], [[], [], []]]
    titulos_matriz = [["Enigma", "Forte Desempenho", "Alto Potencial"], ["Questionável", "Mantenedor", "Forte Desempenho"], ["Inadequado", "Questionável", "Risco"]]
    def get_posicao(score):
        if score >= 80: return 2
        if score >= 60: return 1
        return 0
    for c in equipe_filtrada:
        atributos = {item['nome_principal']: item['valor_principal'] for item in c['atributos_detalhados']}
        score_tecnica = atributos.get('Tecnica', 0)
        score_comportamento = atributos.get('Comportamento', 0)
        pos_x, pos_y = get_posicao(score_comportamento), get_posicao(score_tecnica)
        matriz[2 - pos_y][pos_x].append(c)
    return render_template('matriz_talentos.html', matriz=matriz, titulos=titulos_matriz, nome_setor=nome_setor, num_turno=num_turno)

@app.route('/comparador')
def comparador():
    colaboradores = get_dados_completos()
    colaboradores_ordenados = sorted(colaboradores, key=lambda x: x['Nome_completo'])
    return render_template('comparador.html', colaboradores=colaboradores_ordenados)


# --- ROTAS DA API ---
@app.route('/api/salvar_avaliacao', methods=['POST'])
def salvar_avaliacao_api():
    dados = request.json
    nome_colaborador = dados.get('nome_completo')
    processo_colaborador = dados.get('processo')
    sub_atributos_recebidos = dados.get('sub_atributos', {})
    sub_atributos_para_salvar = {chave: int(valor) for chave, valor in sub_atributos_recebidos.items()}
    avaliacoes_atuais = carregar_dados_json(ARQUIVO_AVALIACOES)
    avaliacoes_atuais[nome_colaborador] = sub_atributos_para_salvar
    salvar_dados_json(avaliacoes_atuais, ARQUIVO_AVALIACOES)
    overall_calculado = calcular_overall_com_notas(sub_atributos_para_salvar, processo_colaborador)
    historico_geral = carregar_dados_json(ARQUIVO_HISTORICO)
    if nome_colaborador not in historico_geral:
        historico_geral[nome_colaborador] = []
    novo_registro = {"data": datetime.now().strftime('%Y-%m-%d'), "overall": overall_calculado, "sub_atributos": sub_atributos_para_salvar}
    historico_geral[nome_colaborador].append(novo_registro)
    salvar_dados_json(historico_geral, ARQUIVO_HISTORICO)
    return jsonify({'status': 'sucesso', 'mensagem': f'Avaliação de {nome_colaborador} salva!'})

@app.route('/api/colaborador/<int:colaborador_id>/historico')
def get_historico_colaborador(colaborador_id):
    colaboradores = get_dados_completos()
    colaborador = next((c for c in colaboradores if c['id'] == colaborador_id), None)
    if not colaborador:
        return jsonify({"erro": "Colaborador não encontrado"}), 404
    nome_completo = colaborador['Nome_completo']
    historico_geral = carregar_dados_json(ARQUIVO_HISTORICO)
    historico_do_colaborador = historico_geral.get(nome_completo, [])
    return jsonify(historico_do_colaborador)

@app.route('/api/colaborador/<int:colaborador_id>/salvar_insignias', methods=['POST'])
def salvar_insignias_api(colaborador_id):
    dados = request.json
    nome_colaborador = dados.get('nome_completo')
    ids_insignias = dados.get('insignias', [])
    if not nome_colaborador:
        return jsonify({'status': 'erro', 'mensagem': 'Nome do colaborador não fornecido.'}), 400
    insignias_gerais = carregar_dados_json(ARQUIVO_INSIGNIAS)
    insignias_gerais[nome_colaborador] = ids_insignias
    salvar_dados_json(insignias_gerais, ARQUIVO_INSIGNIAS)
    return jsonify({'status': 'sucesso', 'mensagem': 'Insígnias salvas com sucesso!'})

@app.route('/api/colaborador/pdi', methods=['POST'])
def gerir_pdi_api():
    dados = request.json
    nome_colaborador = dados.get('nome_completo')
    acao = dados.get('acao')
    if not nome_colaborador or not acao:
        return jsonify({'status': 'erro', 'mensagem': 'Dados insuficientes.'}), 400
    pdi_geral = carregar_dados_json(ARQUIVO_PDI)
    pdi_do_colaborador = pdi_geral.get(nome_colaborador, [])
    if acao == 'adicionar':
        nova_acao = {"id": int(time.time()), "descricao": dados.get('descricao', 'Ação não descrita'), "prazo": dados.get('prazo', ''), "status": "A Fazer"}
        pdi_do_colaborador.append(nova_acao)
        pdi_geral[nome_colaborador] = pdi_do_colaborador
        salvar_dados_json(pdi_geral, ARQUIVO_PDI)
        return jsonify({'status': 'sucesso', 'mensagem': 'Ação adicionada ao PDI!', 'nova_acao': nova_acao})
    elif acao == 'atualizar_status':
        pdi_id, novo_status = dados.get('pdi_id'), dados.get('novo_status')
        for item in pdi_do_colaborador:
            if item.get('id') == pdi_id: item['status'] = novo_status; break
        pdi_geral[nome_colaborador] = pdi_do_colaborador
        salvar_dados_json(pdi_geral, ARQUIVO_PDI)
        return jsonify({'status': 'sucesso', 'mensagem': 'Status da ação atualizado!'})
    elif acao == 'apagar':
        pdi_id = dados.get('pdi_id')
        pdi_do_colaborador = [item for item in pdi_do_colaborador if item.get('id') != pdi_id]
        pdi_geral[nome_colaborador] = pdi_do_colaborador
        salvar_dados_json(pdi_geral, ARQUIVO_PDI)
        return jsonify({'status': 'sucesso', 'mensagem': 'Ação apagada do PDI!'})
    return jsonify({'status': 'erro', 'mensagem': 'Ação desconhecida.'}), 400

@app.route('/api/comparar', methods=['POST'])
def api_comparar():
    try:
        ids_selecionados = request.json.get('ids', [])
        if not 2 <= len(ids_selecionados) <= 4:
            return jsonify({"erro": "Selecione de 2 a 4 colaboradores."}), 400
        ids_selecionados = [int(id_str) for id_str in ids_selecionados]
        colaboradores_todos = get_dados_completos()
        colaboradores_selecionados = [c for c in colaboradores_todos if c['id'] in ids_selecionados]
        cards_data_serializable = []
        for c in colaboradores_selecionados:
            colaborador_limpo = {}
            for key, value in c.items():
                if hasattr(value, 'item'): colaborador_limpo[key] = value.item()
                elif pd.isna(value): colaborador_limpo[key] = None
                else: colaborador_limpo[key] = value
            colaborador_limpo['overall'] = calcular_overall_individual(colaborador_limpo, PESOS)
            cards_data_serializable.append(colaborador_limpo)
        dados_grafico = {'labels': list(ESTRUTURA_ATRIBUTOS.keys()), 'datasets': []}
        cores = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8', '#6f42c1']
        for i, c in enumerate(cards_data_serializable):
            dataset = {
                'label': c['Nome_completo'].split(' ')[0],
                'data': [item['valor_principal'] for item in c['atributos_detalhados']],
                'backgroundColor': cores[i % len(cores)]
            }
            dados_grafico['datasets'].append(dataset)
        return jsonify({'cards_data': cards_data_serializable, 'chart_data': dados_grafico})
    except Exception as e:
        print(f"ERRO na API /api/comparar: {e}")
        traceback.print_exc()
        return jsonify({"erro": "Ocorreu um erro interno no servidor."}), 500

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)