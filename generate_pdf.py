import re
import os
from fpdf import FPDF

class RFIDProjectPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, "Sistema de Controle de Acesso RFID - ESP32 + MQTT + FastAPI", align="L", ln=False)
            self.cell(0, 10, f"Pág. {self.page_no()}", align="R", ln=True)
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Documentação do Projeto - Matheus Dums", align="C")

def build_pdf(md_path, pdf_path):
    pdf = RFIDProjectPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Adicionar fontes TrueType do Windows para suporte completo a UTF-8 / acentos
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    font_italic_path = r"C:\Windows\Fonts\ariali.ttf"
    
    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        pdf.add_font("Arial", "", font_path)
        pdf.add_font("Arial", "B", font_bold_path)
        if os.path.exists(font_italic_path):
            pdf.add_font("Arial", "I", font_italic_path)
    else:
        # Fallback para as fontes padrão se as TTF do Windows não forem encontradas
        # (pode haver problemas com alguns acentos dependendo da codificação)
        pdf.add_font("Arial", "", "helvetica")
        pdf.add_font("Arial", "B", "helveticabold")
    
    # Fonte mono para blocos de código
    pdf.add_font("CourierNew", "", r"C:\Windows\Fonts\cour.ttf")
    pdf.add_font("CourierNew", "B", r"C:\Windows\Fonts\courbd.ttf")

    # Capa
    pdf.add_page()
    
    # Banner/Título principal
    pdf.ln(40)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(33, 37, 41) # Dark Gray
    pdf.multi_cell(0, 12, "SISTEMA DE CONTROLE DE ACESSO RFID", align="C")
    
    pdf.ln(10)
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(108, 117, 125) # Muted Gray
    pdf.multi_cell(0, 8, "Integração ESP32, Leitor RC522, Broker MQTT, API FastAPI e Dashboard Web em Tempo Real", align="C")
    
    pdf.ln(30)
    # Desenhar uma linha decorativa azul
    pdf.set_draw_color(0, 123, 255)
    pdf.set_line_width(1.5)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    
    pdf.ln(40)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 10, "Desenvolvedor: Matheus Dums", align="C", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, "Ano: 2026", align="C", ln=True)
    
    # Começar conteúdo
    pdf.add_page()
    pdf.set_text_color(33, 37, 41)
    
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_code_block = False
    code_content = []
    
    in_table = False
    table_headers = []
    table_rows = []
    
    in_mermaid = False
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        
        # Ignorar o bloco sequenceDiagram do Mermaid pois gera ruído visual no PDF estático
        if line.strip().startswith("```mermaid"):
            in_mermaid = True
            i += 1
            continue
        if in_mermaid:
            if line.strip() == "```":
                in_mermaid = False
                # Adicionar uma breve descrição do fluxo
                pdf.set_font("Arial", "I", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(0, 6, "[Fluxo de Comunicação: A tag é lida pelo ESP32 -> Enviada por MQTT (tags) -> Validada na API/Banco de Dados -> Enviada por WebSockets para a Dashboard e por MQTT (resposta) para feedback no ESP32]")
                pdf.set_text_color(33, 37, 41)
                pdf.ln(5)
            i += 1
            continue

        # Tratar blocos de código
        if line.strip().startswith("```"):
            if in_code_block:
                # Imprimir bloco de código acumulado
                pdf.set_font("CourierNew", "", 8.5)
                pdf.set_fill_color(245, 245, 245)
                pdf.set_draw_color(220, 220, 220)
                pdf.set_line_width(0.2)
                
                # Juntar as linhas do bloco
                code_text = "\n".join(code_content)
                # Adicionar margem interna usando multi_cell com preenchimento
                # Calculando altura do bloco
                pdf.multi_cell(0, 4.5, code_text, border=1, fill=True)
                pdf.ln(5)
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
            
        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # Tratar tabelas markdown
        if line.strip().startswith("|"):
            # Ignorar linhas de separador de tabela como |---|---|
            if "---" in line:
                i += 1
                continue
                
            parts = [p.strip() for p in line.split("|")[1:-1]]
            
            if not in_table:
                in_table = True
                table_headers = parts
            else:
                table_rows.append(parts)
            
            i += 1
            continue
        else:
            if in_table:
                # Renderizar tabela acumulada
                render_table(pdf, table_headers, table_rows)
                in_table = False
                table_headers = []
                table_rows = []
                pdf.ln(5)

        # Tratar cabeçalhos
        if line.startswith("# "):
            pdf.ln(8)
            pdf.set_font("Arial", "B", 18)
            pdf.set_text_color(0, 51, 102) # Dark Blue
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            pdf.set_text_color(33, 37, 41)
        elif line.startswith("## "):
            pdf.ln(6)
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(0, 82, 163) # Medium Blue
            pdf.cell(0, 8, line[3:], ln=True)
            pdf.ln(3)
            pdf.set_text_color(33, 37, 41)
        elif line.startswith("### "):
            pdf.ln(4)
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(33, 37, 41)
            pdf.cell(0, 6, line[4:], ln=True)
            pdf.ln(2)
        elif line.strip() == "---":
            pdf.ln(4)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
        # Tratar listas ordenadas ou não ordenadas
        elif line.strip().startswith(("* ", "- ", "1. ", "2. ", "3. ", "4. ", "5. ")):
            pdf.set_font("Arial", "", 10)
            # Substituir bullet points por caractere de bullet do Arial
            clean_line = line.strip()
            if clean_line.startswith("* ") or clean_line.startswith("- "):
                marker = "- "
                text = clean_line[2:]
            else:
                marker = clean_line.split(". ", 1)[0] + ". "
                text = clean_line.split(". ", 1)[1]
            
            # Fazer indentação
            current_x = pdf.get_x()
            pdf.set_x(current_x + 5)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(8, 6, marker)
            pdf.set_font("Arial", "", 10)
            
            # Formatando texto com bold se necessário
            render_text_with_formatting(pdf, text, 6)
            pdf.set_x(current_x)
            pdf.ln(2)
        # Linha em branco
        elif not line.strip():
            pdf.ln(2)
        # Parágrafo normal
        else:
            pdf.set_font("Arial", "", 10)
            render_text_with_formatting(pdf, line.strip(), 5)
            pdf.ln(3)
            
        i += 1
        
    # Salvar PDF
    pdf.output(pdf_path)
    print(f"PDF gerado com sucesso em: {pdf_path}")

def render_text_with_formatting(pdf, text, line_height):
    """Auxiliar para tratar negritos marcados com ** no texto inline."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Arial", "B", 10)
            # Escrever sem forçar quebra de linha imediatamente
            pdf.write(line_height, part[2:-2])
        else:
            pdf.set_font("Arial", "", 10)
            pdf.write(line_height, part)
    pdf.write(line_height, "\n")

def render_table(pdf, headers, rows):
    """Desenha uma tabela Markdown formatada."""
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 230, 242) # Azul claro para cabeçalho
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.3)
    
    # Calcular larguras proporcionais para cada coluna baseado no número de colunas
    num_cols = len(headers)
    if num_cols == 4:
        col_widths = [45, 40, 45, 60] # Larguras customizadas para tabelas de pinagem e BD
    elif num_cols == 3:
        col_widths = [50, 40, 100]
    else:
        col_widths = [190 / num_cols] * num_cols
        
    # Cabeçalho
    for idx, header in enumerate(headers):
        pdf.cell(col_widths[idx], 8, header, border=1, align="C", fill=True)
    pdf.ln()
    
    # Linhas
    pdf.set_font("Arial", "", 8.5)
    row_idx = 0
    for row in rows:
        # Alternar cores de linha para melhor leitura (zebra striping)
        if row_idx % 2 == 0:
            pdf.set_fill_color(255, 255, 255)
        else:
            pdf.set_fill_color(245, 248, 253)
            
        # Determinar altura da célula dinâmica se houver quebra de linha
        # Por simplicidade, usamos cell para linhas curtas. Se for muito longa, podemos truncar ou usar multi_cell.
        # Vamos usar multi_cell mantendo o alinhamento
        
        # Encontrar a altura máxima necessária
        max_lines = 1
        for idx, cell_text in enumerate(row):
            # Limpar formatações como ** do texto da tabela
            clean_text = cell_text.replace("**", "")
            # Estimativa de linhas
            lines_needed = max(1, int(len(clean_text) / (col_widths[idx] * 0.45)))
            if lines_needed > max_lines:
                max_lines = lines_needed
        
        row_height = max_lines * 4.5
        
        # Salvar posição X e Y inicial
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        
        for idx, cell_text in enumerate(row):
            clean_text = cell_text.replace("**", "")
            # Desenha a célula usando multi_cell para permitir quebra de texto
            pdf.set_xy(start_x + sum(col_widths[:idx]), start_y)
            pdf.multi_cell(col_widths[idx], row_height / max_lines, clean_text, border=1, align="L", fill=True)
            
        pdf.set_xy(start_x, start_y + row_height)
        row_idx += 1

if __name__ == "__main__":
    build_pdf("DOCUMENTACAO.md", "DOCUMENTACAO.pdf")
