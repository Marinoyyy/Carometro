import pandas as pd
import os
from dotenv import load_dotenv
from unidecode import unidecode

# Carrega as variáveis de ambiente do ficheiro .env (para obter o seu Cloud Name)
load_dotenv()

# --- CONFIGURAÇÕES ---
# Nome da pasta onde você guardou as imagens descarregadas
PASTA_DAS_FOTOS = 'fotos_para_corrigir' 
# Nome do seu ficheiro Excel
ARQUIVO_COLABORADORES = 'Colaboradores.xlsx'
# O seu Cloud Name, lido do ficheiro .env
CLOUD_NAME = os.getenv('CLOUD_NAME')

def sync_local_filenames_to_excel():
    """
    Lê os nomes dos ficheiros de uma pasta local, constrói os URLs corretos do Cloudinary
    e atualiza a coluna 'Foto_URL' no ficheiro Excel.
    """
    print("Iniciando a correção de links a partir da pasta local...")

    if not CLOUD_NAME:
        print("\n[ERRO] A variável 'CLOUD_NAME' não foi encontrada no seu ficheiro .env.")
        print("Por favor, certifique-se de que o ficheiro .env está configurado corretamente.")
        return

    try:
        # 1. Ler todos os nomes de ficheiros da pasta local
        print(f"A ler ficheiros da pasta: '{PASTA_DAS_FOTOS}'...")
        nomes_dos_ficheiros = os.listdir(PASTA_DAS_FOTOS)
        
        # 2. Criar um dicionário para mapear o nome base ao nome completo do ficheiro
        # Ex: {'deividi-manoel-monteiro-da-silva': 'deividi-manoel-monteiro-da-silva_frrf5t.jpg'}
        mapa_de_nomes = {}
        for nome_completo in nomes_dos_ficheiros:
            # Pega na parte do nome antes do primeiro '_'
            nome_base = nome_completo.split('_')[0]
            mapa_de_nomes[nome_base] = nome_completo
        
        print(f"Encontrados {len(mapa_de_nomes)} ficheiros de imagem.")
        
        # 3. Ler o ficheiro Excel
        print(f"A ler o ficheiro: {ARQUIVO_COLABORADORES}")
        df = pd.read_excel(ARQUIVO_COLABORADORES)

        # 4. Verificar e criar a coluna 'Foto_URL' se necessário
        if 'Foto_URL' not in df.columns:
            df['Foto_URL'] = ''
            print("Coluna 'Foto_URL' criada na planilha.")

        updates_count = 0
        # 5. Iterar sobre cada colaborador na planilha
        for index, row in df.iterrows():
            nome_colaborador = row.get('Nome_completo')
            if pd.isna(nome_colaborador):
                continue

            # Gera o nome base esperado a partir do nome do colaborador
            nome_base_esperado = unidecode(nome_colaborador.lower().replace(' ', '-'))

            # Procura o nome completo do ficheiro no nosso mapa
            nome_ficheiro_real = mapa_de_nomes.get(nome_base_esperado)

            if nome_ficheiro_real:
                # Se encontrou, constrói o URL completo do Cloudinary
                url_final = f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload/{nome_ficheiro_real}"
                
                # Atualiza a coluna na planilha
                df.at[index, 'Foto_URL'] = url_final
                updates_count += 1
                print(f"  [OK] Link gerado para: {nome_colaborador}")
            else:
                print(f"  [AVISO] Nenhuma imagem encontrada na pasta para: {nome_colaborador}")

        # 6. Salvar o ficheiro Excel atualizado
        df.to_excel(ARQUIVO_COLABORADORES, index=False)
        print(f"\nCorreção concluída! {updates_count} links foram atualizados.")
        print(f"O ficheiro '{ARQUIVO_COLABORADORES}' foi salvo com sucesso.")

    except FileNotFoundError:
        print(f"\n[ERRO] A pasta '{PASTA_DAS_FOTOS}' não foi encontrada. Verifique o nome e a localização da pasta.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        print("Verifique se o ficheiro Excel não está aberto noutro programa.")

# Executa a função principal
if __name__ == "__main__":
    sync_local_filenames_to_excel()