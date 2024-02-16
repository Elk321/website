import streamlit as st
from st_files_connection import FilesConnection
import pandas as pd
from google.cloud import storage
from datetime import datetime
import json

conn = st.connection("gcs", type=FilesConnection)
credentials = dict(st.secrets.google.cloud.storage.credentials)
credentials = json.dumps(credentials)


def upload_file(filename, data):
    storage_client = storage.Client(credentials)
    bucket = storage_client.get_bucket("bartabacchi_website")
    blob = bucket.blob(filename)
    blob.upload_from_string(data.to_csv(index=False), "text/csv")


def check_file_exists(filename):
    storage_client = storage.Client(credentials)
    bucket = storage_client.get_bucket("bartabacchi_website")
    blob = bucket.blob(filename)
    return blob.exists()


def float_format(number):
    if number == " ":
        return " "
    else:
        number = float(number)
        return "{:.2f}".format(number).replace(".", ",")


def update_debt_list(name, amount, username):
    lista_tabacchi = conn.read("bartabacchi_website/lista/"
                               "lista_debiti_tabacchi.csv",
                               input_format="csv", ttl=3)
    lista_mirko = conn.read("bartabacchi_website/lista/"
                            "lista_debiti_mirko.csv",
                            input_format="csv", ttl=3)
    total = amount
    if name in lista_tabacchi["nome"].unique():
        row_number = (lista_tabacchi.index.get_loc
                      (lista_tabacchi[lista_tabacchi["nome"] == name]
                       .index[0]))
        lista_tabacchi.at[row_number, "totale"] += amount
        total = lista_tabacchi.at[row_number, "totale"]
        if (lista_tabacchi.at[row_number, "totale"] >
                lista_tabacchi.at[row_number, "limite"]):
            st.warning("Attenzione! Questo soggetto ha "
                       "superato il limite!")
    else:
        lista_tabacchi.loc[-1] = [name, amount, " "]

    upload_file("lista/lista_debiti_tabacchi.csv",
                lista_tabacchi)

    if name in lista_mirko["nome"].unique():
        row_number = (lista_mirko.index.get_loc
                      (lista_mirko[lista_mirko["nome"] == name]
                       .index[0]))
        lista_mirko.at[row_number, "totale"] += amount
        if (lista_mirko.at[row_number, "totale"] >
                lista_mirko.at[row_number, "limite"]):
            st.warning("Attenzione! Questo soggetto "
                       "ha superato il limite!")
    elif username == "mirko":
        if name in lista_tabacchi["nome"].unique():
            lista_tabacchi = conn.read("bartabacchi_website/lista/"
                                       "lista_debiti_tabacchi.csv",
                                       input_format="csv", ttl=3)
            row_number = (lista_tabacchi.index.get_loc
                          (lista_tabacchi[lista_tabacchi["nome"] == name]
                           .index[0]))
            amount = lista_tabacchi.at[row_number, "totale"]
            limite = lista_tabacchi.at[row_number, "limite"]
            lista_mirko.loc[-1] = [name, amount, limite]
        else:
            lista_mirko.loc[-1] = [name, amount, " "]

        upload_file("lista/lista_mirko.csv", lista_mirko)

    return total


def debt_journal(name, amount, object, date, hour, current_total):
    if not check_file_exists(f"nomi/{name}.csv"):
        debt_list = pd.DataFrame(columns=["debiti", "pagati", "oggetto",
                                          "data", "ore", "totale"])
        upload_file(f"nomi/{name}.csv", debt_list)
    debt_list = conn.read(f"bartabacchi_website/nomi/{name}.csv",
                          input_format="csv", ttl=3)
    if amount > 0:
        debt_list.loc[-1] = [amount, " ", object, date,
                             hour, current_total]
    else:
        debt_list.loc[-1] = [" ", amount, object, date,
                             hour, current_total]
    upload_file(f"nomi/{name}.csv", debt_list)


