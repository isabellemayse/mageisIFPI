#importar o pysomplegui e o bacno de dados
import sqlite3
import PySimpleGUI as sg

# criar e ativar o banco de dados
dbase = sqlite3.connect("operacoes.db")
cursor = dbase.cursor()

# cria a tabela operacoes 
cursor.execute("""
CREATE TABLE IF NOT EXISTS operacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    data TEXT NOT NULL,
    ativo TEXT NOT NULL,
    valor_unitario REAL NOT NULL,
    quantidade INTEGER NOT NULL,
    compra_venda TEXT NOT NULL,
    taxa_corretora REAL NOT NULL,
    valor_final_real REAL
)
""")

dbase.commit() 

#bloco de funções

#função para limpar os campos de entrada de dados 
def limpar_campos():
    window["data"].update("")
    window["ativo"].update("")
    window["valor_unitario"].update("")
    window["quantidade"].update("")
    window["compra"].update(True)
    window["venda"].update(False)
    window["taxa_corretora"].update("")
    window["data"].SetFocus()

#função para abrir detalhes de um ativo - H2
def abrir_detalhes_ativo(ativo):
    pass

# função para calcular o valor final da operação e taxa de corretora e imposto
def calcular_valor_final(valor_unitario, quantidade, taxa_corretora):
    valor_bruto = valor_unitario * quantidade
    valor_taxa = (valor_bruto * taxa_corretora) / 100
    valor_imposto = (valor_bruto * 3) / 100
    valor_final = valor_bruto + valor_taxa + valor_imposto
    return round(valor_final, 2)

# função para inserseir as operações que o usuario deseja
def salvar_operacao(data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real):
    valor_final_real = calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
    if compra_venda == "Compra":
        quantidade = abs(quantidade)
    else:
        quantidade = -abs(quantidade)
    
    cursor.execute("INSERT INTO operacoes (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real) VALUES (?, ?, ?, ?, ?, ?, ?)", (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real))
    dbase.commit() #aplica todas as mudanças no database



# layout da aplicaçãõ - padrão do pysimplegui
layout = [
    [sg.Text("Data: "), sg.InputText(key="data")],
    [sg.Text("Ativo: "), sg.InputText(key="ativo")],
    [sg.Text("Valor unitário: (R$)"), sg.InputText(key="valor_unitario")],
    [sg.Text("Quantidade: "), sg.InputText(key="quantidade")],
    [sg.Text("Operação: "), sg.Radio("Compra", group_id=1, key="compra"), sg.Radio("Venda", group_id=1, key="venda", default=True)],
    [sg.Text("Taxa da corretora: (%)"), sg.InputText(key="taxa_corretora")],
    [sg.Text("Taxa de Imposto: 3%")],
    [sg.Button("Salvar"), sg.Button("Limpar campos"), sg.Button("Sair"), sg.Button("Detalhar um ativo")], #detalahr ainda não aplicado
    [sg.Text("Histórico de Operações: "), sg.Multiline(key="dados_operacoes", size=(50, 5), disabled=True)]
]

#criar janela
window = sg.Window("Operações com ativos", layout)

while True: #tem que manter a janela com um loop
    opcao, values = window.read()
    if opcao in (None, "Sair"):
        break
    if opcao == "Limpar campos":
        limpar_campos()
    if opcao == "Detalhar um ativo":
        ativo = values["ativo"]
        abrir_detalhes_ativo(ativo)
    if opcao == "Salvar":
        data = values["data"]
        ativo = values["ativo"]
        valor_unitario = float(values["valor_unitario"])
        quantidade = int(values["quantidade"])
        if values["compra"]:
            compra_venda = "Compra"
        else:
            compra_venda = "Venda"
        taxa_corretora = float(values["taxa_corretora"])
        valor_final_real = calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
        salvar_operacao(data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real)
        
        # organizar a caixa de texto com os dados inseridos
        cursor.execute("SELECT data, SUM(CASE WHEN compra_venda='Compra' THEN quantidade ELSE -quantidade END) as total_quantidade, SUM(CASE WHEN compra_venda='Compra' THEN valor_unitario*quantidade ELSE -valor_unitario*quantidade END) as total_valor FROM operacoes GROUP BY data ORDER BY data") #revisar esse
        rows = cursor.fetchall()
        dados_operacoes = "\n".join([f"{row[0]} - Total de ações: {row[1]} - Total investido: {row[2]}" for row in rows])
        window.Element("dados_operacoes").Update(dados_operacoes)

#encerar

window.close()
dbase.close()