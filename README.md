Claro\! Aqui está um **README.md** pronto para você copiar e colar na raiz do seu projeto. Ele cobre desde a instalação até o uso do Admin.

-----

# 📼 Wyrd Logger - Ferramenta de Teste RTLS

Este software é um "Sniffer" e Gravador de dados MQTT para testes de campo do sistema RTLS. Ele permite selecionar ESPs e Ativos específicos e gerar logs CSV organizados por teste.

## 🚀 Instalação e Configuração

### 1\. Pré-requisitos

  * **Python 3.10+** instalado.
  * **Mosquitto MQTT** rodando (porta 1883).

### 2\. Criar Ambiente Virtual (Venv)

Abra o terminal na pasta do projeto e execute:

```bash
# Cria a pasta 'venv'
python -m venv venv
```

### 3\. Ativar o Ambiente

  * **Linux / Mac:**
    ```bash
    source venv/bin/activate
    ```
  * **Windows (PowerShell):**
    ```powershell
    venv\Scripts\activate
    ```

*(Você saberá que funcionou se aparecer `(venv)` no começo da linha do terminal).*

### 4\. Instalar Dependências

Com o ambiente ativado, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

*(Se você ainda não gerou o requirements.txt, use: `pip install fastapi uvicorn paho-mqtt sqlalchemy sqladmin python-multipart jinja2`)*

-----

## ▶️ Como Rodar

Certifique-se de que o Broker MQTT está rodando. Depois, na raiz do projeto (onde você vê a pasta `app/`), execute:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

  * Acesse o painel principal: **[http://127.0.0.1:8000](https://www.google.com/search?q=http://127.0.0.1:8000)**
  * Acesse o painel administrativo: **[http://127.0.0.1:8000/admin](https://www.google.com/search?q=http://127.0.0.1:8000/admin)**

-----

## ⚙️ O Painel Admin

O Admin é fundamental para o funcionamento do sistema, pois **as ESPs só monitoram o que está cadastrado aqui** (via Whitelist).

1.  Acesse **/admin** no navegador.
2.  **Embarcados:**
      * Cadastre as ESPs que você vai usar no teste.
      * **ID ESP:** Deve ser idêntico ao que está no firmware (ex: `WRD00000002`).
3.  **Ativos:**
      * Cadastre os Beacons que você quer rastrear.
      * **MAC Beacon:** O endereço MAC do beacon (ex: `AA:BB:CC:DD:EE:FF`).

> **Nota:** Sempre que você adicionar novos Ativos no Admin, reinicie as ESPs (ou aguarde elas pedirem configuração) para que elas atualizem a Whitelist interna delas.

-----

## 📂 Onde ficam os dados?

Ao iniciar um teste, o sistema cria automaticamente a seguinte estrutura de pastas:

```text
testes/
  └── Nome_Do_Seu_Teste/
      ├── info.txt            # Metadados (Data, Hora, Duração, Descrição)
      ├── WRD00000002/        # Pasta da ESP
      │   └── aa-bb-cc...csv  # Log do Beacon específico
      └── WRD00000003/
          └── ...
```