def check_blacklist(name):
    blacklist = conn.read("bartabacchi_website/lista/lista_nera.csv")
    name = name.lower()
    if name in blacklist["nome"].unique():
        st.warning("Attenzione!!! Questo soggetto è nella lista nera.")


def add_blacklist(name):
    blacklist = conn.read("bartabacchi_website/lista/lista_nera.csv")
    lista_tabacchi = conn.read("bartabacchi_website/lista/"
                               "lista_debiti_tabacchi.csv",
                               input_format="csv", ttl=3)
    name = name.lower()
    row_number = (lista_tabacchi.index.get_loc
                  (lista_tabacchi[lista_tabacchi["nome"] == name]
                   .index[0]))
    limite = lista_tabacchi.at[row_number, "limite"]
    if limite == 0:
        blacklist.loc[-1] = name
    upload_file("lista/lista_nera.csv", blacklist)


def add_name(name, username):
    name_list = conn.read("bartabacchi_website/lista/name_list.csv",
                          input_format="csv", ttl=3)
    if not (name in name_list["nome"].unique()):
        if username == "mirko":
            name_list.loc[-1] = [name, "m"]

        else:
            name_list.loc[-1] = [name, " "]
    upload_file("lista/name_list.csv", name_list)


def add_debt_current(filename, name, amount, object, hour):
    debt_list = conn.read(f"bartabacchi_website/{filename}", input_format="csv", ttl=3)
    if amount > 0:
        debt_list.loc[-1] = [name, float_format(amount), " ", object, hour]
    else:
        if not object:
            object = " "
        debt_list.loc[-1] = [name, " ", float_format(amount), object, hour]
    upload_file(filename, debt_list)


def show_debt(filename):
    if check_file_exists(filename):
        debt_list = conn.read(f"bartabacchi_website/{filename}",
                              input_format="csv", ttl=3)
        if not debt_list.empty:
            height = (len(debt_list) + 1) * 35 + 3
            st.dataframe(debt_list,
                         hide_index=True,
                         column_config={
                             "nome": "Nome",
                             "debiti": "Debiti",
                             "pagati": "Pagati",
                             "oggetto": "Oggetto",
                             "ore": "Orario"
                         },
                         width=2000, height=height)
        else:
            st.warning("No data available.")
    else:
        st.warning("No data available.")


def show_debt_mirko(filename):
    if check_file_exists(filename):
        debt_list = conn.read(f"bartabacchi_website/{filename}",
                              input_format="csv", ttl=3)
        if not debt_list.empty:
            height = (len(debt_list) + 1) * 35 + 3
            debt_list = debt_list.drop(columns="oggetto", axis=1)
            st.dataframe(debt_list,
                         hide_index=True,
                         column_config={
                             "nome": "Nome",
                             "debiti": "Debiti",
                             "pagati": "Pagati",
                             "ore": "Orario"
                         },
                         width=2000, height=height)
        else:
            st.warning("No data available.")
    else:
        st.warning("No data available.")


def total_debt(filename):
    debt_list = conn.read(f"bartabacchi_website/{filename}",
                          input_format="csv", ttl=3)
    total_amount = 0
    total_payement = 0
    total_calcio = 0
    total_voucher = 0
    total_carta = 0
    for index, row in debt_list.iterrows():
        if row['debiti'] != " ":
            total_amount += float(row['debiti'].replace(",", "."))
        if row['pagati'] != " ":
            total_payement += float(row['pagati'].replace(",", "."))
        if row['oggetto'] == "Scommesse calcio" and row['debiti'] != " ":
            total_calcio += float(row['debiti'].replace(",", "."))
        elif row['oggetto'] == "Voucher":
            total_voucher += float(row['pagati'].replace(",", "."))
        elif row['oggetto'] == "Carta, Bancomat":
            total_carta += float(row['pagati'].replace(",", "."))

    debt_cash = abs(total_payement) + total_voucher + total_carta

    return (float_format(total_amount),
            float_format(total_payement),
            float_format(total_calcio),
            float_format(total_voucher),
            float_format(debt_cash),
            float_format(total_carta))


