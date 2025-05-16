# Arquivos FAISS para o Pedala SJC

Os arquivos FAISS são essenciais para o funcionamento do aplicativo, mas são muito grandes para serem incluídos diretamente neste repositório.

## Arquivos necessários
- `vetor_univesp.index` (aproximadamente 350MB)
- `vetor_univesp.pkl` (aproximadamente 17MB)

## Como obter os arquivos

O aplicativo está configurado para baixar automaticamente esses arquivos do Google Drive quando necessário. A função `download_file_from_google_drive()` em `pedala_teste_2.py` faz isso usando os links públicos:

```python
# URLs dos arquivos FAISS no Google Drive
INDEX_URL = "https://drive.google.com/file/d/1cs4c3Uwvn1sEyG4_Dc8rkscJeaxeh4TO/view?usp=share_link"
PKL_URL = "https://drive.google.com/file/d/1YT_OgYIzPh9P72cLhtEeLDnkxYKov6Ku/view?usp=share_link"
```

## Como funciona

Na primeira execução do aplicativo, esses arquivos serão baixados automaticamente para:
- `/vetor_univesp.index`
- `/vetor_univesp.pkl`

Se você precisar desses arquivos para desenvolvimento local, pode baixá-los diretamente dos links acima ou usar o módulo `gdown` do Python conforme implementado no aplicativo.