import sqlite3
import PySimpleGUI as sg

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
            valor_final_real REAL,
            preco_medio REAL
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
    def abrir_detalhes_ativo(self):
        layout = [
            [sg.Text("Digite o ativo: "), sg.Input(key="ativo_input"), sg.Button("Buscar")],
            [sg.Text("Detalhes do ativo: "), sg.Multiline(key="dados_ativo", size=(85, 10), disabled=True)], 
            [sg.Button("Voltar")]
        ]

        window = sg.Window("Detalhes do ativo", layout, size=(700, 300))

        while True:
            event, values = window.read()

            if event in (None, "Voltar"):
                break
            elif event == "Buscar":
                ativo = values["ativo_input"]
                self.cursor.execute("SELECT * FROM operacoes WHERE ativo=?", (ativo,))
                rows = self.cursor.fetchall()
                dados_ativo = "\n".join([f"Data: {row[1]}, Ativo: {row[2]}, Valor unitário: {row[3]}, Quantidade: {row[4]}, Compra/Venda: {row[5]}, Taxa da corretora: {row[6]}, Valor final: {row[7]}" for row in rows])

                window.Element("dados_ativo").update(dados_ativo)

        window.close()

    # função para calcular o valor final da operação e taxa de corretora e imposto
    def calcular_valor_final(self, valor_unitario, quantidade, taxa_corretora):
        valor_bruto = valor_unitario * quantidade
        valor_taxa = (valor_bruto * taxa_corretora) / 100
        valor_imposto = (valor_bruto * 3) / 100
        valor_final = valor_bruto + valor_taxa + valor_imposto
        return round(valor_final, 2)
    
    def calcular_preco_medio(self, valor_final, quantidade, valor_unitario, compra_venda):
        if compra_venda == "Compra":
            preco_medio = (valor_final + (quantidade * valor_unitario)) / (quantidade + quantidade)
        else:
            pass
        return round(preco_medio, 2)

    # função para inserseir as operações que o usuario deseja
    def salvar_operacao(self, data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio):
        valor_final_real = self.calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
        if compra_venda == "Compra":
            quantidade = abs(quantidade)
        else:
            quantidade = -abs(quantidade)
        
        self.cursor.execute("INSERT INTO operacoes (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio))
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
            [sg.Text(" ")],
            [sg.Text("Histórico de Operações: ")], 
            [sg.Multiline(key="dados_operacoes", size=(85, 10), disabled=True)]
        ]

    #criar janela
    def iniciar(self):
        self.window = sg.Window("Operações com ativos", self.criar_janela(), size=(700, 500))

        while True: #tem que manter a janela com um loop
            opcao, values = self.window.read()
            if opcao in (None, "Sair"):
                break
            if opcao == "Limpar campos":
                self.limpar_campos()
            if opcao == "Detalhar um ativo":
                ativo = values["ativo"]
                self.abrir_detalhes_ativo()
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
                preco_medio = self.calcular_preco_medio(valor_final_real, quantidade, valor_unitario, compra_venda)
                self.salvar_operacao(data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio)
                
                # organizar a caixa de texto com os dados inseridos
                self.cursor.execute("SELECT data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio FROM operacoes")

                rows = self.cursor.fetchall()
                dados_operacoes = "\n".join([f"{row[0]} - Ativo: {row[1]} - Total investido: {row[6]} - Preço Médio: {row[7]}" for row in rows])

                self.window.Element("dados_operacoes").Update(dados_operacoes)


        self.window.close()
        self.dbase.close()

aplicacao = Investimento()
aplicacao.iniciar()


## ajustar a taxa da corretora - colocar em reais
## ordenar o historico por data
## mostrar preço medio no detalhamento