def total_debt_mirko(filename):
    debt_list = conn.read(f"bartabacchi_website/{filename}",
                          input_format="csv", ttl=3)
    total_amount = 0
    total_payement = 0
    for index, row in debt_list.iterrows():
        if row['debiti'] != " ":
            total_amount += float(row['debiti'].replace(",", "."))
        if row['pagati'] != " ":
            total_payement += float(row['pagati'].replace(",", "."))

        return float_format(total_amount), float_format(total_payement)


def change_limit(edited_name, edited_value):
    lista_tabacchi = conn.read("bartabacchi_website/lista/lista_debiti_tabacchi.csv",
                               input_format="csv", ttl=3)
    lista_mirko = conn.read("bartabacchi_website/lista/lista_debiti_mirko.csv",
                            input_format="csv", ttl=3)
    row_number = lista_tabacchi.index.get_loc(lista_tabacchi[lista_tabacchi["nome"] == edited_name].index[0])
    lista_tabacchi.at[row_number, "limite"] = edited_value
    upload_file("lista/lista_debiti_tabacchi.csv", lista_tabacchi)

    if edited_name in lista_mirko["nome"].unique():
        row_number = lista_mirko.index.get_loc(lista_mirko[lista_mirko["nome"] == edited_name].index[0])
        lista_mirko.at[row_number, "limite"] = edited_value
        upload_file("lista/lista_debiti_mirko.csv", lista_mirko)


def show_journal(name):
    name = name.lower()
    if check_file_exists(f"nomi/{name}.csv"):
        journal = conn.read(f"bartabacchi_website/nomi/{name}.csv",
                            input_format="csv", ttl=3)
        if not journal.empty:
            for index, row in journal.iterrows():
                if row["debiti"] != " ":
                    debiti_row = f"""Giorno {row['data']} 
                                    ore {row['ore']} 
                                    Debito {row['debiti']} euro 
                                    Motivo: {row['oggetto']} 
                                    Totale: {row["totale"]}.
                                    """
                    st.write(debiti_row)
                else:
                    if (row["oggetto"] == "Voucher" or
                            row["oggetto"] == "Carta, Bancomat"):
                        pagati_row_voucher = f"""Giorno {row['data']} 
                                                ore {row['ore']} 
                                                pagato {row['pagati'].strip("-")} 
                                                euro con {row['oggetto'].lower()}.
                                                Totale: {row["totale"]}
                                                """
                        st.write(pagati_row_voucher)
                    else:
                        pagati_row_cash = f"""Giorno {row['data']} 
                                              ore {row['ore']} 
                                              pagato {row['pagati'].strip("-")} 
                                              euro in contanti. 
                                              Totale: {row['totale']}
                                              """
                        st.write(pagati_row_cash)
        else:
            st.warning("No data available.")
    else:
        st.warning("No data available.")


