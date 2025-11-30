import sys
import os
import base64
import json

# Adiciona o diretório raiz ao path
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.utils import generate_keypair, sign_message, verify_signature
from logger_config import log_debug, log_error

# Cores para saída
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(text):
    """Imprime um header formatado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_step(step_num, description):
    """Imprime um passo numerado"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}[PASSO {step_num}]{Colors.RESET} {description}")

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def test_basic_signature():
    """Teste 1: Assinatura e Verificação Básica"""
    print_header("TESTE 1: ASSINATURA E VERIFICAÇÃO BÁSICA")
    
    print_step(1, "Gerando par de chaves RSA-2048...")
    private_key, public_key = generate_keypair()
    print_success(f"Chaves geradas com sucesso!")
    print(f"  • Chave privada: {len(private_key)} bytes")
    print(f"  • Chave pública: {len(public_key)} bytes")
    
    # Mensagem original
    message = "Olá, esta é uma mensagem importante!"
    print_step(2, f"Mensagem original: '{message}'")
    
    # Assina a mensagem
    print_step(3, "Assinando mensagem com chave privada...")
    signature = sign_message(message, private_key)
    print_success("Mensagem assinada!")
    print(f"  • Assinatura (base64): {signature[:50]}...")
    
    # Verifica a assinatura
    print_step(4, "Verificando assinatura com chave pública...")
    is_valid = verify_signature(message, signature, public_key)
    
    if is_valid:
        print_success("✓ Assinatura VÁLIDA - Mensagem não foi alterada!")
    else:
        print_error("✗ Assinatura INVÁLIDA - Mensagem foi alterada!")
    
    return is_valid

def test_tampered_message():
    """Teste 2: Detectar Mensagem Alterada"""
    print_header("TESTE 2: DETECTAR MENSAGEM ALTERADA")
    
    print_step(1, "Gerando par de chaves RSA-2048...")
    private_key, public_key = generate_keypair()
    print_success("Chaves geradas!")
    
    # Mensagem original
    message_original = "Transferir 100 reais para João"
    print_step(2, f"Mensagem original: '{message_original}'")
    
    # Assina
    print_step(3, "Assinando mensagem...")
    signature = sign_message(message_original, private_key)
    print_success("Mensagem assinada!")
    
    # ATAQUE: Tenta alterar a mensagem
    message_tampered = "Transferir 1000 reais para João"
    print_step(4, f"ATAQUE: Alterando mensagem para: '{message_tampered}'")
    print_warning("Atacante tenta usar a mesma assinatura para a mensagem alterada...")
    
    # Verifica com mensagem alterada
    print_step(5, "Verificando assinatura da mensagem alterada...")
    is_valid = verify_signature(message_tampered, signature, public_key)
    
    if not is_valid:
        print_success("✓ ATAQUE DETECTADO! A assinatura não corresponde à mensagem alterada!")
        print(f"  • Mensagem original:  '{message_original}'")
        print(f"  • Mensagem alterada:  '{message_tampered}'")
        print(f"  • Assinatura rejeitada: INTEGRIDADE PRESERVADA ✅")
    else:
        print_error("✗ FALHA - Assinatura aceita (isso não deveria acontecer)")
    
    return not is_valid

def test_json_message():
    """Teste 3: Assinatura de Objetos JSON (Mensagens de Chat)"""
    print_header("TESTE 3: ASSINATURA DE MENSAGENS JSON (CHAT REAL)")
    
    print_step(1, "Gerando par de chaves RSA-2048...")
    private_key, public_key = generate_keypair()
    print_success("Chaves geradas!")
    
    # Simula uma mensagem de chat criptografada
    chat_message = {
        "encrypted_message": "U2FsdGVkX1/8M7n3Q2L...[base64 encrypted]",
        "username": "alice",
        "room": "group_chat_123",
        "timestamp": "2025-11-30 15:45:32"
    }
    print_step(2, "Mensagem JSON (como em chat real):")
    print(json.dumps(chat_message, indent=2, ensure_ascii=False))
    
    # Assina
    print_step(3, "Assinando mensagem JSON...")
    signature = sign_message(chat_message, private_key)
    print_success("Mensagem assinada!")
    print(f"  • Assinatura: {signature[:60]}...")
    
    # Verifica com dados corretos
    print_step(4, "Verificando assinatura (dados corretos)...")
    is_valid_1 = verify_signature(chat_message, signature, public_key)
    
    if is_valid_1:
        print_success("✓ Assinatura válida para dados originais")
    else:
        print_error("✗ Falha na verificação")
    
    # Tenta alterar um campo
    chat_message_tampered = chat_message.copy()
    chat_message_tampered["encrypted_message"] = "U2FsdGVkX1/XXXXXXXXXXXXXXXX"
    
    print_step(5, "ATAQUE: Alterando campo 'encrypted_message'...")
    print_warning("Tentando usar a mesma assinatura...")
    
    is_valid_2 = verify_signature(chat_message_tampered, signature, public_key)
    
    if not is_valid_2:
        print_success("✓ ATAQUE DETECTADO! Mensagem alterada foi rejeitada!")
    else:
        print_error("✗ Falha - mensagem alterada foi aceita")
    
    return is_valid_1 and not is_valid_2

