import sys
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QTableView, QMessageBox,
    QComboBox, QSpinBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


def is_blank(x: str) -> bool:
    return x is None or str(x).strip() == ""


class MySQLAdminGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL Table Manager (PK-safe) - PyQt5")
        self.resize(1150, 680)

        self.engine = None
        self.current_db = None
        self.current_table = None

        self.pk_cols = []
        self.auto_inc_pk = False
        self.df_original = None

        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)

        left = QVBoxLayout()
        form = QFormLayout()

        self.host_inp = QLineEdit("localhost")
        self.port_inp = QSpinBox()
        self.port_inp.setRange(1, 65535)
        self.port_inp.setValue(3306)

        self.user_inp = QLineEdit("elevator_ai")
        self.pass_inp = QLineEdit("elevator123")
        self.pass_inp.setEchoMode(QLineEdit.Password)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_mysql)

        self.db_combo = QComboBox()
        self.use_db_btn = QPushButton("Use Database")
        self.use_db_btn.clicked.connect(self.use_database)

        form.addRow("Host", self.host_inp)
        form.addRow("Port", self.port_inp)
        form.addRow("User", self.user_inp)
        form.addRow("Password", self.pass_inp)
        form.addRow(self.connect_btn)
        form.addRow(QLabel("Databases"))
        form.addRow(self.db_combo)
        form.addRow(self.use_db_btn)
        left.addLayout(form)

        left.addWidget(QLabel("Tables"))
        self.table_list = QListWidget()
        left.addWidget(self.table_list)

        self.load_table_btn = QPushButton("Load Table")
        self.load_table_btn.clicked.connect(self.load_table)
        left.addWidget(self.load_table_btn)

        root.addLayout(left, 1)

        right = QVBoxLayout()
        self.table_view = QTableView()
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        right.addWidget(self.table_view, 1)

        actions = QHBoxLayout()
        self.add_btn = QPushButton("Add Row")
        self.del_btn = QPushButton("Delete Selected")
        self.save_btn = QPushButton("Save Changes")
        self.refresh_btn = QPushButton("Refresh")

        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_selected)
        self.save_btn.clicked.connect(self.save_changes)
        self.refresh_btn.clicked.connect(self.refresh_table)

        actions.addWidget(self.add_btn)
        actions.addWidget(self.del_btn)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.refresh_btn)
        right.addLayout(actions)

        root.addLayout(right, 3)

    def _make_engine(self, db: str = None):
        host = self.host_inp.text().strip()
        port = self.port_inp.value()
        user = self.user_inp.text().strip()
        password = self.pass_inp.text()

        db_part = "" if not db else f"/{db}"
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}{db_part}?charset=utf8mb4"
        return create_engine(url, pool_pre_ping=True)

    def connect_mysql(self):
        try:
            self.engine = self._make_engine(db=None)
            with self.engine.connect() as conn:
                rows = conn.execute(text("SHOW DATABASES")).fetchall()

            self.db_combo.clear()
            for (db,) in rows:
                self.db_combo.addItem(db)

            QMessageBox.information(self, "OK", "Connected. Databases loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Connect failed", str(e))
            self.engine = None

    def use_database(self):
        if not self.engine:
            QMessageBox.warning(self, "Warning", "Connect first!")
            return
        db = self.db_combo.currentText().strip()
        if not db:
            return
        try:
            self.engine = self._make_engine(db=db)
            self.current_db = db
            self.load_tables()
            QMessageBox.information(self, "OK", f"Using database: {db}")
        except Exception as e:
            QMessageBox.critical(self, "Use DB failed", str(e))

    def load_tables(self):
        self.table_list.clear()
        with self.engine.connect() as conn:
            rows = conn.execute(text("SHOW TABLES")).fetchall()
        for (t,) in rows:
            self.table_list.addItem(t)

    def load_table(self):
        if not self.engine or not self.current_db:
            QMessageBox.warning(self, "Warning", "Connect + Use Database first!")
            return
        item = self.table_list.currentItem()
        if not item:
            return

        table = item.text()
        self.current_table = table

        try:
            insp = inspect(self.engine)
            self.pk_cols = insp.get_pk_constraint(table).get("constrained_columns", []) or []
            self.auto_inc_pk = (len(self.pk_cols) == 1 and self.pk_cols[0].lower() == "id")

            self.df_original = pd.read_sql(f"SELECT * FROM `{table}`", self.engine)
            self._df_to_model(self.df_original)

            QMessageBox.information(
                self, "Loaded",
                f"Table: {table}\nPrimary key: {', '.join(self.pk_cols) if self.pk_cols else '(none)'}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Load table failed", str(e))

    def refresh_table(self):
        if self.current_table:
            self.load_table()

    def _df_to_model(self, df: pd.DataFrame):
        self.model.clear()
        self.model.setColumnCount(len(df.columns))
        self.model.setHorizontalHeaderLabels(list(df.columns))

        for r in range(len(df)):
            row_items = []
            for c, col in enumerate(df.columns):
                val = df.iloc[r, c]
                item = QStandardItem("" if pd.isna(val) else str(val))
                if col in self.pk_cols and self.auto_inc_pk:
                    item.setEditable(False)
                else:
                    item.setEditable(True)
                row_items.append(item)
            self.model.appendRow(row_items)

        self.table_view.resizeColumnsToContents()

    def _model_to_df(self) -> pd.DataFrame:
        cols = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
        data = []
        for r in range(self.model.rowCount()):
            row = []
            for c in range(self.model.columnCount()):
                item = self.model.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)
        return pd.DataFrame(data, columns=cols)

    def add_row(self):
        if self.model.columnCount() == 0:
            return
        empty = []
        for c in range(self.model.columnCount()):
            col = self.model.headerData(c, Qt.Horizontal)
            it = QStandardItem("")
            if col in self.pk_cols and self.auto_inc_pk:
                it.setEditable(False)
            else:
                it.setEditable(True)
            empty.append(it)
        self.model.appendRow(empty)

    def delete_selected(self):
        idxs = self.table_view.selectionModel().selectedRows()
        if not idxs:
            return
        for idx in sorted(idxs, key=lambda x: x.row(), reverse=True):
            self.model.removeRow(idx.row())

    def save_changes(self):
        if not self.engine or not self.current_table:
            return

        if not self.pk_cols:
            QMessageBox.critical(
                self, "Save blocked",
                "Table này không có PRIMARY KEY.\nĐể update/delete an toàn, hãy thêm PK trước."
            )
            return

        try:
            df_new = self._model_to_df()

            def pk_key_from_row(row) -> tuple:
                return tuple(str(row[pk]).strip() for pk in self.pk_cols)

            orig_map = {}
            for _, row in self.df_original.iterrows():
                orig_map[pk_key_from_row(row)] = row.to_dict()

            new_map = {}
            new_rows_no_pk = []
            for _, row in df_new.iterrows():
                k = pk_key_from_row(row)
                if self.auto_inc_pk and len(self.pk_cols) == 1 and is_blank(k[0]):
                    new_rows_no_pk.append(row.to_dict())
                else:
                    new_map[k] = row.to_dict()

            orig_keys = set(orig_map.keys())
            new_keys = set(new_map.keys())

            delete_keys = list(orig_keys - new_keys)
            insert_keys = list(new_keys - orig_keys)
            common_keys = list(orig_keys & new_keys)

            update_keys = []
            for k in common_keys:
                o = orig_map[k]
                n = new_map[k]
                changed = False
                for col in df_new.columns:
                    if col in self.pk_cols:
                        continue
                    ov = "" if o.get(col) is None else str(o.get(col))
                    nv = "" if n.get(col) is None else str(n.get(col))
                    if ov != nv:
                        changed = True
                        break
                if changed:
                    update_keys.append(k)

            with self.engine.begin() as conn:
                for k in delete_keys:
                    where_clause = " AND ".join([f"`{pk}`=:pk_{i}" for i, pk in enumerate(self.pk_cols)])
                    params = {f"pk_{i}": k[i] for i in range(len(self.pk_cols))}
                    conn.execute(text(f"DELETE FROM `{self.current_table}` WHERE {where_clause}"), params)

                for k in insert_keys:
                    row = new_map[k]
                    cols = list(df_new.columns)
                    col_clause = ", ".join([f"`{c}`" for c in cols])
                    val_clause = ", ".join([f":{c}" for c in cols])
                    conn.execute(text(
                        f"INSERT INTO `{self.current_table}` ({col_clause}) VALUES ({val_clause})"
                    ), row)

                for row in new_rows_no_pk:
                    cols = [c for c in df_new.columns if c not in self.pk_cols]
                    col_clause = ", ".join([f"`{c}`" for c in cols])
                    val_clause = ", ".join([f":{c}" for c in cols])
                    params = {c: row.get(c) for c in cols}
                    conn.execute(text(
                        f"INSERT INTO `{self.current_table}` ({col_clause}) VALUES ({val_clause})"
                    ), params)

                for k in update_keys:
                    row = new_map[k]
                    set_cols = [c for c in df_new.columns if c not in self.pk_cols]
                    set_clause = ", ".join([f"`{c}`=:{c}" for c in set_cols])
                    where_clause = " AND ".join([f"`{pk}`=:pk_{i}" for i, pk in enumerate(self.pk_cols)])
                    params = {c: row.get(c) for c in set_cols}
                    params.update({f"pk_{i}": k[i] for i in range(len(self.pk_cols))})
                    conn.execute(text(
                        f"UPDATE `{self.current_table}` SET {set_clause} WHERE {where_clause}"
                    ), params)

            QMessageBox.information(
                self, "Saved",
                f"DELETE: {len(delete_keys)} | INSERT: {len(insert_keys) + len(new_rows_no_pk)} | UPDATE: {len(update_keys)}"
            )
            self.refresh_table()

        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MySQLAdminGUI()
    w.show()
    sys.exit(app.exec())

