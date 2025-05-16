# Pedala SJC - Guia de Pedalada Urbana

![Pedala SJC Logo](generated-icon.png)

## Sobre o Projeto

O Pedala SJC é um aplicativo Streamlit que gera rotas de ciclismo personalizadas para ciclistas urbanos na cidade de São José dos Campos. Com um foco especial em rotas circulares (que começam e terminam no mesmo ponto), o aplicativo leva em consideração o nível de experiência do ciclista, a distância desejada, e o estilo de pedalada preferido.

## Funcionalidades

- 🚲 **Geração de rotas circulares** com controle rigoroso de distância (tolerância máxima de 2km)
- 🗺️ **Mapa interativo** com visualização da rota completa
- 📊 **Perfil de elevação** para analisar dificuldade do terreno
- 📝 **Guia personalizado de pedalada** com dicas específicas para cada nível de ciclista
- 📄 **Geração de PDF** para download e compartilhamento do roteiro
- 🌡️ **Integração com sensores ambientais** para considerar condições climáticas

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io) - Framework para criação da interface web
- [Google Maps API](https://developers.google.com/maps) - Para geração de rotas e geocodificação
- [OpenAI API](https://openai.com) - Para geração de conteúdo personalizado e tradução
- [FAISS](https://github.com/facebookresearch/faiss) - Para busca vetorial e recomendações
- [FPDF](https://pyfpdf.readthedocs.io/en/latest/) - Para geração de PDFs
- [SQLAlchemy](https://www.sqlalchemy.org/) - Para persistência de dados

## Como Instalar

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/pedala-sjc.git
cd pedala-sjc
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Baixe os arquivos de modelo FAISS:
   - Os arquivos `vetor_univesp.pkl` e `vetor_univesp.index` não estão incluídos no repositório devido ao tamanho.
   - Eles serão baixados automaticamente na primeira execução ou você pode baixá-los manualmente:
   ```
   # URLs de download:
   # https://drive.google.com/uc?id=1-HBQCEDeJxbWQ2NBjbH1D3goA13ikDYE (vetor_univesp.index)
   # https://drive.google.com/uc?id=1YftI8E1mL78m4NxHDHwO8DgLcUGcSRxz (vetor_univesp.pkl)
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` com suas chaves de API (não compartilhe este arquivo):
   ```
   OPENAI_API_KEY=sua_chave_api_openai
   GOOGLE_MAPS_API_KEY=sua_chave_api_google_maps
   ```

5. Execute o aplicativo:
```bash
streamlit run app.py
```

## Estrutura do Projeto

### Arquivos Principais
- `app.py` - Aplicativo principal Streamlit com interface do usuário
- `db_utils.py` - Utilitários para interação com o banco de dados PostgreSQL
- `pdf_generator.py` - Geração de PDFs de roteiros para download
- `rota_simplificada.py` - Lógica para simplificação das instruções de rota
- `pedala_teste_2.py` - Processamento de dados de ciclismo e análise de condições

### Componentes Auxiliares
- `utils/echarts_helper.py` - Visualizações de dados com ECharts
- `utils/openai_helper.py` - Integração com OpenAI para geração de conteúdo
- `utils/new_gauge_chart.py` - Gráficos de medição para sensores ambientais

### Arquivos de Modelo (não incluídos no repositório)
- `vetor_univesp.index` - Índice FAISS para busca semântica
- `vetor_univesp.pkl` - Metadados para o índice FAISS

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Agradecimentos

- Comunidade ciclística de São José dos Campos
- Contribuidores do projeto