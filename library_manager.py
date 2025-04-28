import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import os

# ---------------------------- DATABASE & AUTH ---------------------------- #

def init_db():
    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, author TEXT, category TEXT)""")
    conn.commit()
    return conn, cur

def validate_user(cur, username, password):
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cur.fetchone() is not None

def register_user(cur, conn, username, password):
    cur.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    conn.commit()

# ---------------------------- APP FEATURES ---------------------------- #

CATEGORIES = ["Fiction", "Non-fiction", "Academic", "Religious", "Other"]

def add_book(cur, conn, title, author, category):
    cur.execute("INSERT INTO books (title, author, category) VALUES (?, ?, ?)", (title, author, category))
    conn.commit()

def edit_book(cur, conn, book_id, title, author, category):
    cur.execute("UPDATE books SET title=?, author=?, category=? WHERE id=?", (title, author, category, book_id))
    conn.commit()

def delete_book(cur, conn, book_id):
    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()

def get_books(cur, filter_cat="All"):
    if filter_cat == "All":
        cur.execute("SELECT * FROM books")
    else:
        cur.execute("SELECT * FROM books WHERE category=?", (filter_cat,))
    return cur.fetchall()

def search_books(cur, query):
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    return [book for book in books if query.lower() in book[1].lower() or query.lower() in book[2].lower()]

def export_books_csv(books):
    df = pd.DataFrame(books, columns=["ID", "Title", "Author", "Category"])
    return df.to_csv(index=False).encode('utf-8')

def export_books_pdf(books):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Personal Library Book List", ln=True, align='C')
    pdf.ln(10)
    for book in books:
        pdf.cell(0, 10, f"{book[1]} by {book[2]} [{book[3]}]", ln=True)
    pdf_file = "books.pdf"
    pdf.output(pdf_file)
    return pdf_file

# ---------------------------- MAIN APP ---------------------------- #

def main_app(username):
    st.title(f"Welcome, {username}! Personal Library Manager")
    conn, cur = init_db()

    tab1, tab2, tab3 = st.tabs(["Manage Books", "Search/Filter", "Export"])

    with tab1:
        st.subheader("Add a New Book")
        with st.form("add_form"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            category = st.selectbox("Category", CATEGORIES)
            submitted = st.form_submit_button("Add Book")
            if submitted:
                if title and author and category:
                    add_book(cur, conn, title, author, category)
                    st.success("Book added successfully!")

        st.subheader("All Books")
        books = get_books(cur)
        st.write(f"Total Books: {len(books)}")
        for book in books:
            with st.expander(f"{book[1]} by {book[2]} [{book[3]}]"):
                new_title = st.text_input(f"Edit Title {book[0]}", value=book[1], key=f"t{book[0]}")
                new_author = st.text_input(f"Edit Author {book[0]}", value=book[2], key=f"a{book[0]}")
                new_cat = st.selectbox(f"Edit Category {book[0]}", CATEGORIES, index=CATEGORIES.index(book[3]), key=f"c{book[0]}")
                if st.button("Save Changes", key=f"save{book[0]}"):
                    edit_book(cur, conn, book[0], new_title, new_author, new_cat)
                    st.success("Book updated!")
                    st.rerun()
                if st.button("Delete", key=f"del{book[0]}"):
                    delete_book(cur, conn, book[0])
                    st.warning("Book deleted!")
                    st.rerun()

    with tab2:
        st.subheader("Search or Filter Books")
        query = st.text_input("Search by title or author")
        filter_cat = st.selectbox("Filter by Category", ["All"] + CATEGORIES)
        filtered = search_books(cur, query) if query else get_books(cur, filter_cat)
        st.write(f"Found {len(filtered)} books")
        for book in filtered:
            st.write(f"{book[1]} by {book[2]} [{book[3]}]")

    with tab3:
        st.subheader("Export Books")
        books = get_books(cur)
        csv = export_books_csv(books)
        st.download_button("Download CSV", data=csv, file_name="books.csv", mime="text/csv")

        pdf_file = export_books_pdf(books)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", data=f, file_name="books.pdf", mime="application/pdf")
        os.remove(pdf_file)

# ---------------------------- LOGIN PAGE ---------------------------- #

def login_page():
    st.title("SyedaAlmas Library Login")
    conn, cur = init_db()
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if validate_user(cur, user, pwd):
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    with register_tab:
        new_user = st.text_input("New Username")
        new_pwd = st.text_input("New Password", type="password")
        if st.button("Register"):
            if new_user and new_pwd:
                register_user(cur, conn, new_user, new_pwd)
                st.success("Registered successfully! You can now login.")

# ---------------------------- RUN APP ---------------------------- #

if "user" in st.session_state:
    main_app(st.session_state.user)
else:
    login_page()