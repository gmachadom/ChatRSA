# 📚 Guia de Documentação - ChatRSA

## 🎯 Comece Aqui

1. **[README.md](README.md)** ← **COMECE AQUI**

   - Setup e instruções básicas

   - As 3 chaves do sistema - ✅ **DOCUMENTO PRINCIPAL** - tudo o que você precisa saber2. **[README_SEGURANCA.md](README_SEGURANCA.md)** ← **LEIA ISTO** - Links para documentação completa

   - Fluxo passo-a-passo
   - Momentos cruciais

   - Segurança ao sair
   - Garantias de segurança
   - Tabelas de referência

2. **[REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md)** ← **Consulte quando precisa**
   - Perguntas frequentes e respostas
   - Cheat sheet
   - Estados rápidos

---

## 📖 Documentação Completa

| Arquivo                 | Para quê               | Ler quando                      |
| ----------------------- | ---------------------- | ------------------------------- |
| **README_SEGURANCA.md** | 📘 **GUIA COMPLETO**   | Primeira vez / Aprender sistema |
| REFERENCIA_RAPIDA.md    | 🔍 Consulta rápida     | Precisa responder rápido        |
| ARQUITETURA.md          | 🏗️ Estrutura do código | Quer entender design            |
| LOGS.md                 | 📝 Eventos de logging  | Debuggando                      |
| LOGGING_EXAMPLES.md     | 📊 Exemplos de logs    | Vendo fluxos em ação            |

---

## ⚡ Fluxo de Leitura Recomendado

### Para Usuário Final

1. [README.md](README.md) - entender o projeto
2. [README_SEGURANCA.md](README_SEGURANCA.md) - "Como funciona?"
3. Pronto para usar!

### Para Desenvolvedor

1. [README.md](README.md) - setup
2. [README_SEGURANCA.md](README_SEGURANCA.md) - entender o protocolo
3. [ARQUITETURA.md](ARQUITETURA.md) - estrutura do código
4. [LOGS.md](LOGS.md) - saber o que está acontecendo
5. Código: `server/server.py`, `client/client.py`

### Para Auditor de Segurança

1. [README_SEGURANCA.md](README_SEGURANCA.md) - **tudo**
2. [ARQUITETURA.md](ARQUITETURA.md) - implementação
3. Código completo
4. Testes (veja seção "🧪 Teste Manual Completo" em README_SEGURANCA.md)

### Para Consulta Rápida

1. [REFERENCIA_RAPIDA.md](REFERENCIA_RAPIDA.md) - FAQ
2. [README_SEGURANCA.md](README_SEGURANCA.md) - Ctrl+F para buscar

---

## 🎯 Respostas Rápidas

| Pergunta                       | Arquivo              | Seção                  |
| ------------------------------ | -------------------- | ---------------------- |
| "Como funciona o sistema?"     | README_SEGURANCA.md  | Fluxo Passo-a-Passo    |
| "Quantas chaves tem?"          | README_SEGURANCA.md  | As 3 Chaves do Sistema |
| "Quando a Session é criada?"   | README_SEGURANCA.md  | Momentos Cruciais      |
| "O que é Session Key?"         | REFERENCIA_RAPIDA.md | Chaves                 |
| "Por que é seguro?"            | README_SEGURANCA.md  | Garantias de Segurança |
| "O quê faz quando alguém sai?" | README_SEGURANCA.md  | Segurança ao Sair      |
| "Como testar?"                 | README_SEGURANCA.md  | Teste Manual Completo  |

---

## 📊 Documento Principal

### README_SEGURANCA.md - Sumário

```
1. Visão Geral
2. As 3 Chaves do Sistema
   - RSA Privada (Identidade)
   - RSA Pública (Identidade)
   - Session Key (Conversa)
   - ChaCha20 (Mensagens)
3. Fluxo Passo-a-Passo
   - Fase 1: Registro
   - Fase 2: Amizade
   - Fase 3: Convite
   - Fase 4: Primeira entrada
   - Fase 5: Segunda entrada
   - Fase 6: Mensagens
4. Momentos Cruciais
   - Quando Session é criada
   - Troca de chaves
   - Criptografia de mensagens
   - Logout e invalidação
5. Segurança ao Sair
   - Proteção em camadas
6. Garantias de Segurança
   - Sigilo
   - Integridade
   - Autenticidade
   - Não-repúdio
7. Tabelas de referência
8. Teste manual
```

---

## 🚀 Comece Agora

```bash
# 1. Leia o setup
cat README.md

# 2. Entenda a segurança
cat README_SEGURANCA.md

# 3. Quando tiver dúvida rápida
cat REFERENCIA_RAPIDA.md

# 4. Se quer debug
cat LOGS.md
```

---

## 💡 Dica: Buscar no Documento Principal

`README_SEGURANCA.md` tem **tudo**. Se não sabe por onde começar:

1. Ctrl+F para buscar sua pergunta
2. Provavelmente a resposta está lá
3. Se não estiver, procure em REFERENCIA_RAPIDA.md

Exemplos:

- "quando" → Momentos Cruciais
- "chave" → As 3 Chaves do Sistema
- "sai" → Segurança ao Sair
- "seguro" → Garantias de Segurança

---

## ✅ Checklist antes de usar

- [ ] Leu README.md
- [ ] Entendeu que tudo está em README_SEGURANCA.md
- [ ] Fez o setup (pip install, flask db upgrade, etc)
- [ ] Rodou o servidor
- [ ] Rodou o Streamlit
- [ ] Testou com 2 usuários
- [ ] Confirmou que um consegue descriptografar as mensagens do outro

Pronto! Seu chat seguro está funcionando! 🔐
