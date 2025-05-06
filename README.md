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

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` com suas chaves de API (não compartilhe este arquivo):
   ```
   OPENAI_API_KEY=sua_chave_api_openai
   GOOGLE_MAPS_API_KEY=sua_chave_api_google_maps
   ```

4. Execute o aplicativo:
```bash
streamlit run app.py
```

## Estrutura do Projeto

- `app.py` - Aplicativo principal Streamlit
- `db_utils.py` - Utilitários para interação com o banco de dados
- `pdf_generator.py` - Geração de PDFs de roteiros
- `rota_simplificada.py` - Lógica para simplificação das instruções de rota
- `utils/` - Módulos de utilidades e componentes

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Agradecimentos

- Comunidade ciclística de São José dos Campos
- Contribuidores do projeto