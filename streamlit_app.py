# -*- coding: utf-8 -*-
"""
FIVA Email Extractor - Streamlit Version
Aplicação web ultra-simples para utilizadores não-técnicos
Deploy gratuito em Streamlit Cloud
"""
import streamlit as st
import tempfile
import os
from datetime import datetime
from extractor import processar_pdf_para_emails

# Configuração da página
st.set_page_config(
    page_title="FIVA Email Extractor",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: transparent;
    }
    div[data-testid="stFileUploader"] {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(44, 62, 80, 0.1);
    }
    h1 {
        color: white !important;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🏥 FIVA Email Extractor")
st.markdown('<p class="subtitle">Extração rápida de emails de PDFs de dadores</p>', unsafe_allow_html=True)

# Container principal
with st.container():
    st.markdown("---")
    
    # Upload de ficheiro
    uploaded_file = st.file_uploader(
        "📄 Selecione ou arraste o ficheiro PDF",
        type=['pdf'],
        help="Apenas ficheiros PDF são permitidos. Máximo 50MB."
    )
    
    if uploaded_file is not None:
        # Mostrar info do ficheiro
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📁 Ficheiro: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
        
        # Validar tamanho
        if file_size_mb > 50:
            st.markdown('<div class="error-box">⚠️ <b>Erro:</b> Ficheiro demasiado grande. O tamanho máximo é 50MB.</div>', unsafe_allow_html=True)
        else:
            # Botão de processar
            if st.button("🚀 Extrair Emails", type="primary", use_container_width=True):
                with st.spinner("⏳ A processar PDF... Por favor aguarde."):
                    try:
                        # Guardar temporariamente
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Processar PDF
                        conteudo_emails = processar_pdf_para_emails(tmp_path)
                        
                        # Limpar ficheiro temporário
                        os.unlink(tmp_path)
                        
                        # Mostrar sucesso
                        st.markdown('<div class="success-box">✅ <b>Sucesso!</b> Emails extraídos com sucesso.</div>', unsafe_allow_html=True)
                        
                        # Preparar download
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"Emails_Mailing_{timestamp}.txt"
                        
                        # Botão de download
                        st.download_button(
                            label="📥 Download Emails_Mailing.txt",
                            data=conteudo_emails.encode('utf-8'),
                            file_name=filename,
                            mime="text/plain",
                            type="primary",
                            use_container_width=True
                        )
                        
                        # Preview do conteúdo
                        with st.expander("👁️ Pré-visualizar conteúdo"):
                            st.text(conteudo_emails[:1000] + "\n\n[... conteúdo truncado ...]")
                        
                    except Exception as e:
                        st.markdown(f'<div class="error-box">⚠️ <b>Erro ao processar PDF:</b><br>{str(e)}</div>', unsafe_allow_html=True)
                        st.error("💡 **Dica:** Verifique se o PDF tem o formato correto de dadores (secções APTOS, SUSPENSOS, ELIMINADOS).")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: rgba(255,255,255,0.8); font-size: 0.9rem;'>
        🏥 FIVA v3.0 • Enfermagem Comunitária<br>
        Dados processados localmente e eliminados automaticamente
    </div>
""", unsafe_allow_html=True)

# Sidebar (informações)
with st.sidebar:
    st.markdown("## ℹ️ Informação")
    st.markdown("""
    **O que esta app faz?**
    
    Extrai listas de emails de PDFs de dadores, segmentadas por status:
    - ✅ APTOS
    - ⏸️ SUSPENSOS  
    - ❌ ELIMINADOS (últimos 3 anos)
    
    **Funcionalidades:**
    - Correção automática de emails
    - Filtro temporal inteligente
    - Relatório de correções
    
    **Segurança:**
    - Ficheiros processados temporariamente
    - Sem armazenamento de dados
    - Privacidade garantida
    """)
    
    st.markdown("---")
    st.markdown("**📞 Suporte:** FIVA 3.0")
