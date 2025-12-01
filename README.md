Aqui está o **README.md** completo e atualizado, incluindo a etapa de baixar o repositório.

Basta criar um arquivo chamado `README.md` na raiz do seu projeto e colar o conteúdo abaixo:

````markdown
# 📼 Wyrd Logger - Ferramenta de Teste RTLS

Este software é um "Sniffer" e Gravador de dados MQTT para testes de campo do sistema RTLS. Ele permite selecionar ESPs e Ativos específicos e gerar logs CSV organizados por teste, mantendo compatibilidade com o firmware v0.4.0.

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
Antes de começar, certifique-se de ter instalado:
* **Git** (para baixar o código).
* **Python 3.10** ou superior.
* **Mosquitto MQTT Broker** (rodando na porta padrão 1883).

### 2. Baixar o Repositório
Abra o seu terminal (ou Git Bash) na pasta onde deseja salvar o projeto e execute:

```bash
# Clone o repositório (substitua pela URL real do seu git se já tiver)
git clone [https://github.com/VPN-IND/teste_wyrd_rtls](https://github.com/VPN-IND/teste_wyrd_rtls)

# Entre na pasta do projeto
cd nome-da-pasta-do-projeto
````

> **Nota:** Se você não usa Git, pode baixar o arquivo **.ZIP** do repositório, extrair e abrir o terminal dentro da pasta extraída.

### 3\. Criar Ambiente Virtual (Venv)

O ambiente virtual isola as bibliotecas do projeto para não bagunçar seu sistema.

  * **Linux / Mac:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

  * **Windows (PowerShell):**

    ```powershell
    python -m venv venv
    venv\Scripts\activate
    ```

*(Você saberá que funcionou se aparecer `(venv)` no começo da linha do terminal).*

### 4\. Instalar Dependências

Com o ambiente ativado, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

*Caso o arquivo `requirements.txt` ainda não exista, instale manualmente:*

```bash
pip install fastapi uvicorn paho-mqtt sqlalchemy sqladmin python-multipart jinja2
```

-----

## ▶️ Como Rodar

Certifique-se de que o **Mosquitto MQTT** está rodando. Depois, na raiz do projeto (onde você vê a pasta `app/`), execute:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

  * 🖥️ **Painel de Controle:** [http://127.0.0.1:8000](https://www.google.com/search?q=http://127.0.0.1:8000)
  * ⚙️ **Configuração (Admin):** [http://127.0.0.1:8000/admin](https://www.google.com/search?q=http://127.0.0.1:8000/admin)

-----

## ⚙️ Configurando o Admin

O Admin é fundamental. O firmware das ESPs pede ao servidor uma "Whitelist" ao iniciar. **Se a ESP ou o Ativo não estiverem cadastrados aqui, a ESP não enviará dados.**

1.  Acesse **/admin** no navegador.
2.  **Embarcados:**
      * Cadastre as ESPs que você vai usar.
      * **ID ESP:** Deve ser idêntico ao gravado no firmware (ex: `WRD00000002`).
3.  **Ativos:**
      * Cadastre os Beacons que você quer rastrear.
      * **MAC Beacon:** O endereço MAC do beacon (ex: `AA:BB:CC:DD:EE:FF`).

> **Dica:** Ao iniciar o servidor (`uvicorn`), ele envia automaticamente um comando MQTT forçando todas as ESPs conectadas a baixarem a nova lista de ativos cadastrados.

-----

## 📂 Onde ficam os dados?

Ao iniciar um teste na tela principal, o sistema cria automaticamente a seguinte estrutura de pastas na raiz do projeto:

```text
testes/
  └── Nome_Do_Seu_Teste/
      ├── info.txt            # Resumo (Data, Hora, Duração, Descrição)
      ├── WRD00000002/        # Pasta da ESP específica
      │   └── aa-bb-cc...csv  # Log CSV com RSSI e WiFi
      └── WRD00000003/
          └── ...
```

```
```