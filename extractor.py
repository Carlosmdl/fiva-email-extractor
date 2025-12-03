# -*- coding: utf-8 -*-
"""
FIVA Email Extractor - Lógica Isolada
Extrai APENAS emails de PDFs de dadores, sem funcionalidades completas do FIVA
"""
import re
import datetime as dt
from typing import Tuple, Dict, List
import pdfplumber
import pandas as pd

# Domínios de email populares em Portugal
DOMINIOS_CONHECIDOS = {
    'gmail': ['.com', '.pt'],
    'hotmail': ['.com', '.pt'],
    'outlook': ['.com', '.pt'],
    'sapo': ['.pt'],
    'live': ['.com', '.pt'],
    'yahoo': ['.com', '.pt'],
    'icloud': ['.com'],
    'mail': ['.pt'],
    'iol': ['.pt'],
    'clix': ['.pt'],
    'netcabo': ['.pt']
}


class EmailProcessor:
    """Processamento e correção automática de emails."""
    
    def __init__(self):
        self.common_domains = DOMINIOS_CONHECIDOS
        self.corrections_log = []
    
    def correct_email(self, email: str) -> Tuple[str, bool]:
        """Corrige automaticamente emails com terminações malformadas."""
        if not isinstance(email, str) or not email.strip():
            return "", False
        
        original = email.strip().replace(" ", "")
        corrected = original
        was_changed = False
        
        # Padrão 1: Email termina com .co → adicionar 'm'
        if re.search(r"@[\w\.-]+\.co$", corrected, re.IGNORECASE):
            corrected = corrected + "m"
            was_changed = True
        
        # Padrão 2: Email termina com .c ou . → verificar domínio conhecido
        elif re.search(r"@([\w\.-]+)\.(c|)$", corrected, re.IGNORECASE):
            match = re.search(r"@([\w\.-]+)\.(c|)$", corrected, re.IGNORECASE)
            domain_part = match.group(1).lower()
            
            # Tentar encontrar domínio conhecido
            for known_domain, extensions in self.common_domains.items():
                if known_domain in domain_part:
                    primary_ext = extensions[0]
                    corrected = re.sub(r"\.(c|)$", primary_ext, corrected, flags=re.IGNORECASE)
                    was_changed = True
                    break
            
            # Se não encontrou domínio conhecido, assumir .com
            if not was_changed:
                corrected = re.sub(r"\.(c|)$", ".com", corrected, flags=re.IGNORECASE)
                was_changed = True
        
        # Registrar correção
        if was_changed:
            self.corrections_log.append({
                'original': original,
                'corrected': corrected
            })
        
        return corrected, was_changed
    
    def validate_email(self, email: str) -> bool:
        """Valida formato de email usando regex."""
        if not isinstance(email, str):
            return False
        
        email = email.strip().replace(" ", "")
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(pattern, email) is not None


class SimplePDFExtractor:
    """Extração simplificada de dados do PDF - apenas o essencial."""
    
    def __init__(self, email_processor: EmailProcessor):
        self.email_processor = email_processor
    
    def extrair_emails_pdf(self, caminho_pdf: str) -> pd.DataFrame:
        """Extrai dados básicos do PDF: ID, Nome, Email, Status."""
        dados = []
        status_atual = "INDEFINIDO"
        
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if not texto:
                        continue
                    
                    linhas = texto.split('\n')
                    for linha in linhas:
                        linha_upper = linha.upper()
                        
                        # Detectar mudança de seção
                        if "APTOS" in linha_upper:
                            status_atual = "APTO"
                        elif "SUSPENSOS" in linha_upper:
                            status_atual = "SUSPENSO"
                        elif "ELIMINADOS" in linha_upper:
                            status_atual = "ELIMINADO"
                        
                        # Procurar ID de dador
                        match_id = re.search(r"(S[PCL]\.[A-Z0-9]+\.\d+/\d+)", linha)
                        if match_id:
                            id_dador = match_id.group(1)
                            status = status_atual
                            
                            # Verificar status na própria linha
                            if "APTO" in linha_upper:
                                status = "APTO"
                            elif "SUSPENSO" in linha_upper:
                                status = "SUSPENSO"
                            elif "ELIMINADO" in linha_upper:
                                status = "ELIMINADO"
                            
                            # Extrair email
                            match_email = re.search(r"[\w\.\-]+@[\w\.\-]+\.[a-zA-Z0-9\.]{1,}", linha)
                            email_original = match_email.group(0) if match_email else ""
                            
                            # Corrigir email
                            email_corrigido, foi_corrigido = self.email_processor.correct_email(email_original)
                            tem_email = "Sim" if self.email_processor.validate_email(email_corrigido) else "Não"
                            
                            # Extrair nome básico
                            nome = ""
                            resto = linha[match_id.end():].strip()
                            match_nome = re.match(r"([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][A-ZÀÁÂÃÇÉÊÍÓÔÕÚa-zàáâãçéêíóôõú\s]+?)(?=\s*\d{2}/\d{2}/\d{4}|\s*\w+@|$)", resto)
                            if match_nome:
                                nome = match_nome.group(1).strip()
                            
                            # Para ELIMINADOS: extrair ano do ID
                            ano_registo = None
                            if status == "ELIMINADO":
                                match_ano = re.search(r'/(\d{2})$', id_dador)
                                if match_ano:
                                    ano_2digitos = int(match_ano.group(1))
                                    ano_registo = 2000 + ano_2digitos if ano_2digitos < 50 else 1900 + ano_2digitos
                            
                            dados.append({
                                "ID Dador": id_dador,
                                "Nome": nome,
                                "Email Original": email_original,
                                "Email Corrigido": email_corrigido,
                                "Email Foi Alterado": "Sim" if foi_corrigido else "Não",
                                "Status": status,
                                "Tem Email": tem_email,
                                "Ano Registo": ano_registo
                            })
        
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {e}")
        
        return pd.DataFrame(dados)


