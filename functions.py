import streamlit as st
from st_files_connection import FilesConnection
import pandas as pd
from google.cloud import storage
from datetime import datetime
import json

credentials = dict(st.secrets.google.cloud.storage.credentials)
credentials = json.dumps(credentials)


@st.cache_resource(ttl=600)
def read_file(filename):
    conn = st.connection("gcs", type=FilesConnection)
    file = conn.read(f"bartabacchi_website/{filename}")
    return file


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


def update_debt_list(name, amount, username, lista_tabacchi):
    total = amount
    if name in lista_tabacchi["nome"].unique():
        row_number = (lista_tabacchi.index.get_loc
                      (lista_tabacchi[lista_tabacchi["nome"] == name]
                       .index[0]))
        lista_tabacchi.at[row_number, "totale"] += amount
        total = lista_tabacchi.at[row_number, "totale"]
        if lista_tabacchi.at[row_number, "limite"]:
            if total > float(lista_tabacchi.at[row_number, "limite"]):
                st.warning("Attenzione! Questo soggetto ha "
                           "superato il limite!")
    else:
        lista_tabacchi.loc[len(lista_tabacchi)] = [name, amount, " "]

    upload_file("lista/lista_debiti_tabacchi.csv",
                lista_tabacchi)

    return total, lista_tabacchi


def debt_journal(name, amount, object, date, hour, current_total):
    if not check_file_exists(f"nomi/{name}.csv"):
        debt_list = pd.DataFrame(columns=["debiti", "pagati", "oggetto",
                                          "data", "ore", "totale"])
    else:
        debt_list = read_file(f"nomi/{name}.csv")

    if amount > 0:
        debt_list.loc[len(debt_list)] = [amount, " ", object, date,
                                         hour, current_total]
    else:
        debt_list.loc[len(debt_list)] = [" ", amount, object, date,
                                         hour, current_total]
    upload_file(f"nomi/{name}.csv", debt_list)


def check_blacklist(name, blacklist):
    name = name.lower()
    if name in blacklist["nome"].unique():
        st.warning("Attenzione!!! Questo soggetto è nella lista nera.")


def add_blacklist(name, blacklist, lista_tabacchi):
    name = name.lower()
    row_number = (lista_tabacchi.index.get_loc
                  (lista_tabacchi[lista_tabacchi["nome"] == name]
                   .index[0]))
    limite = lista_tabacchi.at[row_number, "limite"]
    if limite == 0:
        blacklist.loc[len(blacklist)] = name
    upload_file("lista/lista_nera.csv", blacklist)
    return blacklist


def add_name(name, name_list):
    if not (name in name_list["nome"].unique()):
        name_list.loc[len(name_list)] = name

    name_list = name_list.sort_values(by=["nome"])
    upload_file("lista/name_list.csv", name_list)
    return name_list


def add_debt_current(debt_list, name, amount, object, hour, filename):
    if amount > 0:
        debt_list.loc[len(debt_list)] = [name, float_format(amount), " ", object, hour]
    else:
        if not object:
            object = " "
        debt_list.loc[len(debt_list)] = [name, " ", float_format(amount), object, hour]
    upload_file(filename, debt_list)
    return debt_list


def show_debt(filename, current_list, debt_list):
    if filename == current_list:
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
    elif check_file_exists(filename):
        debt_list = read_file(filename)
        if debt_list.empty:
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


def total_debt(filename, current_list, debt_list):
    if filename != current_list:
        debt_list = read_file(filename)
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


def change_limit(edited_name, edited_value, lista_tabacchi):
    row_number = lista_tabacchi.index.get_loc(lista_tabacchi[lista_tabacchi["nome"] == edited_name].index[0])
    lista_tabacchi.at[row_number, "limite"] = edited_value
    upload_file("lista/lista_debiti_tabacchi.csv", lista_tabacchi)
    return lista_tabacchi


def show_journal(name):
    name = name.lower()
    if check_file_exists(f"nomi/{name}.csv"):
        journal = read_file(f"nomi/{name}.csv")
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
                                                pagato {str(row['pagati']).strip("-")} 
                                                euro con {row['oggetto'].lower()}.
                                                Totale: {row["totale"]}
                                                """
                        st.write(pagati_row_voucher)
                    else:
                        pagati_row_cash = f"""Giorno {row['data']} 
                                              ore {row['ore']} 
                                              pagato {str(row['pagati']).strip("-")} 
                                              euro in contanti. 
                                              Totale: {row['totale']}
                                              """
                        st.write(pagati_row_cash)
        else:
            st.warning("No data available.")
    else:
        st.warning("No data available.")


def current_page_tabacchi(name_list, object_list, lista_tabacchi, blacklist, debt_list, current_date):
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
                    name_list = add_name(new_name, name_list)

    with st.form(key="add_debt", clear_on_submit=True, border=False):
        row2 = st.columns(4)
        with row2[0]:
            name_list = name_list.sort_values(by=["nome"])
            name = st.selectbox("Nome",
                                name_list["nome"].apply(lambda x: x.capitalize()),
                                placeholder="Seleziona",
                                index=None)
        with row2[1]:
            debiti = st.number_input("Debiti", value=None)
        with row2[2]:
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
                now = datetime.now()
                if str(date) == current_date:
                    time = now.strftime("%H:%M")
                    total, lista_tabacchi = update_debt_list(name.lower(), debiti, "tabacchi", lista_tabacchi)
                    debt_journal(name.lower(), debiti, oggetto, current_date, time, total)
                    check_blacklist(name, blacklist)
                    debt_list = add_debt_current(debt_list,
                                                 name=name,
                                                 amount=debiti,
                                                 object=oggetto,
                                                 hour=time,
                                                 filename=f"date/tabacchi/{current_date}.csv")
                    st.success("Aggiunto!")

    show_debt(f"date/tabacchi/{date}.csv",
              f"date/tabacchi/{current_date}.csv",
              debt_list=debt_list)
    st.subheader(" ")
    try:
        (total_amount, total_payement,
         total_calcio, total_voucher, debt_cash, total_carta) = (
            total_debt(f"date/tabacchi/{date}.csv",
                       f"date/tabacchi/{current_date}.csv", debt_list))
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

    return lista_tabacchi


def show_page_debt_tabacchi(lista_tabacchi, blacklist):
    st.title("Debiti")
    lista_tabacchi = lista_tabacchi.drop(lista_tabacchi[lista_tabacchi.totale == 0].index)
    lista_tabacchi = lista_tabacchi.sort_values(by=["nome"], ignore_index=True)
    lista_tabacchi["nome"] = lista_tabacchi["nome"].apply(lambda x: x.capitalize())
    height = (len(lista_tabacchi) + 1) * 35 + 3
    lista = st.data_editor(lista_tabacchi, hide_index=True,
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
        edited_name = lista_tabacchi.at[edited_rows_number, "nome"].lower()
        lista_tabacchi = change_limit(edited_name, edited_value, lista_tabacchi)
        blacklist = add_blacklist(edited_name, blacklist, lista_tabacchi)
        del st.session_state.table["edited_rows"][edited_rows_number]
        st.rerun()

    return lista_tabacchi, blacklist


def debt_journal_page():
    st.title("Diario debiti")
    name_list = read_file("lista/name_list.csv")
    name_list = name_list.sort_values(by=["nome"])
    name = st.selectbox("Nome", name_list["nome"].apply(
        lambda x: x.capitalize()),
                        placeholder="Seleziona", index=None)

    if name:
        st.subheader(name)
        show_journal(name)