def current_page_tabacchi():
    date = st.date_input("Data", format="DD/MM/YYYY", key="date")
    with st.expander("Nuovo nome"):
        st.write("Aggiungere il nome se non è presente nella lista:")
        with st.form(key="add_name", clear_on_submit=True, border=False):
            row1 = st.columns(2)
            with row1[0]:
                tip = """Attenzione!!!
                Aggiungere solo se il soggetto non è 
                presente nella lista.
                Controlla bene!!! Non aggiungere nomi diversi 
                per un singolo soggetto!"""
                new_name = st.text_input("Nuovo nome",
                                         help=tip)
            with row1[1]:
                st.subheader("")
                button1 = st.form_submit_button("Aggiungi")
                if button1:
                    add_name(new_name, "tabacchi")
                    st.rerun()

    with st.form(key="add_debt", clear_on_submit=True, border=False):
        row2 = st.columns(4)
        with row2[0]:
            name_list = conn.read("bartabacchi_website/lista/name_list.csv",
                                  input_format="csv", ttl=3)
            name_list = name_list.sort_values(by=["nome"])
            name = st.selectbox("Nome",
                                name_list["nome"].apply(lambda x: x.capitalize()),
                                placeholder="Seleziona",
                                index=None)
        with row2[1]:
            debiti = st.number_input("Debiti", value=None)
        with row2[2]:
            object_list = conn.read("bartabacchi_website/lista/oggetto.csv",
                                    input_format="csv", ttl=3)
            oggetto = st.selectbox("Oggetto", object_list,
                                   placeholder="Seleziona",
                                   index=None)
        with row2[3]:
            st.subheader(" ")
            button2 = st.form_submit_button("Aggiungi")
        if button2:
            if not name or not debiti:
                pass
            elif debiti > 0 and (oggetto == "Voucher" or
                                 oggetto == "Carta, Bancomat" or not oggetto):
                st.warning("Inserire l'oggetto corretto.")
            else:
                if not check_file_exists(f"date/tabacchi/{date}.csv"):
                    debt_list = pd.DataFrame(columns=["nome", "debiti", "pagati", "oggetto", "ore"])
                    upload_file(f"date/tabacchi/{date}.csv", debt_list)

                now = datetime.now()
                current_date = now.strftime("%Y-%m-%d")

                if str(date) == current_date:
                    time = now.strftime("%H:%M")
                    total = update_debt_list(name.lower(), debiti, "tabacchi")
                    debt_journal(name.lower(), debiti, oggetto, current_date, time, total)
                else:
                    time = " "

                check_blacklist(name)
                add_debt_current(f"date/tabacchi/{date}.csv",
                                 name=name,
                                 amount=debiti,
                                 object=oggetto,
                                 hour=time)
                st.success("Aggiunto!")

    show_debt(f"date/tabacchi/{date}.csv")
    st.subheader(" ")
    try:
        (total_amount, total_payement,
         total_calcio, total_voucher, debt_cash, total_carta) = (
            total_debt(f"date/tabacchi/{date}.csv"))
        st.write("<b>Totale debiti:</b>", total_amount,
                 f"(di cui {total_calcio} scommesse calcio)",
                 unsafe_allow_html=True)
        st.write("<b>Totale debiti pagati:</b>",
                 total_payement.strip("-"),
                 f"(di cui {total_voucher.strip('-')} "
                 f"pagati con voucher e "
                 f"{total_carta.strip('-')} pagati con carta)",
                 unsafe_allow_html=True)
        st.write("<b>Totale debiti pagati in contanti:</b>", debt_cash,
                 unsafe_allow_html=True)
    except (TypeError, FileNotFoundError):
        pass


def show_page_debt_tabacchi():
    st.title("Debiti")
    lista = conn.read("bartabacchi_website/lista/lista_debiti_tabacchi.csv",
                      input_format="csv", ttl=3)
    lista = lista.drop(lista[lista.totale == 0].index)
    lista = lista.sort_values(by=["nome"], ignore_index=True)
    lista["nome"] = lista["nome"].apply(lambda x: x.capitalize())
    height = (len(lista) + 1) * 35 + 3
    lista = st.data_editor(lista, hide_index=True,
                           width=2000, height=height,
                           column_config={
                               "nome": "Nome",
                               "totale": st.column_config.NumberColumn
                               ("Totale", format="%.2f"),
                               "limite": "Limite"},
                           key="table",
                           disabled=("nome", "totale"))

    edited_rows = st.session_state.table["edited_rows"]
    if edited_rows:
        edited_rows_number = list(edited_rows.keys())[0]
        edited_value = edited_rows[edited_rows_number]["limite"]
        edited_name = lista.at[edited_rows_number, "nome"].lower()
        change_limit(edited_name, edited_value)
        add_blacklist(edited_name)
        del st.session_state.table["edited_rows"][edited_rows_number]
        st.rerun()