def gerar_lista_emails(df: pd.DataFrame, email_processor: EmailProcessor) -> str:
    """Gera ficheiro de texto com listas de emails segmentadas por status."""
    
    # Determinar ano de corte para ELIMINADOS (últimos 3 anos)
    ano_atual = dt.datetime.now().year
    if 'Ano Registo' in df.columns and not df['Ano Registo'].dropna().empty:
        ano_max_amostra = df['Ano Registo'].dropna().max()
        if ano_max_amostra > 2000:  # Validação básica
            ano_atual = int(ano_max_amostra)
    ano_corte = ano_atual - 3
    
    # Construir texto
    linhas = []
    linhas.append("=" * 80)
    linhas.append("LISTAGEM DE EMAILS PARA MAILING - FIVA Email Extractor")
    linhas.append(f"Gerado em: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("=" * 80)
    linhas.append("")
    
    # Estatísticas gerais
    total_emails_validos = len(df[df['Tem Email'] == 'Sim'])
    emails_corrigidos = len(df[df['Email Foi Alterado'] == 'Sim'])
    cobertura = (total_emails_validos / len(df) * 100) if len(df) > 0 else 0
    
    linhas.append("📊 ESTATÍSTICAS:")
    linhas.append(f"   Total de emails válidos: {total_emails_validos}")
    linhas.append(f"   Emails corrigidos automaticamente: {emails_corrigidos}")
    linhas.append(f"   Cobertura: {cobertura:.1f}%")
    linhas.append("")
    
    # Gerar listas por status
    for status in ["APTO", "SUSPENSO", "ELIMINADO"]:
        linhas.append("=" * 80)
        linhas.append(f"📧 {status}S")
        linhas.append("=" * 80)
        linhas.append("")
        
        # Aplicar filtro temporal para ELIMINADOS
        if status == "ELIMINADO":
            df_filtrado = df[df["Status"] == status].copy()
            if 'Ano Registo' in df_filtrado.columns:
                df_filtrado = df_filtrado[
                    (df_filtrado['Ano Registo'].notna()) & 
                    (df_filtrado['Ano Registo'] >= ano_corte)
                ]
            emails_status = df_filtrado[df_filtrado["Tem Email"] == "Sim"]["Email Corrigido"].unique()
            
            linhas.append(f"FILTRO APLICADO: Apenas dadores eliminados dos últimos 3 anos (>={ano_corte})")
            linhas.append(f"(Dadores eliminados antes de {ano_corte} foram excluídos para focar recursos de retenção)")
            linhas.append("")
        else:
            emails_status = df[
                (df["Status"] == status) & (df["Tem Email"] == "Sim")
            ]["Email Corrigido"].unique()
        
        if len(emails_status) > 0:
            linhas.append(f"Total: {len(emails_status)} emails")
            linhas.append("")
            linhas.append("; ".join(emails_status))
            linhas.append("")
        else:
            linhas.append("Nenhum email válido encontrado para este status.")
        
        linhas.append("")
    
    # Relatório de correções
    if emails_corrigidos > 0:
        linhas.append("=" * 80)
        linhas.append("🔧 RELATÓRIO DE CORREÇÕES APLICADAS")
        linhas.append("=" * 80)
        linhas.append("")
        
        for correcao in email_processor.corrections_log:
            linhas.append(f"   {correcao['original']} → {correcao['corrected']}")
    
    return "\n".join(linhas)


def processar_pdf_para_emails(caminho_pdf: str) -> str:
    """Função principal: processa PDF e retorna conteúdo do ficheiro de emails."""
    email_processor = EmailProcessor()
    extractor = SimplePDFExtractor(email_processor)
    
    # Extrair dados
    df = extractor.extrair_emails_pdf(caminho_pdf)
    
    if df.empty:
        raise Exception("Nenhum dado extraído do PDF. Verifique se o formato está correto.")
    
    # Gerar lista de emails
    conteudo = gerar_lista_emails(df, email_processor)
    
    return conteudo
