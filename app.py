import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        sector TEXT,
        quantity INTEGER,
        priority TEXT,
        notes TEXT,
        status TEXT DEFAULT 'لم يتم',
        volunteer TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_recipient(name, phone, sector, quantity, priority, notes):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO recipients (name, phone, sector, quantity, priority, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone, sector, quantity, priority, notes))
    conn.commit()
    conn.close()

def add_volunteer(name, code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO volunteers (name, code) VALUES (?, ?)", (name, code))
    conn.commit()
    conn.close()

def get_recipients():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM recipients", conn)
    conn.close()
    return df

def get_volunteers():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM volunteers", conn)
    conn.close()
    return df

def assign_recipients():
    recipients = get_recipients()
    volunteers = get_volunteers()
    if volunteers.empty or recipients.empty:
        return "Need volunteers and recipients."
    v_codes = volunteers['code'].tolist()
    assignments = {}
    for i, row in recipients.iterrows():
        assigned_vol = v_codes[i % len(v_codes)]
        assignments[row['id']] = assigned_vol
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for rid, vcode in assignments.items():
        cur.execute("UPDATE recipients SET volunteer=? WHERE id=?", (vcode, rid))
    conn.commit()
    conn.close()
    return "Assigned recipients."

def get_volunteer_recipients(code):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM recipients WHERE volunteer=?", conn, params=(code,))
    conn.close()
    return df

def update_status(recipient_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE recipients SET status=? WHERE id=?", (new_status, recipient_id))
    conn.commit()
    conn.close()

def main():
    st.title("تطبيق توزيع الأضحية - شبراملس")

    init_db()

    page = st.sidebar.radio("القائمة", ["إضافة مستحق", "إضافة مندوب", "التوزيع التلقائي", "شاشة المندوب", "عرض البيانات"])

    if page == "إضافة مستحق":
        st.header("إضافة مستحق")
        name = st.text_input("الاسم")
        phone = st.text_input("رقم الهاتف")
        sector = st.text_input("مربع التوزيع")
        quantity = st.number_input("الكمية", min_value=1, step=1)
        priority = st.selectbox("الأولوية", ["عادية", "عالية"])
        notes = st.text_area("ملاحظات")
        if st.button("حفظ"):
            if name:
                add_recipient(name, phone, sector, quantity, priority, notes)
                st.success("تم إضافة المستحق.")
            else:
                st.error("من فضلك أدخل الاسم.")
    elif page == "إضافة مندوب":
        st.header("إضافة مندوب")
        name = st.text_input("الاسم")
        code = st.text_input("كود الدخول")
        if st.button("حفظ مندوب"):
            if name and code:
                try:
                    add_volunteer(name, code)
                    st.success("تم إضافة المندوب.")
                except:
                    st.error("الكود مستخدم من قبل.")
            else:
                st.error("أدخل الاسم والكود.")
    elif page == "التوزيع التلقائي":
        st.header("التوزيع التلقائي")
        if st.button("قسّم الحالات على المندوبين"):
            msg = assign_recipients()
            st.info(msg)
    elif page == "شاشة المندوب":
        st.header("شاشة المندوب")
        code = st.text_input("أدخل كودك")
        if st.button("عرض الحالات"):
            df = get_volunteer_recipients(code)
            if df.empty:
                st.warning("لا توجد حالات.")
            else:
                for idx, row in df.iterrows():
                    with st.expander(f"{row['name']} - الحالة: {row['status']}"):
                        st.write(f"رقم الهاتف: {row['phone']}")
                        st.write(f"مربع التوزيع: {row['sector']}")
                        st.write(f"كمية اللحمة: {row['quantity']}")
                        st.write(f"الأولوية: {row['priority']}")
                        st.write(f"ملاحظات: {row['notes']}")
                        new_status = st.selectbox("تحديث الحالة", ["لم يتم", "في الطريق", "تم التسليم", "لم نجده"], index=["لم يتم", "في الطريق", "تم التسليم", "لم نجده"].index(row['status']))
                        if st.button("حفظ الحالة", key=f"save_{row['id']}"):
                            update_status(row['id'], new_status)
                            st.success("تم تحديث الحالة.")
    elif page == "عرض البيانات":
        st.header("عرض جميع البيانات")
        tab = st.radio("اختر", ["المستحقين", "المندوبين"])
        if tab == "المستحقين":
            df = get_recipients()
            st.dataframe(df)
        else:
            df = get_volunteers()
            st.dataframe(df)

if __name__ == "__main__":
    main()