def debt_journal_page():
    st.title("Diario debiti")
    name_list = conn.read("bartabacchi_website/lista/name_list.csv",
                          input_format="csv", ttl=3)
    name_list = name_list.sort_values(by=["nome"])
    name = st.selectbox("Nome", name_list["nome"].apply(
        lambda x: x.capitalize()),
                        placeholder="Seleziona", index=None)

    if name:
        st.subheader(name)
        show_journal(name)


def current_page_mirko():
    date = st.date_input("Data", format="DD/MM/YYYY", key="date")
    with st.expander("Nuovo nome"):
        st.write("Aggiungere il nome se non è presente nella lista:")
        with st.form(key="add_name", clear_on_submit=True, border=False):
            row1 = st.columns(2)
            with row1[0]:
                tip = """Attenzione!!!
                    Aggiungere solo se il soggetto non è 
                    presente nella lista.
                    Controlla bene!!! Non aggiungere nomi diversi 
                    per un singolo soggetto!"""
                new_name = st.text_input("Nuovo nome",
                                         help=tip)
            with row1[1]:
                st.subheader("")
                button1 = st.form_submit_button("Aggiungi")
                if button1:
                    add_name(new_name, "tabacchi")
                    st.rerun()

    with (st.form(key="add_debt", clear_on_submit=True, border=False)):
        row2 = st.columns(4)
        with row2[0]:
            name_list = conn.read("bartabacchi_website/lista/name_list.csv",
                                  input_format="csv", ttl=3)
            name_list = name_list.sort_values(by=["nome"])
            name = st.selectbox("Nome",
                                name_list["nome"].apply(lambda x: x.capitalize()),
                                placeholder="Seleziona",
                                index=None)
        with row2[1]:
            debiti = st.number_input("Debiti", value=None)

        with row2[2]:
            st.subheader(" ")
            button2 = st.form_submit_button("Aggiungi")
        if button2:
            if not name or not debiti:
                pass
            else:
                if not check_file_exists(f"date/mirko/{date}.csv"):
                    debt_list = pd.DataFrame(columns=["nome", "debiti", "pagati", "oggetto", "ore"])
                    upload_file(f"date/mirko/{date}.csv", debt_list)

                now = datetime.now()
                current_date = now.strftime("%Y-%m-%d")

                if str(date) == current_date:
                    time = now.strftime("%H:%M")
                    total = update_debt_list(name.lower(), debiti, "mirko")
                    debt_journal(name.lower(), debiti, " ", current_date, time, total)
                else:
                    time = " "

                check_blacklist(name)
                add_debt_current(f"date/mirko/{date}.csv",
                                 name=name,
                                 amount=debiti,
                                 object=" ",
                                 hour=time)
                st.success("Aggiunto!")

        show_debt_mirko(f"date/mirko/{date}.csv")
        st.subheader(" ")
        try:
            total_debt, total_payement = total_debt_mirko(f"date/mirko/"
                                                          f"{date}.csv")
            st.write(f"<b>Totale debiti:</b> {total_debt}",
                     unsafe_allow_html=True)
            st.write(f"<b>Totale debiti pagati:</b>"
                     f"{total_payement.strip('-')}",
                     unsafe_allow_html=True)

        except (TypeError, FileNotFoundError):
            pass


def show_page_debt_mirko():
    st.title("Debiti")
    lista = conn.read("bartabacchi_website/lista/lista_debiti_mirko.csv",
                      input_format="csv", ttl=3)
    lista = lista.drop(lista[lista.totale == 0].index)
    lista = lista.sort_values(by=["nome"], ignore_index=True)
    lista["nome"] = lista["nome"].apply(lambda x: x.capitalize())
    height = (len(lista) + 1) * 35 + 3
    lista = st.data_editor(lista, hide_index=True,
                           width=2000, height=height,
                           column_config={
                               "nome": "Nome",
                               "totale": st.column_config.NumberColumn
                               ("Totale", format="%.2f"),
                               "limite": "Limite"},
                           key="table",
                           disabled=True)
