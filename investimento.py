import sqlite3
import PySimpleGUI as sg

class Investimento:
    def __init__(self):
    # criar e ativar o banco de dados
        self.dbase = sqlite3.connect("investimentos.db")
        self.cursor = self.dbase.cursor()
        self.create_table()
        self.window = None
        self.detalhes_ativo_window = None
        self.total_compras = 0.0


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
            valor_final_real REAL NOT NULL,
            preco_medio REAL,
            lucro_prejuizo REAL
        )
        """)

        self.dbase.commit() 

    def calcular_valor_final(self, valor_unitario, quantidade, taxa_corretora):
        valor_bruto = valor_unitario * quantidade
        valor_imposto = valor_bruto * 0.0003
        valor_final = valor_bruto + taxa_corretora + valor_imposto
        return round(valor_final, 2)
    
    def buscar_operacoes_compra(self, ativo):
        #buscar no banco de dados as operações de compra do ativo
        self.cursor.execute("SELECT * FROM operacoes WHERE ativo=? AND compra_venda=?", (ativo, "Compra"))
        operacoes_compra = self.cursor.fetchall()
        return operacoes_compra

    def calcular_preco_medio(self, ativo, valor_unitario, quantidade, compra_venda):
        if compra_venda == 'Compra':
            operacoes_compra = self.buscar_operacoes_compra(ativo)
            total_quantidade = sum(row[4] for row in operacoes_compra)
            total_valor = sum(row[3] * row[4] for row in operacoes_compra)
            total_quantidade += quantidade
            total_valor += valor_unitario * quantidade
            preco_medio = total_valor / total_quantidade if total_quantidade != 0 else 0

            # Armazenar o preço médio calculado para futuras vendas
            self.ultimo_preco_medio_compra = round(preco_medio, 2)
        else:
            # Verificar se existe um preço médio de compra anterior
            if hasattr(self, 'ultimo_preco_medio_compra'):
                preco_medio = self.ultimo_preco_medio_compra
            else:
                # Buscar o preço médio das operações de compra do ativo no banco de dados
                operacoes_compra = self.buscar_operacoes_compra(ativo)
                preco_medio = sum(row[8] for row in operacoes_compra) / len(operacoes_compra) if operacoes_compra else 0

        return round(preco_medio, 2)


    def calcular_lucro_prejuizo(self, valor_unitario, quantidade, compra_venda):
        if compra_venda == 'Compra':
            self.total_compras += valor_unitario * quantidade
        else:
            if self.total_compras >= valor_unitario * quantidade:
                self.total_compras -= valor_unitario * quantidade
            else:
                lucro_prejuizo = self.total_compras - (valor_unitario * quantidade)
                self.total_compras = 0
                return -lucro_prejuizo

        return -self.total_compras

    def limpar_campos(self):
        self.window["data"].update("")
        self.window["ativo"].update("")
        self.window["valor_unitario"].update("")
        self.window["quantidade"].update("")
        self.window["compra"].update(True)
        self.window["venda"].update(False)
        self.window["taxa_corretora"].update("")
        self.window["data"].SetFocus()

    def abrir_detalhes_ativo(self):
        layout = [
            [sg.Text("Ativo:"), sg.Input(key="ativo_input"), sg.Button("Buscar"), sg.Button("Voltar")],
            [sg.Table(
                headings=["ID", "Data", "Ativo", "Valor Unitário", "Quantidade", "Compra/Venda", "Taxa da Corretora", "Valor Final", "Preço Médio", "Lucro/Prejuízo"],
                auto_size_columns=True,
                justification="center",
                num_rows=10,
                enable_events=True,
                values=[],  # Os dados serão adicionados dinamicamente
                key="dados_operacoes"
            )]
        ]

        self.detalhes_ativo_aberto = True
        self.detalhes_ativo_window = sg.Window("Detalhes do Ativo").layout(layout)

        while self.detalhes_ativo_aberto:
            event, values = self.detalhes_ativo_window.read()

            if event == "Buscar":
                ativo = values["ativo_input"]
                self.cursor.execute("SELECT * FROM operacoes WHERE ativo=?", (ativo,))
                operacoes = self.cursor.fetchall()

                preco_total = 0.0
                quantidade_total = 0

                for operacao in operacoes:
                    valor_unitario = operacao[3]
                    quantidade = operacao[4]
                    preco_total += valor_unitario * quantidade
                    quantidade_total += quantidade

                if quantidade_total != 0:
                    preco_medio = preco_total / quantidade_total
                else:
                    preco_medio = 0.0

                preco_atual = 100.0  # Substitua pelo valor atual do preço do ativo
                lucro_prejuizo = quantidade_total * (preco_atual - preco_medio)

                # Atualizar a tabela de operações com os valores do preço médio e lucro/prejuízo
                operacoes_com_valores = []
                for operacao in operacoes:
                    operacao_com_valores = list(operacao)
                    operacao_com_valores.append(preco_medio)
                    operacao_com_valores.append(lucro_prejuizo)
                    operacoes_com_valores.append(operacao_com_valores)

                self.detalhes_ativo_window["dados_operacoes"].update(values=operacoes_com_valores)

            if event == "Voltar" or event == sg.WINDOW_CLOSED:
                self.detalhes_ativo_aberto = False

        self.detalhes_ativo_window.close()
        self.detalhes_ativo_window = None

    def excluir_operacao(self, selected_id):
        row_index = selected_id # Obter o índice da linha selecionada
        selected_id = int(self.window['dados_operacoes'].Get()[row_index][0])  # Obter o ID a partir do índice da linha
        print(selected_id)
        if self.dbase:
            print("Conexão com o banco de dados estabelecida")
        else:
            print("Erro na conexão com o banco de dados")
        self.cursor.execute("DELETE FROM operacoes WHERE id=?", (selected_id,))
        self.dbase.commit()
        print("Operação de exclusão executada com sucesso")
        self.atualizar_tabela_operacoes()

    def salvar_operacao(self, data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora):
        valor_final_real = self.calcular_valor_final(valor_unitario, quantidade, taxa_corretora)
        if compra_venda == "Compra":
            quantidade = abs(quantidade)
        else:
            quantidade = -abs(quantidade)
        
        preco_medio = self.calcular_preco_medio(ativo, valor_unitario, quantidade, compra_venda)  # Calcula o preço médio
        lucro_prejuizo = self.calcular_lucro_prejuizo(valor_unitario, quantidade, compra_venda)  # Calcula o lucro/prejuízo
        
        self.cursor.execute("INSERT INTO operacoes (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio, lucro_prejuizo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio, lucro_prejuizo))
        self.dbase.commit()  # Aplica todas as mudanças no banco de dados
        self.limpar_campos()  # Limpar os campos depois de salvar
        operacao = [str(self.cursor.lastrowid), data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, preco_medio, lucro_prejuizo]
        self.atualizar_tabela_operacoes()

    def editar_operacao(self, selected_id):
        row_index = selected_id  
        selected_id = int(self.window['dados_operacoes'].Get()[row_index][0])  # Obter o ID a partir do índice da linha
        self.cursor.execute("SELECT * FROM operacoes WHERE id=?", (selected_id,))
        operacao = self.cursor.fetchone()

        if operacao is None:
            sg.popup("Operação não encontrada!")
            return

        layout = [
            [sg.Text("Data: "), sg.InputText(key="data", default_text=operacao[1])],
            [sg.Text("Ativo: "), sg.InputText(key="ativo", default_text=operacao[2])],
            [sg.Text("Valor unitário (R$):"), sg.InputText(key="valor_unitario", default_text=str(operacao[3]))],
            [sg.Text("Quantidade: "), sg.InputText(key="quantidade", default_text=str(operacao[4]))],
            [
                sg.Text("Operação: "),
                sg.Radio("Compra", group_id="compra_venda", key="compra", default=operacao[5] == "Compra"),
                sg.Radio("Venda", group_id="compra_venda", key="venda", default=operacao[5] == "Venda")
            ],
            [sg.Text("Taxa da corretora (R$):"), sg.InputText(key="taxa_corretora", default_text=str(operacao[6]))],
            [sg.Button("Salvar"), sg.Button("Cancelar")]
        ]

        janela_aberta = True
        window_editar_operacao = sg.Window("Editar Operação", layout)

        while janela_aberta:
            event, values = window_editar_operacao.read()

            if event in (None, "Cancelar"):
                break
            elif event == "Salvar":
                data = values["data"]
                ativo = values["ativo"]
                valor_unitario = float(values["valor_unitario"])
                quantidade = int(values["quantidade"])
                compra_venda = "Compra" if values["compra"] else "Venda"
                taxa_corretora = float(values["taxa_corretora"])
                valor_final_real = self.calcular_valor_final(valor_unitario, quantidade, taxa_corretora)

                self.cursor.execute("""
                    UPDATE operacoes
                    SET data=?, ativo=?, valor_unitario=?, quantidade=?, compra_venda=?, taxa_corretora=?, valor_final_real=?
                    WHERE id=?
                """, (data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora, valor_final_real, selected_id))

                self.dbase.commit()
                sg.popup("Operação atualizada com sucesso!")
                janela_aberta = False

        window_editar_operacao.close()
        self.buscar_operacoes_compra(ativo)  # Atualiza a exibição das operações na janela principal

    def carregar_operacoes(self):
        self.cursor.execute("SELECT * FROM operacoes")
        operacoes = self.cursor.fetchall()

        self.window['dados_operacoes'].update(values=[])

        for operacao in operacoes:
            self.window['dados_operacoes'].add_row(operacao)

    def criar_janela(self):
        return [
            [sg.Text("Data: "), sg.Input(key="data"), sg.CalendarButton("Selecionar", target="data", format="%d/%m/%Y")],
            [sg.Text("Ativo: "), sg.Input(key="ativo")],
            [sg.Text("Valor unitário (R$):"), sg.Input(key="valor_unitario")],
            [sg.Text("Quantidade: "), sg.Input(key="quantidade")],
            [sg.Text("Operação: "), sg.Radio("Compra", group_id=1, key="compra"), sg.Radio("Venda", group_id=1, key="venda", default=True)],
            [sg.Text("Taxa da corretora (R$):"), sg.Input(key="taxa_corretora")],
            [sg.Button("Salvar"), sg.Button("Limpar campos"), sg.Button("Sair"), sg.Button("Detalhar um ativo")],
            [sg.Text(" ")],
            [sg.Text("Histórico de Operações: ")],
            [sg.Table(
                headings=["ID", "Data", "Ativo", "Valor Unitário", "Quantidade", "Compra/Venda", "Taxa da Corretora", "Valor Final", "Preço Médio", "Lucro/Prejuízo"],
                auto_size_columns=True,
                justification="center",
                num_rows=10,
                enable_events=True,
                values=[],
                key = "dados_operacoes"
                )],
            [sg.Button("Excluir", key="Excluir"), sg.Button("Editar", key="Editar")]
        ]
    
    def atualizar_tabela_operacoes(self):
        self.cursor.execute("SELECT * FROM operacoes ORDER BY data")
        rows = self.cursor.fetchall()
        data = []

        for row in rows:
            operacao = list(row)
            preco_medio = (row[1], row[2], row[3], row[4])  # Preço médio armazenado no banco de dados
            lucro_prejuizo = (row[2], row[3], row[4])
            operacao.append(preco_medio)
            operacao.append(lucro_prejuizo)
            data.append([str(item) for item in operacao])

        self.window['dados_operacoes'].update(values=data)

    def iniciar(self):
        self.window = sg.Window("Operações com ativos", self.criar_janela())

        while True: # tem que manter a janela com um loop
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
                self.salvar_operacao(data, ativo, valor_unitario, quantidade, compra_venda, taxa_corretora)
                self.atualizar_tabela_operacoes()
            if opcao == "Excluir":
                selected_rows = values["dados_operacoes"]
                if selected_rows:
                    selected_id = selected_rows[0]  # Obter o ID diretamente
                    self.excluir_operacao(selected_id)
                    self.atualizar_tabela_operacoes()
            if opcao == "Editar":
                selected_rows = values["dados_operacoes"]
                if selected_rows:
                    selected_id = selected_rows[0]
                    self.editar_operacao(selected_id)
                    self.atualizar_tabela_operacoes()

aplicacao = Investimento()
aplicacao.iniciar()