def test_signature_chain():
    """Teste 4: Cadeia de Assinatura (múltiplos usuários)"""
    print_header("TESTE 4: CADEIA DE ASSINATURA (MÚLTIPLOS USUÁRIOS)")
    
    print_step(1, "Gerando chaves para ALICE...")
    alice_private, alice_public = generate_keypair()
    print_success("Chaves de Alice geradas!")
    
    print_step(2, "Gerando chaves para BOB...")
    bob_private, bob_public = generate_keypair()
    print_success("Chaves de Bob geradas!")
    
    # Mensagem original de ALICE
    message = "Oi Bob, tudo bem?"
    print_step(3, f"Alice envia: '{message}'")
    
    # ALICE assina
    print_step(4, "Alice assina a mensagem com sua chave privada...")
    alice_signature = sign_message(message, alice_private)
    print_success("Mensagem assinada por Alice!")
    
    # BOB verifica com chave pública de ALICE
    print_step(5, "Bob verifica a assinatura usando chave pública de Alice...")
    is_valid = verify_signature(message, alice_signature, alice_public)
    
    if is_valid:
        print_success("✓ Bob confia que é realmente de Alice!")
        print(f"  • Remetente: Alice")
        print(f"  • Mensagem: '{message}'")
        print(f"  • Status: AUTÊNTICA E ÍNTEGRA ✅")
    else:
        print_error("✗ Falha na verificação")
    
    return is_valid

def print_summary():
    """Imprime resumo da demonstração"""
    print_header("RESUMO: PILAR DE INTEGRIDADE")
    
    print(f"{Colors.BOLD}O que foi demonstrado:{Colors.RESET}\n")
    
    print("1️⃣  ASSINATURA DIGITAL RSA")
    print("   • Cada mensagem é assinada com chave PRIVADA do remetente")
    print("   • Apenas o remetente consegue criar a assinatura")
    print("   • Impossível falsificar sem a chave privada\n")
    
    print("2️⃣  VERIFICAÇÃO DE INTEGRIDADE")
    print("   • Receptor verifica com chave PÚBLICA do remetente")
    print("   • Se mensagem foi alterada → assinatura inválida")
    print("   • Detecta tampering/interceptação\n")
    
    print("3️⃣  AUTENTICIDADE COMPROVADA")
    print("   • Só quem tem chave privada consegue assinar")
    print("   • Prova que é realmente do remetente")
    print("   • Não-repúdio: remetente não pode negar ter enviado\n")
    
    print("4️⃣  FLUXO NO CHATRSA")
    print("   • Alice: encripta + assina → envia ao servidor")
    print("   • Servidor: repassa com assinatura intacta")
    print("   • Bob: verifica assinatura → descriptografa → lê mensagem")
    print("   • Se assinatura inválida → rejeita mensagem ❌\n")
    
def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("╔" + "═"*78 + "╗")
    print("║" + "DEMONSTRAÇÃO DE INTEGRIDADE - VERIFICAÇÃO DE ASSINATURA DIGITAL".center(78) + "║")
    print("║" + "Sistema de Chat Seguro ChatRSA".center(78) + "║")
    print("╚" + "═"*78 + "╝")
    print(f"{Colors.RESET}\n")
    
    try:
        # Executa todos os testes
        result1 = test_basic_signature()
        result2 = test_tampered_message()
        result3 = test_json_message()
        result4 = test_signature_chain()
        
        # Resumo
        print_summary()
        
        # Resultado final
        if all([result1, result2, result3, result4]):
            print(f"{Colors.BOLD}{Colors.GREEN}")
            print("╔" + "═"*78 + "╗")
            print("║" + "✅ TODOS OS TESTES PASSARAM - INTEGRIDADE FUNCIONANDO PERFEITAMENTE ✅".center(78) + "║")
            print("╚" + "═"*78 + "╝")
            print(f"{Colors.RESET}\n")
            return 0
        else:
            print(f"{Colors.BOLD}{Colors.RED}")
            print("Alguns testes falharam!")
            print(f"{Colors.RESET}\n")
            return 1
            
    except Exception as e:
        print_error(f"Erro durante execução: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
