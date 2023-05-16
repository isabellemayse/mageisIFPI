#importar o pysomplegui e o bacno de dados
import sqlite3
import PySimpleGUI as sg
import janela2 as j2

class Investimento:
    def __init__(self):
    # criar e ativar o banco de dados
        self.dbase = sqlite3.connect("operacoes.db")
        self.cursor = self.dbase.cursor()
        self.create_table()
        self.window = None


    # cria a tabela operacoes 
    def create_table(self):
        self.cursor.execute("""
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
        self.dbase.commit() 

    #função para limpar os campos de entrada de dados 
    def limpar_campos(self):
        self.window["data"].update("")
        self.window["ativo"].update("")
        self.window["valor_unitario"].update("")
        self.window["quantidade"].update("")
        self.window["compra"].update(True)
        self.window["venda"].update(False)
        self.window["taxa_corretora"].update("")
        self.window["data"].SetFocus()

    #função para abrir detalhes de um ativo - H2
    def abrir_detalhes_ativo(self, ativo):
        pass

    # função para calcular o valor final da operação e taxa de corretora e imposto
    def calcular_valor_final(self, valor_unitario, quantidade, taxa_corretora):
        valor_bruto = valor_unitario * quantidade
        valor_taxa = (valor_bruto * taxa_corretora) / 100
        valor_imposto = (valor_bruto * 3) / 100
        valor_final = valor_bruto + valor_taxa + valor_imposto
        return round(valor_final, 2)

    # função para inserseir as operações que o usuario deseja
    def salvar_operacao(self, data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real):
        valor_final_real = self.calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
        if compra_venda == "Compra":
            quantidade = abs(quantidade)
        else:
            quantidade = -abs(quantidade)
        
        self.cursor.execute("INSERT INTO operacoes (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real) VALUES (?, ?, ?, ?, ?, ?, ?)", (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real))
        self.dbase.commit() #aplica todas as mudanças no database
        self.limpar_campos() #limpar os campos depois de salvar

    # layout da aplicaçãõ - padrão do pysimplegui
    def criar_janela(self): 
        return [
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
    def iniciar(self):
        self.window = sg.Window("Operações com ativos", self.criar_janela())

        while True: #tem que manter a janela com um loop
            opcao, values = self.window.read()
            if opcao in (None, "Sair"):
                break
            if opcao == "Limpar campos":
                self.limpar_campos()
            if opcao == "Detalhar um ativo":
                ativo = values["ativo"]
                self.abrir_detalhes_ativo(ativo)
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
                valor_final_real = self.calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
                self.salvar_operacao(data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real)
                
                # organizar a caixa de texto com os dados inseridos
                self.cursor.execute("SELECT data, SUM(CASE WHEN compra_venda='Compra' THEN quantidade ELSE -quantidade END) as total_quantidade, SUM(CASE WHEN compra_venda='Compra' THEN valor_unitario*quantidade ELSE -valor_unitario*quantidade END) as total_valor FROM operacoes GROUP BY data ORDER BY data") 
                rows = self.cursor.fetchall()
                dados_operacoes = "\n".join([f"{row[0]} - Total de ações: {row[1]} - Total investido: {row[2]}" for row in rows])
                self.window.Element("dados_operacoes").Update(dados_operacoes)


        self.window.close()
        self.dbase.close()

aplicacao = Investimento()
aplicacao.iniciar()