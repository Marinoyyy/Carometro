# renomear_fotos.py
import os
import pandas as pd
from unidecode import unidecode
import re

# --- CONFIGURAÇÕES ---
MODO_TESTE = False # MUDE PARA False PARA RENOMEAR DE VERDADE
ARQUIVO_EXCEL = 'Colaboradores.xlsx'
PASTA_FOTOS = os.path.join('static', 'fotos')
PALAVRAS_IGNORADAS = ['copia', 'de', 'foto', 'imagem', 'img', 'picking', 'checkout', 'expedicao', 'loja', 'reabastecimento', 'controle', 'estoque', 'recebimento', 'setor']

def limpar_texto(texto):
    texto_limpo = unidecode(texto.lower())
    texto_limpo = re.sub(r'[\W_]+', ' ', texto_limpo)
    for palavra in PALAVRAS_IGNORADAS:
        texto_limpo = texto_limpo.replace(f' {palavra} ', ' ')
    return texto_limpo.split()

print("Iniciando script inteligente para renomear fotos (v2.0)...")
try:
    df = pd.read_excel(ARQUIVO_EXCEL)
    nomes_oficiais = df['Nome_completo'].dropna().tolist()
    print(f"Encontrados {len(nomes_oficiais)} nomes na planilha.")
    fotos_na_pasta = [f for f in os.listdir(PASTA_FOTOS) if os.path.isfile(os.path.join(PASTA_FOTOS, f))]
    print(f"Encontradas {len(fotos_na_pasta)} fotos na pasta '{PASTA_FOTOS}'.\n")
except Exception as e:
    print(f"!!! ERRO ao carregar dados: {e}. Abortando.")
    exit()

renomeadas, ignoradas = 0, 0
for nome_antigo_arquivo in fotos_na_pasta:
    nome_base_arquivo, extensao = os.path.splitext(nome_antigo_arquivo)
    palavras_chave_arquivo = limpar_texto(nome_base_arquivo)
    if not palavras_chave_arquivo:
        print(f"❌ Ignorado: '{nome_antigo_arquivo}' não contém palavras-chave úteis.")
        ignoradas += 1
        continue

    melhor_match, maior_pontuacao, matches_ambiguos = None, 0, []
    for nome_oficial in nomes_oficiais:
        palavras_nome_oficial = limpar_texto(nome_oficial)
        pontuacao_atual = sum(1 for palavra_chave in palavras_chave_arquivo if palavra_chave in palavras_nome_oficial)
        if pontuacao_atual > maior_pontuacao:
            maior_pontuacao, melhor_match, matches_ambiguos = pontuacao_atual, nome_oficial, []
        elif pontuacao_atual == maior_pontuacao and maior_pontuacao > 0:
            matches_ambiguos.append(nome_oficial)

    if maior_pontuacao >= 2 and not matches_ambiguos:
        novo_nome_base = unidecode(melhor_match.lower().replace(' ', '-'))
        novo_nome_arquivo = f"{novo_nome_base}{extensao}"
        caminho_antigo, caminho_novo = os.path.join(PASTA_FOTOS, nome_antigo_arquivo), os.path.join(PASTA_FOTOS, novo_nome_arquivo)
        print(f"✔ Encontrado: '{nome_antigo_arquivo}'  -->  '{novo_nome_arquivo}' (Match: {melhor_match})")
        if not MODO_TESTE:
            try:
                os.rename(caminho_antigo, caminho_novo)
            except Exception as e:
                print(f"  └─ !!! ERRO ao renomear: {e}")
        renomeadas += 1
    elif matches_ambiguos:
        print(f"⚠ Ignorado: '{nome_antigo_arquivo}' é ambíguo. Possíveis matches: {[melhor_match] + matches_ambiguos}")
        ignoradas += 1
    else:
        print(f"❌ Ignorado: '{nome_antigo_arquivo}' não teve correspondência forte na planilha.")
        ignoradas += 1

print("\n--- Concluído! ---")
if MODO_TESTE:
    print(">>> MODO DE TESTE ATIVADO. NENHUM ARQUIVO FOI REALMENTE RENOMEADO. <<<")
print(f"Arquivos que seriam renomeados: {renomeadas}")
print(f"Arquivos ignorados: {ignoradas}")
if MODO_TESTE and renomeadas > 0:
    print("\nSe os resultados estão corretos, mude MODO_TESTE para False e rode o script novamente.")